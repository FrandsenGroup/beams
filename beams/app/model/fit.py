import numpy as np
import sympy as sp
from scipy.optimize import least_squares

from collections import OrderedDict
import time
import re
import logging

from app.resources import resources
from app.model import domain

INDEPENDENT_VARIABLE = "t"

DELTA = "\u0394"
LAMBDA = "\u03BB"
BETA = "\u03B2"
SIGMA = "\u03C3"
ALPHA = "\u03B1"
PHI = "\u03A6"
PI = "\u03C0"
NAUGHT = "\u2080"

SIMPLE_EXPONENTIAL = "exp(-\u03BB*t)"
STRETCHED_EXPONENTIAL = "exp(-(\u03BB*t)^\u03B2)"
SIMPLE_GAUSSIAN = "exp(-1/2*(\u03C3*t)^2)"
GAUSSIAN_KT = "1/3 + 2/3*(1 - (\u03C3*t)^2)*exp(-1/2*(\u03C3*t)^2)"
LORENTZIAN_KT = "1/3 + 2/3*(1 - \u03BB*t)*exp(-\u03BB*t)"
COMBINED_KT = "1/3 + 2/3*(1-\u03C3^2*t^2-\u03BB*t)*exp(-\u03C3^2*t^2/2-\u03BB*t)"
STRETCHED_KT = "1/3 + 2/3*(1-(\u03C3*t)^\u03B2)*exp(-(\u03C3*t)^\u03B2/\u03B2)"
COSINE = "a*cos(2*\u03C0*v*t + \u03C0*\u03A6/180)*exp(-\u03B2*t)"
INTERNAL_COSINE = "a*cos(2*\u03C0*v*t + \u03C0*\u03A6/180)*exp(-\u03BB*t) + (1-\u03B12)*exp(-\u03BB*t)"
BESSEL = "j\u2080*(2*\u03C0*v*t + \u03C0*\u03A6/180)"
INTERNAL_BESSEL = "\u03B1*j\u2080*(2*\u03C0*v*t + \u03C0*\u03A6/180)*exp(-\u03BB*t) + (1-\u03B1)*exp(-\u03BB*t)"

ALPHA_CORRECTION = '((1-\u03B1)+((1+\u03B1)*({})))/((1+\u03B1)+((1-\u03B1)*({})))'

EQUATION_DICTIONARY = {"Simple Exponential": SIMPLE_EXPONENTIAL,
                       "Stretched Exponential": STRETCHED_EXPONENTIAL,
                       "Simple Gaussian": SIMPLE_GAUSSIAN,
                       "Gaussian KT": GAUSSIAN_KT,
                       "Lorentzian KT": LORENTZIAN_KT,
                       "Combined KT": COMBINED_KT,
                       "Stretched KT": STRETCHED_KT,
                       "Cosine": COSINE,
                       "Internal Cosine": INTERNAL_COSINE,
                       "Bessel": BESSEL,
                       "Internal Bessel": INTERNAL_BESSEL}

if "funs" in resources.SAVED_USER_DATA.keys():
    USER_EQUATION_DICTIONARY = resources.SAVED_USER_DATA["funs"]
else:
    USER_EQUATION_DICTIONARY = {}

resources.SAVED_USER_DATA["funs"] = USER_EQUATION_DICTIONARY


class FitParameter:
    def __init__(self, symbol, value, lower, upper, is_global, is_fixed, is_fixed_run=False, fixed_value=None, output=None, uncertainty=None):
        self.uncertainty = uncertainty
        self.output = output
        self.upper = upper
        self.lower = lower
        self.value = value
        self.symbol = symbol
        self.is_fixed = is_fixed
        self.fixed_value = fixed_value
        self.is_fixed_run = is_fixed_run
        self.is_global = is_global

    def __eq__(self, other):
        return other.symbol == self.symbol \
            and other.value == self.value \
            and other.lower == self.lower \
            and other.upper == self.upper \
            and other.is_global == self.is_global \
            and other.is_fixed == self.is_fixed \
            and other.is_fixed_run == self.is_fixed_run \
            and other.fixed_value == self.fixed_value \
            and other.output == self.output \
            and other.uncertainty == self.uncertainty

    def __str__(self):
        return '{}={}'.format(self.symbol, self.value)

    def __repr__(self):
        return 'FitParameter ({})=({},{},{},{},{},{},{})'.format(self.symbol, self.value, self.lower, self.upper,
                                                                 self.is_global, self.is_fixed, self.is_fixed_run,
                                                                 self.fixed_value)

    def get_value(self):
        return float(self.value if not self.is_fixed_run else self.fixed_value)


