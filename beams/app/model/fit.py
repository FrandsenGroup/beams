import numpy as np
import sympy as sp
from scipy.optimize import least_squares

from collections import OrderedDict
import time
import re

from app.resources import resources
from app.model import domain, files

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
INTERNAL_COSINE = "a*cos(2*\u03C0*v*t + \u03C0*\u03A6/180)*exp(-\u03BB*t) + (1-\u03B1)*exp(-\u03BB*t)"
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
    def __init__(self, expression_string):
        self.__expression_string = expression_string

        variables = parse(self.__expression_string)
        variables.discard(INDEPENDENT_VARIABLE)
        self.__expression = lambdify(self.__expression_string, variables, INDEPENDENT_VARIABLE)

    def __eq__(self, other):
        return str(other) == self.__expression_string

    def __str__(self):
        return self.__expression_string

    def __call__(self, *args, **kwargs):
        # The length of this function is due to the fact I have trust issues.

        if len(args) == 0:
            raise ValueError("FitExpression needs at least one parameter (an array).")
        elif not isinstance(args[0], np.ndarray):
            try:
                iter(args[0])
                time_array = np.array(args[0])
            except TypeError:
                raise ValueError("First parameter to FitExpression needs to be an array.")
        else:
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

        try:
            return self.__expression(time_array, *unnamed_pars, **pars)
        except TypeError:
            if ALPHA in pars.keys():
                pars.pop(ALPHA)
                return self.__expression(time_array, *unnamed_pars, **pars)
            raise


class FitConfig:
    LEAST_SQUARES = 1
    GLOBAL_PLUS = 2

    def __init__(self):
        self.expression = ''
        self.parameters = {}
        self.data = {}
        self.flags = 0

    def __str__(self):
        return "FitConfig ({})=({}, {})".format(self.expression, self.flags, self.parameters)

    def set_flags(self, *flags):
        self.flags = 0
        for flag in flags:
            self.flags = self.flags & flag

    def is_least_squares(self):
        return bool(self.flags & FitConfig.LEAST_SQUARES)

    def is_global_plus(self):
        return bool(self.flags & FitConfig.GLOBAL_PLUS)

    def get_symbols_for_run(self, run_id, is_fixed=None, is_global=None):
        symbols = []

        for symbol, parameter in self.parameters[run_id].items():
            if (is_fixed is None and is_global is None) \
                    or (is_fixed and (parameter.is_fixed or parameter.is_fixed_run)) \
                    or (is_fixed is not None and not (is_fixed and (parameter.is_fixed or parameter.is_fixed_run))) \
                    or (is_global and parameter.is_global) \
                    or (is_global is not None and not (is_global and parameter.is_global)):
                symbols.append(symbol)

        return symbols

    def get_values_for_run(self, run_id, is_fixed=None, is_global=None):
        values = []

        for _, parameter in self.parameters[run_id].items():
            if (is_fixed is None and is_global is None) \
                    or (is_fixed and (parameter.is_fixed or parameter.is_fixed_run)) \
                    or (is_fixed is not None and not (is_fixed and (parameter.is_fixed or parameter.is_fixed_run))) \
                    or (is_global and parameter.is_global) \
                    or (is_global is not None and not (is_global and parameter.is_global)):
                values.append(parameter.get_value())

        return values

    def get_lower_values_for_run(self, run_id, is_fixed=None, is_global=None):
        values = []

        for _, parameter in self.parameters[run_id].items():
            if (is_fixed is None and is_global is None) \
                    or (is_fixed and (parameter.is_fixed or parameter.is_fixed_run)) \
                    or (is_fixed is not None and not (is_fixed and (parameter.is_fixed or parameter.is_fixed_run))) \
                    or (is_global and parameter.is_global) \
                    or (is_global is not None and not (is_global and parameter.is_global)):
                values.append(parameter.lower)

        return values

    def get_upper_values_for_run(self, run_id, is_fixed=None, is_global=None):
        values = []

        for _, parameter in self.parameters[run_id].items():
            if (is_fixed is None and is_global is None) \
                    or (is_fixed and (parameter.is_fixed or parameter.is_fixed_run)) \
                    or (is_fixed is not None and not (is_fixed and (parameter.is_fixed or parameter.is_fixed_run))) \
                    or (is_global and parameter.is_global) \
                    or (is_global is not None and not (is_global and parameter.is_global)):
                values.append(parameter.upper)

        return values

    def set_outputs(self, run_id, symbol, output, uncertainty):
        self.parameters[run_id][symbol].value = output  # You may be tempted to keep this value. Go for it.
        self.parameters[run_id][symbol].output = output
        self.parameters[run_id][symbol].uncertainty = uncertainty


class FitDataset:
    def __init__(self):
        t = time.localtime()
        current_time = time.strftime("%d-%m-%Y-%H-%M-%S", t)

        self.id = str(current_time)
        self.fits = {}
        self.options = {}
        self.function = None

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


class Fit:
    def __init__(self):
        self.__variables = dict()
        self.kwargs = dict()
        self.expression_as_string = None
        self.expression = None
        self.bin_size = None
        self.x_min = None
        self.x_max = None
        self.title = None
        self.run_id = None

    @property
    def variables(self):
        return self.__variables

    @variables.setter
    def variables(self, variables):
        self.__variables = variables
        self.kwargs = {}
        for var in self.__variables.values():
            if not var.is_fixed:
                self.kwargs[var.symbol] = var.value

    def __call__(self, *args, **kwargs):
        if len(args) < 1 or not isinstance(args[0], np.ndarray):
            raise ValueError("Only takes numpy array of values as an input.")
        return self.expression(args[0], **self.kwargs)

    def write(self, out_file):
        run = domain.RunService.get_runs_by_ids([self.run_id])[0]
        meta_string = files.TITLE_KEY + ":" + str(run.meta[files.TITLE_KEY]) + "," \
                      + files.BIN_SIZE_KEY + ":" + str(self.bin_size) + "," \
                      + files.TEMPERATURE_KEY + ":" + str(run.meta[files.TEMPERATURE_KEY]) + "," \
                      + files.FIELD_KEY + ":" + str(run.meta[files.FIELD_KEY]) + "," \
                      + files.T0_KEY + ":" + str(run.meta[files.T0_KEY])

        asymmetry = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].raw()

        for v in self.__variables.values():
            if v.symbol == ALPHA:
                asymmetry = asymmetry.correct(v.value)

        asymmetry = asymmetry.bin(self.bin_size).cut(self.x_min, self.x_max)
        calculated_asymmetry = self(asymmetry.time)

        np.savetxt(out_file, np.c_[asymmetry.time, asymmetry, calculated_asymmetry, asymmetry.uncertainty],
                   fmt='%2.9f, %2.4f, %2.4f, %2.4f', header="BEAMS\n" + meta_string + "\nTime, Asymmetry, Calculated, Uncertainty")