class FitExpression:
    def __init__(self, expression_string, variables=None):
        self.__expression_string = expression_string

        if variables is None:
            variables = parse(self.__expression_string)
            variables.discard(INDEPENDENT_VARIABLE)

        self.__expression = lambdify(self.__expression_string, variables, INDEPENDENT_VARIABLE)
        self.__fixed = {}

    def __eq__(self, other):
        return str(other) == self.__expression_string

    def __str__(self):
        return self.__expression_string

    def __call__(self, *args, **kwargs):
        # The length of this function is due to the fact I have trust issues.

        time_array = args[0]

        pars = {}
        unnamed_pars = []
        if len(args) > 1:
            for arg in args[1:]:
                if isinstance(arg, FitParameter):
                    pars[arg.symbol] = arg.value
                else:
                    try:
                        unnamed_pars.append(float(arg))
                    except ValueError:
                        raise ValueError("Every parameter after the array should be of type FitParameter.")
        for k, v in kwargs.items():
            pars[k] = v

        for symbol, value in self.__fixed.items():
            pars[symbol] = value

        try:
            return self.__expression(time_array, *unnamed_pars, **pars)
        except TypeError:
            if ALPHA in pars.keys():
                pars.pop(ALPHA)
                return self.__expression(time_array, *unnamed_pars, **pars)
            raise

    def set_fixed(self, parameters):
        self.__fixed = {symbol: parameter.value for symbol, parameter in parameters}


class FitConfig:
    LEAST_SQUARES = 1
    GLOBAL_PLUS = 2

    def __init__(self):
        self.expression = ''
        self.parameters = {}
        self.titles = {}
        self.data = {}
        self.flags = 0

    def __str__(self):
        return "FitConfig ({})=({}, {})".format(self.expression, self.flags, self.parameters)

    def set_flags(self, *flags):
        self.flags = 0
        for flag in flags:
            self.flags = self.flags | flag

    def is_least_squares(self):
        return bool(self.flags & FitConfig.LEAST_SQUARES)

    def is_global_plus(self):
        return bool(self.flags & FitConfig.GLOBAL_PLUS)

    def get_symbols_for_run(self, run_id, is_fixed=None, is_global=None):
        symbols = []
        for symbol, parameter in self.parameters[run_id].items():
            if (is_fixed is None and is_global is None) \
                    or (is_fixed and (parameter.is_fixed or parameter.is_fixed_run)) \
                    or (is_fixed is not None and (is_fixed == parameter.is_fixed and is_fixed == parameter.is_fixed_run)) \
                    or (is_global and parameter.is_global) \
                    or (is_global is not None and (is_global == parameter.is_global)):
                symbols.append(symbol)

        return symbols

    def get_values_for_run(self, run_id, is_fixed=None, is_global=None):
        values = []

        for _, parameter in self.parameters[run_id].items():
            if (is_fixed is None and is_global is None) \
                    or (is_fixed and (parameter.is_fixed or parameter.is_fixed_run)) \
                    or (is_fixed is not None and (is_fixed == parameter.is_fixed and is_fixed == parameter.is_fixed_run)) \
                    or (is_global and parameter.is_global) \
                    or (is_global is not None and (is_global == parameter.is_global)):
                values.append(parameter.get_value())

        return values

    def get_lower_values_for_run(self, run_id, is_fixed=None, is_global=None):
        values = []

        for _, parameter in self.parameters[run_id].items():
            if (is_fixed is None and is_global is None) \
                    or (is_fixed and (parameter.is_fixed or parameter.is_fixed_run)) \
                    or (is_fixed is not None and (is_fixed == parameter.is_fixed and is_fixed == parameter.is_fixed_run)) \
                    or (is_global and parameter.is_global) \
                    or (is_global is not None and (is_global == parameter.is_global)):

                if parameter.is_fixed or parameter.is_fixed_run:
                    values.append(parameter.get_value() - 0.0000001)
                else:
                    values.append(parameter.lower)

        return values

    def get_upper_values_for_run(self, run_id, is_fixed=None, is_global=None):
        values = []

        for _, parameter in self.parameters[run_id].items():
            if (is_fixed is None and is_global is None) \
                    or (is_fixed and (parameter.is_fixed or parameter.is_fixed_run)) \
                    or (is_fixed is not None and (is_fixed == parameter.is_fixed and is_fixed == parameter.is_fixed_run)) \
                    or (is_global and parameter.is_global) \
                    or (is_global is not None and (is_global == parameter.is_global)):

                if parameter.is_fixed or parameter.is_fixed_run:
                    values.append(parameter.get_value() + 0.0000001)
                else:
                    values.append(parameter.upper)

        return values

    def get_adjusted_global_symbols(self):
        symbols = []
        for i, run_id in enumerate(self.parameters.keys()):
            for symbol, parameter in self.parameters[run_id].items():
                if parameter.is_global and i == 0:
                    symbols.append(symbol)
                elif not parameter.is_global:
                    symbols.append(symbol + _shortened_run_id(run_id))

        return symbols

    def get_adjusted_global_values(self):
        values = []
        for i, run_id in enumerate(self.parameters.keys()):
            for _, parameter in self.parameters[run_id].items():
                if parameter.is_global and i == 0:
                    values.append(parameter.value)
                elif not parameter.is_global:
                    values.append(parameter.value)

        return values

    def get_adjusted_global_lowers(self):
        lowers = []
        for i, run_id in enumerate(self.parameters.keys()):
            for _, parameter in self.parameters[run_id].items():
                if parameter.is_global and i == 0:
                    if parameter.is_fixed or parameter.is_fixed_run:
                        lowers.append(parameter.get_value() - 0.0000001)
                    else:
                        lowers.append(parameter.lower)
                elif not parameter.is_global:
                    if parameter.is_fixed or parameter.is_fixed_run:
                        lowers.append(parameter.get_value() - 0.0000001)
                    else:
                        lowers.append(parameter.lower)

        return lowers

    def get_adjusted_global_uppers(self):
        uppers = []
        for i, run_id in enumerate(self.parameters.keys()):
            for _, parameter in self.parameters[run_id].items():
                if parameter.is_global and i == 0:
                    if parameter.is_fixed or parameter.is_fixed_run:
                        uppers.append(parameter.get_value() + 0.0000001)
                    else:
                        uppers.append(parameter.upper)
                elif not parameter.is_global:
                    if parameter.is_fixed or parameter.is_fixed_run:
                        uppers.append(parameter.get_value() + 0.0000001)
                    else:
                        uppers.append(parameter.upper)

        return uppers

    def get_kwargs(self, run_id):
        kwargs = {}
        for symbol, parameter in self.parameters[run_id].items():
            if symbol != ALPHA:
                kwargs[symbol] = parameter.get_value()
        return kwargs

    def set_outputs(self, run_id, symbol, output, uncertainty):
        self.parameters[run_id][symbol].value = output  # You may be tempted to keep this value... Go for it.
        self.parameters[run_id][symbol].output = output
        self.parameters[run_id][symbol].fixed_value = output
        self.parameters[run_id][symbol].uncertainty = uncertainty