class FitEngine:
    def __init__(self):
        self.__run_service = domain.RunService()

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

    def _least_squares_fit_global(self, spec):
        # (0) Get the parameters for our variables. These are generated to work with our stepwise approach.
        guesses = spec.get_global_fit_guesses()
        lowers = spec.get_global_fit_lowers()
        uppers = spec.get_global_fit_uppers()

        # 1) Concatenate our time, asymmetry and uncertainty arrays for each dataset together.
        concatenated_asymmetry = np.array([])
        concatenated_uncertainty = np.array([])
        concatenated_time = np.array([])
        for _, asymmetry in spec.get_data().items():
            concatenated_asymmetry = np.concatenate((concatenated_asymmetry, asymmetry))
            concatenated_uncertainty = np.concatenate((concatenated_uncertainty, asymmetry.uncertainty))
            concatenated_time = np.concatenate((concatenated_time, asymmetry.time))

        # 2) Create a single global lambda function for all the datasets. Essentially, it acts like a 
        #    stepwise function, once you pass into the asymmetry of another dataset, a separate function
        #    in the lambda will start being used. See its definition for more on why.
        global_lambda_expression = FitEngine._lambdify_global(spec, concatenated_time)
        residual = FitEngine._residual(global_lambda_expression)

        dataset = FitDataset()
        
        # 3) Run a lease squres fit on the global lambda and concatenated datasets
        try:
            opt = least_squares(residual, guesses, bounds=[lowers, uppers], args=(concatenated_time, concatenated_asymmetry, concatenated_uncertainty))
        except ValueError:
            print('You have found an elusive bug. Please submit an issue on github with your actions prior to pressing "fit"')
            print(residual, guesses, [lowers, uppers], (len(concatenated_time), len(concatenated_asymmetry), len(concatenated_uncertainty)))
            import traceback
            traceback.print_exc()
            raise ValueError("Provide all the information above and submit to a github issue please!")

        values = {}
        for i, symbol in enumerate(spec.get_global_fit_symbols()):
            values[symbol] = opt.x[i]

        for run_id, _ in spec.get_data().items():
            new_fit = Fit()
            final_variables = {k: FitVar(v.symbol, v.name, v.value,
                                         v.is_fixed, v.lower, v.upper,
                                         v.is_global, v.independent) for k, v in spec.variables.items()}

            for symbol, var in final_variables.items():
                if var.is_fixed:
                    continue

                if not var.is_global:
                    final_variables[symbol].value = values[symbol + _shortened_run_id(run_id)]
                else:
                    final_variables[symbol].value = values[symbol]

            lambda_expression_without_alpha = lambdify(FitEngine._replace_fixed(spec.function, spec.get_fixed_symbols(), spec.get_fixed_guesses()),
                                                       list(spec.get_unfixed_symbols()), INDEPENDENT_VARIABLE)

            new_fit.variables = final_variables
            new_fit.expression = FitExpression(spec.function, None, lambda_expression_without_alpha)
            new_fit.expression_as_string = spec.function
            new_fit.run_id = run_id
            new_fit.title = self.__run_service.get_runs_by_ids([run_id])[0].meta['Title']
            new_fit.bin_size = spec.get_bin_size()
            new_fit.x_min = spec.get_min_time()
            new_fit.x_max = spec.get_max_time()
            dataset.fits[run_id] = new_fit

        dataset.options = spec.options.copy()
        dataset.function = spec.function

        return dataset

    def _least_squares_fit_non_global(self, config) -> FitDataset:
        dataset = FitDataset()

        for run_id, asymmetry in config.data.items():
            if len(config.get_symbols_for_run(run_id, is_fixed=False)) == 0:
                # TODO Performing a fit will break in this case so we need to handle it.
                pass

            fixed_symbols = config.get_symbols_for_run(run_id, is_fixed=True)
            fixed_values = config.get_values_for_run(run_id, is_fixed=True)

            # We create a separate lambda expression for each run in case they set separate run dependant fixed values.
            alpha_corrected_function = ALPHA_CORRECTION.format(config.expression, config.expression)
            function = FitEngine._replace_fixed(alpha_corrected_function, fixed_symbols, fixed_values)
            lambda_expression = FitExpression(function)
            residual = FitEngine._residual(lambda_expression)

            guesses = config.get_values_for_run(run_id, is_fixed=False)
            lowers = config.get_lower_values_for_run(run_id, is_fixed=False)
            uppers = config.get_upper_values_for_run(run_id, is_fixed=False)

            # 6) Perform a least squares fit
            opt = least_squares(residual, guesses, bounds=[lowers, uppers],
                                args=(asymmetry.time, asymmetry, asymmetry.uncertainty))

            # 7) Replace initial values with fitted values for unfixed variables
            for i, symbol in enumerate(config.get_symbols_for_run(run_id, is_fixed=False)):
                config.set_outputs(run_id, symbol, opt.x[i], 0)

            # 8) Create a callable function of our original string function
            lambda_expression = FitExpression(config.expression)

            # 9) Fill in all values for our new fit object
            new_fit.variables = final_variables
            new_fit.expression = FitExpression(spec.function, None, lambda_expression_without_alpha)
            new_fit.expression_as_string = spec.function
            new_fit.run_id = run_id
            new_fit.title = self.__run_service.get_runs_by_ids([run_id])[0].meta['Title']
            new_fit.bin_size = spec.get_bin_size()
            new_fit.x_min = spec.get_min_time()
            new_fit.x_max = spec.get_max_time()

            # 10) Add fit to our dataset
            dataset.fits[run_id] = new_fit

        # 11) Attach fit spec options and function to dataset (mostly for debugging purposes)
        dataset.options = spec.options.copy()
        dataset.function = spec.function

        return dataset

    @staticmethod
    def _lambdify_global(spec: FitConfig, concatenated_time):
        if spec.options[FitOptions.ALPHA_CORRECT]:
            alpha_corrected_function = ALPHA_CORRECTION.format(spec.function, spec.function)
            function = FitEngine._replace_fixed(alpha_corrected_function, spec.get_fixed_symbols(), spec.get_fixed_guesses())
        else:
            function = FitEngine._replace_fixed(spec.function, spec.get_fixed_symbols(), spec.get_fixed_guesses())

        print('Initial Function : ', function)
        lambdas = OrderedDict()
        run_id_order = []
        for i, (run_id, asymmetry) in enumerate(spec.get_data().items()):
            new_function = function
            for var in spec.get_non_global_symbols():
                new_function = FitEngine._replace_var_with(new_function, var, var + _shortened_run_id(run_id))

            print('For run (' + run_id + ') we have function : ', new_function)
            new_lambda_expression = lambdify(new_function, spec.get_global_fit_symbols(), INDEPENDENT_VARIABLE)
            lambdas[run_id] = new_lambda_expression
            run_id_order.append(run_id)

            print('\tThis function will apply until time : ', concatenated_time[((i + 1) * spec.get_data_length()) - 1])

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
    # fixme bug when smaller variable names (like 'd') occur in other variables.
    def _replace_fixed(function, symbols, values):
        for symbol, value in zip(symbols, values):
            function = re.sub(r'(?<=\b){}(?=\b)'.format(symbol), str(value), function)
        return function

    @staticmethod
    # fixme bug when smaller variable names (like 'd') occur in other variables.
    def _replace_var_with(function, old_symbol, new_symbol):
        return function.replace(old_symbol, new_symbol)


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
    chisq = rw ** 2 / r_exp ** 2
    return p_unc, chisq


def parse(s):
    """ Takes in an expression as a string and returns a set of the free variables. """

    # Add to these sets any keywords you want to be recognized as not variables.
    # Keep keywords lowercase, user input will be cast to lowercase for comparison.
    operator_set = ('+', '-', '/', '*', '(', ')', '[', ']', '{', '}', '^', '!')
    key_1_char_set = ('e', 'i', PI)
    key_2_char_set = ('pi')
    key_3_char_set = ('sin', 'cos', 'tan', 'exp')
    key_4_char_set = ('sinh', 'cosh', 'tanh')

    free_set = set()
    free_variable = []
    skip_chars = 0

    for i, character in enumerate(s):
        if skip_chars > 0:
            skip_chars -= 1
            continue

        if character.isspace() or character in operator_set:
            free_variable_joined = "".join(free_variable)
            free_set.add(free_variable_joined)
            free_variable = []

        elif character.isalpha():
            if s[i:i + 4].lower() in key_4_char_set:
                skip_chars = 3
                continue
            elif s[i:i + 3].lower() in key_3_char_set:
                skip_chars = 2
                continue
            elif s[i:i + 2].lower() in key_2_char_set:
                skip_chars = 1
                continue
            elif len(free_variable) == 0 and (s[i] in key_1_char_set or s[i].lower() in key_1_char_set) and \
                    (i == len(s) - 1 or s[i + 1] in operator_set or s[i + 1].isspace()):
                continue
            else:
                free_variable.append(character)

        elif character.isdigit():
            if free_variable:
                free_variable.append(character)

    free_variable_joined = "".join(free_variable)
    free_set.add(free_variable_joined)
    free_set.remove('')

    return free_set