class Fit(np.ndarray):
    def __new__(cls, input_array, parameters, expression, asymmetry, uncertainty, time, title, run_id, *args, **kwargs):
        self = np.asarray(input_array).view(cls)
        self.parameters = parameters
        self.expression = expression
        self.title = title
        self.run_id = run_id

        return self

    def __call__(self, *args, **kwargs):
        pass


class FitDataset:
    def __init__(self):
        t = time.localtime()
        current_time = time.strftime("%d-%m-%YT%H:%M:%S", t)

        self.id = str(current_time)
        self.fits = {}
        self.flags = 0
        self.expression = None

    def write(self, out_file, save_format=None):
        if save_format is None or save_format == FitOptions.SAVE_1:
            fit_parameters_string = "# Fit Parameters\n\n# \tName\tValue\tLower\tUpper\n\n"
            if self.options[FitOptions.GLOBAL]:
                fit_parameters_string += "# Common parameters for all runs\n\n"

                f = list(self.fits.values())[0]
                for name, v in f.variables.items():
                    if v.is_global:
                        fit_parameters_string += "\t" + str(v) + "\n"

                fit_parameters_string += "\n"

            for f in self.fits.values():
                run = domain.RunService.get_runs_by_ids([f.run_id])[0]
                fit_parameters_string += "# Specific parameters for run {}\n\n".format(run.meta["RunNumber"])

                for name, v in f.variables.items():
                    if not v.is_global:
                        fit_parameters_string += "\t" + str(v) + "\n"

                fit_parameters_string += "\n"

            with open(out_file, 'w', encoding="utf-8") as f:
                f.write("#BEAMS\n"
                        + fit_parameters_string
                        + "# Expression\n\n\t"
                        + "A(t) = " + self.function)

        elif save_format == FitOptions.SAVE_2:
            full_string = ""

            f = list(self.fits.values())[0]

            for name, v in f.variables.items():
                full_string += "{}\t".format(name)

            full_string += "RUN\n"

            for f in self.fits.values():
                for name, v in f.variables.items():
                    full_string += "{:.4f}\t".format(v.value)
                run = domain.RunService.get_runs_by_ids([f.run_id])[0]
                full_string += run.meta["RunNumber"] + "\n"

            with open(out_file, 'w', encoding="utf-8") as f:
                f.write("#BEAMS\n"
                        + full_string)


class FitEngine:
    def __init__(self):
        self.__run_service = domain.RunService()
        self.__logger = logging.getLogger('FitEngine')

    def fit(self, config: FitConfig) -> FitDataset:
        if len(set([len(asymmetry) for asymmetry in config.data.values()])) != 1:
            raise ValueError("Must have one or more datasets all of equal length to fit")

        if config.expression == '':
            raise ValueError("Empty function attribute")

        if config.is_global_plus():
            if config.is_least_squares():
                return self._least_squares_fit_global(config)
        else:
            if config.is_least_squares():
                return self._least_squares_fit_non_global(config)

    def _least_squares_fit_global(self, config: FitConfig):
        # The methods from config will get the adjusted symbols, values, etc. in the same order every time for a global
        #   fit (which is necessary because we can't specify which value belongs to which symbol in the scipy least
        #   squares function.
        guesses = config.get_adjusted_global_values()
        lowers = config.get_adjusted_global_lowers()
        uppers = config.get_adjusted_global_uppers()

        # Don't mind me, just using your io to log for my personal needs.
        self.__logger.debug(config.get_adjusted_global_symbols())
        self.__logger.debug(guesses)
        self.__logger.debug(lowers)
        self.__logger.debug(uppers)

        # We are essentially doing one big fit where you will have global and local (local to a specific section of the
        #   concatenated asymmetry) parameters being refined.
        concatenated_asymmetry = np.array([])
        concatenated_uncertainty = np.array([])
        concatenated_time = np.array([])
        for _, asymmetry in config.data.items():
            concatenated_asymmetry = np.concatenate((concatenated_asymmetry, asymmetry))
            concatenated_uncertainty = np.concatenate((concatenated_uncertainty, asymmetry.uncertainty))
            concatenated_time = np.concatenate((concatenated_time, asymmetry.time))

        # Create a single global lambda function for all the datasets. Essentially, it acts like a
        #    stepwise function, once you pass into the asymmetry of another dataset, a separate function
        #    in the lambda will start being used. See its definition for more on why.
        global_lambda_expression = self._lambdify_global(config, concatenated_time)
        residual = FitEngine._residual(global_lambda_expression)
        
        # Run a lease squares fit with the global lambda and concatenated datasets
        opt = least_squares(residual, guesses, bounds=[lowers, uppers], args=(concatenated_time, concatenated_asymmetry, concatenated_uncertainty))
        self.__logger.debug(opt)

        # Assemble the Fit object, first by updating the parameters in the config with the outputs from
        #   the fit, as well as adding a FitExpression object that can be called.
        dataset = FitDataset()
        values = {}
        for i, symbol in enumerate(config.get_adjusted_global_symbols()):
            values[symbol] = opt.x[i]

        for run_id, asymmetry in config.data.items():
            for symbol, parameter in config.parameters[run_id].items():
                if not parameter.is_global:
                    config.set_outputs(run_id, symbol, values[symbol + _shortened_run_id(run_id)], 0)
                else:
                    config.set_outputs(run_id, symbol, values[symbol], 0)

            lambda_expression = FitExpression(config.expression)

            fitted_asymmetry = lambda_expression(asymmetry.time, **config.get_kwargs(run_id))
            new_fit = Fit(fitted_asymmetry, config.parameters[run_id], lambda_expression,
                          asymmetry, None, asymmetry.time, config.titles[run_id], run_id)

            dataset.fits[run_id] = new_fit

        dataset.expression = config.expression
        dataset.flags = config.flags

        return dataset

    # FIXME We need to update this to use the new BETTER ;) fixed method
    def _least_squares_fit_non_global(self, config) -> FitDataset:
        dataset = FitDataset()
        for run_id, asymmetry in config.data.items():
            # We create a separate lambda expression for each run in case they set separate run dependant fixed values.
            function = ALPHA_CORRECTION.format(config.expression, config.expression)
            lambda_expression = FitExpression(function, variables=config.get_symbols_for_run(run_id))
            residual = FitEngine._residual(lambda_expression)

            guesses = config.get_values_for_run(run_id)
            lowers = config.get_lower_values_for_run(run_id)
            uppers = config.get_upper_values_for_run(run_id)

            self.__logger.debug(config.get_symbols_for_run(run_id))
            self.__logger.debug(guesses)
            self.__logger.debug(lowers)
            self.__logger.debug(uppers)

            # 6) Perform a least squares fit
            opt = least_squares(residual, guesses, bounds=[lowers, uppers],
                                args=(asymmetry.time, asymmetry, asymmetry.uncertainty))
            self.__logger.debug(opt)

            try:
                unc, chi_sq = get_std_unc(opt, asymmetry)

                for i, symbol in enumerate(config.get_symbols_for_run(run_id)):
                    if config.parameters[run_id][symbol].is_fixed or config.parameters[run_id][symbol].is_fixed_run:
                        unc[i] = 0.0

            except np.linalg.LinAlgError:  # Fit did not converge
                unc = [-1 for _ in opt.x]

            self.__logger.debug("Uncertainty: ".format(str(unc)))

            # 7) Replace initial values with fitted values for unfixed variables
            for i, symbol in enumerate(config.get_symbols_for_run(run_id)):
                config.set_outputs(run_id, symbol, opt.x[i], unc[i])

            # 8) Create a callable function of our original string function
            lambda_expression = FitExpression(config.expression)

            # 9) Fill in all values for our new fit object
            fitted_asymmetry = lambda_expression(asymmetry.time, **config.get_kwargs(run_id))
            new_fit = Fit(fitted_asymmetry, config.parameters[run_id], lambda_expression,
                          asymmetry, None, asymmetry.time, config.titles[run_id], run_id)

            # 10) Add fit to our dataset
            dataset.fits[run_id] = new_fit

        # 11) Attach fit spec options and function to dataset (mostly for debugging purposes)
        dataset.expression = config.expression
        dataset.flags = config.flags

        return dataset

    def _lambdify_global(self, config: FitConfig, concatenated_time):
        function = ALPHA_CORRECTION.format(config.expression, config.expression)
        self.__logger.debug('_lambdify_global: {}'.format(function))

        lambdas = OrderedDict()
        run_id_order = []
        for i, (run_id, asymmetry) in enumerate(config.data.items()):
            new_function = function
            for symbol in config.get_symbols_for_run(run_id, is_global=False):
                new_function = FitEngine._replace_var_with(new_function, symbol, symbol + _shortened_run_id(run_id))

            self.__logger.debug("_lambdify_global: f({})={}".format(run_id, new_function))
            new_lambda_expression = FitExpression(new_function, variables=config.get_adjusted_global_symbols())
            lambdas[run_id] = new_lambda_expression
            run_id_order.append(run_id)

        def _lambda_expression(arr, *pars, **kwargs):
            values = []
            length = len(arr)
            section_length = length / len(lambdas)
            for i_x, x in enumerate(arr):
                n = i_x // section_length
                values.append(lambdas[run_id_order[int(n)]](x, *pars, **kwargs))
            return values

        return _lambda_expression

    @staticmethod
    def _residual(lambda_expression):
        def residual(pars, x, y_data, dy_data):
            y_calc = lambda_expression(x, *pars)
            return (y_data - y_calc) / dy_data
        return residual

    @staticmethod
    def _replace_fixed(function, symbols, values):
        for symbol, value in zip(symbols, values):
            function = re.sub(r'(?<=\b){}(?=\b)'.format(symbol), str(value), function)
        return function

    @staticmethod
    def _replace_var_with(function, old_symbol, new_symbol):
        return re.sub(r'(?<=\b){}(?=\b)'.format(old_symbol), str(new_symbol), function)