def is_valid_expression(expression):
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
    return run_id.split('-')[0]





class Fit(np.ndarray):
    def __new__(cls, *args, **kwargs):
        pass


class FitDataset:
    def __init__(self):
        pass


def _residual(lambda_expression):
    def residual(pars, x, y_data, dy_data):
        y_calc = lambda_expression(x, *pars)
        return (y_data - y_calc) / dy_data
    return residual


t0 = 'a + b + c + d + x + t'
t1 = FitExpression(t0)
t6 = _residual(t1)
t2 = FitParameter('a', 1, 0, None, None, False, False)
t3 = FitParameter('b', 2, 0, None, None, False, False)
t4 = FitParameter('c', 3, 0, None, None, False, False)
t5 = np.array([0, 1, 2, 3])

print(t2, t3, t4)
print(t1)
print(t1(t5, *(1, 2, 3, 4, 5)))
print(t1(t5, a=1, b=2, c=3, d=4, x=5))
print(t1(t5, *(t2, t3, t4), d=4, x=5))

opt = least_squares(t6, [1, 2, 3, 4, 5], bounds=[[-100, -100, -100, -100, -100], [100, 100, 100, 100, 100]],
                                    args=(np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), np.array([5, 2, 1, 4, 5, 2, 7, 6, 9, 10]), np.array([1, 2, 1, 2, 1, 2, 1, 1, 1, 2])))

# tspec = FitSpec()
# tfunction = 't + az - bz - dz + cz'
# tvara = FitVar('az', 'a', 1, False, 0, 4, True, False)
# tvarb = FitVar('bz', 'b', 1, False, 0, 4, False, False)
# tvarc = FitVar('cz', 'c', 1, True, 0, 4, True, False)
# tvard = FitVar('dz', 'd', 1, False, 0, 4, False, False)
# tdata1 = [1, 2, 3, 4, 5]
# tdata2 = [2, 3, 4, 5, 6]
# tdataid1 = 'data1'
# tdataid2 = 'data2'
# tspec.function = tfunction
# tspec.variables = {'az': tvara, 'bz': tvarb, 'cz': tvarc, 'dz': tvard}
# tspec.asymmetries = {tdataid1: tdata1, tdataid2: tdata2}
# # tspec.options[FitOptions.ALPHA_CORRECT] = True
# ttime = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
#
# # print(tspec.get_data())
# # for i, j in enumerate(tspec.get_data().items()):
# #     print(i, j)
#
# print(tspec.get_global_fit_symbols())
# texpr = FitEngine._lambdify_global(tspec, ttime)
# print(texpr(4, az=2, bzdata1=3, bzdata2=4, dzdata1=5, dzdata2=6), texpr(11, az=2, bzdata1=3, bzdata2=4, dzdata1=5, dzdata2=6))


# test_expression = 't + c - b'
# test_variables = {'c', 'b', 'd'}
# test_independent = 't'
# test_lambda = lambdify(test_expression, test_variables, test_independent)
# print(test_lambda(1, d=3, b=7, c=11))
# # print(np.array([4.2, 3, 2, 1]).dtype)
# # print(test_lambda(np.array([4.2,3,2,1]), **{'c': 4, 'b': 1}))
#
# fit = Fit()
# fit.variables = {'c': FitVar('c', 'c', 0, 1, -3, 3, True, False), 'b': FitVar('b', 'b', 1, 1, -3, 3, True, False)}
# fit.expression_as_lambda = test_lambda
# print(asy)

# f(x, t)