def get_std_unc(result, data, error=None, num_constraints=0):
    """Return the standard uncertainty of refined parameters.
    This method is based on the scipy.optimize.least_squares routine.

    Args:
        result: Output from scipy.optimize.least_squares routine
        data (numpy array): The data against which the fit is performed
        error (numpy array): Experimental uncertainties on the data points
            (set to unity if not provided)
        num_constraints (int): Number of constraints used in the model
    Returns:
        p_unc (numpy array): standard uncertainties of the refined parameters.
        chisq (float): Value of chi^2 for the fit.
    """

    if error is None:
        error = np.ones_like(data)

    weights = 1.0 / error ** 2
    rw = np.sqrt((result.fun ** 2).sum() / (data ** 2 * weights).sum())
    num_params = len(result.x)
    r_exp = np.sqrt((data.shape[0] - num_params + num_constraints) / (data ** 2 * weights).sum())
    j = result.jac
    jac = np.dot(j.transpose(), j)
    cov = np.linalg.inv(jac) * rw ** 2 / r_exp ** 2
    p_unc = np.sqrt(cov.diagonal())
    chi_sq = rw ** 2 / r_exp ** 2

    return p_unc, chi_sq


def parse(s):
    """ Takes in an expression as a string and returns a set of the free variables. """

    # Add to these sets any keywords you want to be recognized as not variables.
    # Keep keywords lowercase, user input will be cast to lowercase for comparison.
    operator_set = ('+', '-', '/', '*', '(', ')', '[', ']', '{', '}', '^', '!')
    operating_set = ('+', '-', '/', '*', '^')
    key_1_char_set = ('e', 'i', PI)
    key_2_char_set = ('pi')
    key_3_char_set = ('sin', 'cos', 'tan', 'exp')
    key_4_char_set = ('sinh', 'cosh', 'tanh')

    free_set = set()
    free_variable = []
    skip_chars = 0
    last_was_operator = False
    for i, character in enumerate(s):
        if skip_chars > 0:
            skip_chars -= 1
            continue

        if character.isspace() or character in operator_set:
            if last_was_operator and character in operating_set and character != '-':
                raise ValueError('Bad expression')
            last_was_operator = character in operating_set

            free_variable_joined = "".join(free_variable)
            free_set.add(free_variable_joined)
            free_variable = []

        elif character.isalpha():
            if s[i:i + 4].lower() in key_4_char_set:
                if len(free_variable) > 0:
                    raise ValueError('Bad expression')
                skip_chars = 3
                continue
            elif s[i:i + 3].lower() in key_3_char_set:
                if len(free_variable) > 0:
                    raise ValueError('Bad expression')
                skip_chars = 2
                continue
            elif s[i:i + 2].lower() in key_2_char_set:
                if len(free_variable) > 0:
                    raise ValueError('Bad expression')
                skip_chars = 1
                continue
            elif len(free_variable) == 0 and (s[i] in key_1_char_set or s[i].lower() in key_1_char_set) and \
                    (i == len(s) - 1 or s[i + 1] in operator_set or s[i + 1].isspace()):
                if len(free_variable) > 0:
                    raise ValueError('Bad expression')
                continue
            else:
                free_variable.append(character)

        elif character.isdigit():
            if free_variable:
                free_variable.append(character)

    free_variable_joined = "".join(free_variable)
    free_set.add(free_variable_joined)

    try:
        free_set.remove('')
    except KeyError:
        pass

    return free_set


def is_valid_expression(expression):
    try:
        parse(split_expression(expression)[1])
    except (ValueError, TypeError):
        return False

    if "=" not in expression:
        return False

    independent_variable = ""
    open_paren = False
    for i, c in enumerate(expression):
        if open_paren:
            if c == "=":
                return False
            elif c == ")":
                if len(independent_variable) == 0:
                    return False
                for j, k in enumerate(expression):
                    if k == "=":
                        try:
                            sp.sympify(expression[j+1:])
                            return True
                        except Exception:
                            return False
            else:
                independent_variable += c

        if c == "(":
            open_paren = True
    else:
        return False


def split_expression(expression):
    independent_variable = ""
    open_paren = False
    for i, c in enumerate(expression):
        if open_paren:
            if c == "=":
                return None
            elif c == ")":
                if len(independent_variable) == 0:
                    return None
                for j, k in enumerate(expression):
                    if k == "=":
                        try:
                            sp.sympify(expression[j + 1:])
                            return independent_variable, expression[j + 1:]
                        except Exception:
                            return None
            else:
                independent_variable += c
        if c == "(":
            open_paren = True
    else:
        return None


def replace_symbols(expression, pretty=False):
    expression_string = ""

    if pretty:
        skip = False
        for i, c in enumerate(expression):
            if skip:
                skip = False
                continue

            if i + 1 < len(expression):
                if expression[i:i+2] == "pi":
                    expression_string += PI
                    skip = True
                    continue
                elif expression[i:i+2] == '**':
                    expression_string += "^"
                    skip = True
                    continue

            if c == "0" and i > 0 and expression[i-1].isalpha():
                expression_string += NAUGHT
            else:
                expression_string += c
    else:
        for c in expression:
            if c == PI:
                expression_string += "pi"
            elif c == '^':
                expression_string += "**"
            elif c == NAUGHT:
                expression_string += "0"
            else:
                expression_string += c

    return expression_string


def lambdify(expression, variables, independent_variable):
    expression_string = replace_symbols(expression)

    if independent_variable in variables:
        variables.pop(independent_variable)

    var_names = [independent_variable]
    var_names.extend([replace_symbols(var) for var in variables])

    lambda_expression = sp.lambdify(var_names, sp.sympify(expression_string), "numpy")

    return lambda_expression


def _shortened_run_id(run_id):
    return "_" + run_id.split('-')[0]


def _residual(lambda_expression):
    def residual(pars, x, y_data, dy_data):
        y_calc = lambda_expression(x, *pars)
        return (y_data - y_calc) / dy_data
    return residual
