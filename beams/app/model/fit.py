import sys
import uuid

import numpy as np
import sympy as sp
from scipy.optimize import least_squares

from collections import OrderedDict
import re
import logging
import copy

from app.model import objects
from app.util import report

INDEPENDENT_VARIABLE = "t"

DELTA = "\u0394"
LAMBDA = "\u03BB"
BETA = "\u03B2"
SIGMA = "\u03C3"
ALPHA = "\u03B1"
PHI = "\u03A6"
PI = "\u03C0"
NAUGHT = "\u2080"

SIMPLE_EXPONENTIAL = f"a*exp(-{LAMBDA}*t)"
STRETCHED_EXPONENTIAL = f"a*exp(-({LAMBDA}*t)^{BETA})"
SIMPLE_GAUSSIAN = f"a*exp(-1/2*({SIGMA}*t)^2)"
GAUSSIAN_KT = f"a*(1/3 + 2/3*(1 - ({SIGMA}*t)^2)*exp(-1/2*({SIGMA}*t)^2))"
LORENTZIAN_KT = f"a*(1/3 + 2/3*(1 - {LAMBDA}*t)*exp(-{LAMBDA}*t))"
COMBINED_KT = f"a*(1/3 + 2/3*(1-{SIGMA}^2*t^2-{LAMBDA}*t)*exp(-{SIGMA}^2*t^2/2-{LAMBDA}*t))"
STRETCHED_KT = f"a*(1/3 + 2/3*(1-({SIGMA}*t)^{BETA})*exp(-({SIGMA}*t)^{BETA}/{BETA}))"
DAMPED_COSINE = f"a*cos(2*{PI}*v*t + {PI}*{PHI}/180)*exp(-{BETA}*t)"
INTERNAL_COSINE = f"a*(f*cos(2*{PI}*v*t + {PI}*{PHI}/180)*exp(-{LAMBDA}T*t) + (1 - f)*exp(-{LAMBDA}L*t))"
BESSEL = f"a*jn(0, 2*{PI}*v*t + {PI}*{PHI}/180)"
INTERNAL_BESSEL = f"a*(f*jn(0,2*{PI}*v*t + {PI}*{PHI}/180)*exp(-{LAMBDA}T*t) + (1-f)*exp(-{LAMBDA}L*t))"

EQUATION_DICTIONARY = {
    "Simple Exponential": SIMPLE_EXPONENTIAL,
    "Stretched Exponential": STRETCHED_EXPONENTIAL,
    "Simple Gaussian": SIMPLE_GAUSSIAN,
    "Gaussian KT": GAUSSIAN_KT,
    "Lorentzian KT": LORENTZIAN_KT,
    "Combined KT": COMBINED_KT,
    "Stretched KT": STRETCHED_KT,
    "Damped Cosine": DAMPED_COSINE,
    "Internal Cosine": INTERNAL_COSINE,
    "Bessel": BESSEL,
    "Internal Bessel": INTERNAL_BESSEL
}

DEFAULT_VALUES = {
    "Simple Exponential": {'a': 0.25, LAMBDA: 0.1},
    "Stretched Exponential": {'a': 0.25, LAMBDA: 0.1, BETA: 1},
    "Simple Gaussian": {'a': 0.25, SIGMA: 0.1},
    "Gaussian KT": {'a': 0.25, SIGMA: 0.1},
    "Lorentzian KT": {'a': 0.25, LAMBDA: 1},
    "Combined KT": {'a': 0.25, SIGMA: 1, LAMBDA: 1},
    "Stretched KT": {'a': 0.25, SIGMA: 1, BETA: 1},
    "Damped Cosine": {'a': 0.25, PHI: 0, BETA: 1, 'v': 1},
    "Internal Cosine": {'a': 0.25, 'f': 0.667, 'v': 1, PHI: 0, f'{LAMBDA}T': 1, f'{LAMBDA}L': 0.1},
    "Bessel": {'a': 0.25, 'v': 1, PHI: 0},
    "Internal Bessel": {'a': 0.25, 'f': 0.667, 'v': 1, PHI: 0, f'{LAMBDA}T': 1, f'{LAMBDA}L': 0.1}
}

USER_EQUATION_DICTIONARY = {}


class FitParameter:
    def __init__(self, symbol, value, lower, upper, is_global, is_fixed, is_run_specific=False, output=None, uncertainty=None):
        self.uncertainty = uncertainty
        self.output = output
        self.upper = upper
        self.lower = lower
        self.value = value
        self.symbol = symbol
        self.is_fixed = is_fixed
        self.is_run_specific = is_run_specific
        self.is_global = is_global

    def __copy__(self):
        return FitParameter(self.symbol, self.value, self.lower, self.upper, self.is_global, self.is_fixed, self.is_run_specific, self.output, self.uncertainty)

    def __eq__(self, other):
        return other.symbol == self.symbol \
               and other.value == self.value \
               and other.lower == self.lower \
               and other.upper == self.upper \
               and other.is_global == self.is_global \
               and other.is_fixed == self.is_fixed \
               and other.is_run_specific == self.is_run_specific \
               and other.output == self.output \
               and other.uncertainty == self.uncertainty

    def __str__(self):
        return '{}={}'.format(self.symbol, self.value)

    def __repr__(self):
        return 'FitParameter({}, {}, {}, {}, {}, {}, {})'.format(self.symbol, self.value, self.lower, self.upper,
                                                                 self.is_global, self.is_fixed, self.is_run_specific)

    def get_value(self):
        return float(self.value)


class FitExpression:
    def __init__(self, expression_string, variables=None):
        self.__expression_string = expression_string

        if variables is None:
            variables = parse(self.__expression_string)
            variables.discard(INDEPENDENT_VARIABLE)

        self.__variables = variables
        self.__expression = lambdify(self.__expression_string, variables)
        self.__fixed = {}
        self.safe = True

    def __getstate__(self):
        return (self.__expression_string, self.__variables, self.__fixed, self.safe)

    def __setstate__(self, state):
        self.__expression_string = state[0]
        self.__variables = state[1]
        self.__expression = lambdify(self.__expression_string, self.__variables)
        self.__fixed = state[2]
        self.safe = state[3]

    def __eq__(self, other):
        return str(other) == self.__expression_string

    def __str__(self):
        return self.__expression_string

    def __repr__(self):
        return f'FitExpression({self.__expression_string}, {self.__expression}, {self.__fixed}, {self.safe})'

    def __call__(self, *args, **kwargs):
        # The length of this function is due to the fact I have trust issues.
        if not self.safe:
            return self.__expression(*args, **{_replace_unsupported_unicode_characters(k): v for k, v in kwargs.items()})

        # We need to cast it to a complex type in order to avoid errors where we are raising a negative
        # number to a fractional power (which would result in an array of Nan's usually). We do the calculation
        # and then take the real component below.
        time_array = np.array(args[0], dtype=complex)

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
            pars[_replace_unsupported_unicode_characters(k)] = v

        for symbol, value in self.__fixed.items():
            pars[_replace_unsupported_unicode_characters(symbol)] = value

        try:
            return self.__expression(time_array, *unnamed_pars, **pars).real
        except TypeError:
            if ALPHA in pars.keys():
                pars.pop(ALPHA)
                return self.__expression(time_array, *unnamed_pars, **pars).real
            raise

    def set_fixed(self, parameters):
        self.__fixed = {_replace_unsupported_unicode_characters(symbol): parameter.value for symbol, parameter in parameters}


class FitConfig:
    """

    IMPORTANT NOTE : All of the get function use a for loop on self.parameters.items(). Always do this to keep the order
    of the items we get out consistent. The least squares method we use doesn't let us specify the value or lower bound
    etc of a symbol except by passing in arrays ordered the same as the array of symbols.

    """

    def __init__(self):
        self.expression = ''
        self.parameters = {}
        self.titles = {}
        self.data = OrderedDict()  # Important so we can specify order of runs to be fitted for batch fit.
        self.batch = True
        self.flags = 0

    def __repr__(self):
        return f"FitConfig({self.expression}, {self.parameters}, {self.titles}, {self.batch}, {self.flags}, {self.data})"

    def set_flags(self, *flags):
        self.flags = 0
        for flag in flags:
            self.flags = self.flags | flag

    def is_global(self):
        is_global = False
        for par_dict in self.parameters.values():
            for par in par_dict.values():
                is_global = is_global or par.is_global
        return is_global

    def is_batch(self):
        return self.batch

    def is_plus(self):
        return self.is_batch() and self.is_global()

    def get_symbols_for_run(self, run_id, is_fixed=None, is_global=None):
        symbols = []
        for symbol, parameter in self.parameters[run_id].items():
            if (is_fixed is None or (is_fixed == parameter.is_fixed)) and \
                    (is_global is None or (is_global == parameter.is_global)):
                symbols.append(symbol)

        return symbols

    def get_values_for_run(self, run_id, is_fixed=None, is_global=None):
        values = []

        for _, parameter in self.parameters[run_id].items():
            if (is_fixed is None or (is_fixed == parameter.is_fixed)) and \
                    (is_global is None or (is_global == parameter.is_global)):
                values.append(parameter.get_value())

        return np.array(values, dtype=float)

    def get_lower_values_for_run(self, run_id, is_fixed=None, is_global=None):
        values = []

        for _, parameter in self.parameters[run_id].items():
            if (is_fixed is None or (is_fixed == parameter.is_fixed)) and \
                    (is_global is None or (is_global == parameter.is_global)):
                values.append(parameter.lower)

        return np.array(values, dtype=float)

    def get_upper_values_for_run(self, run_id, is_fixed=None, is_global=None):
        values = []

        for _, parameter in self.parameters[run_id].items():
            if (is_fixed is None or (is_fixed == parameter.is_fixed)) and \
                    (is_global is None or (is_global == parameter.is_global)):
                values.append(parameter.upper)

        return np.array(values, dtype=float)

    def get_adjusted_global_symbols(self):
        symbols = []
        for i, run_id in enumerate(self.parameters.keys()):
            for symbol, parameter in self.parameters[run_id].items():
                if parameter.is_fixed:
                    continue
                if parameter.is_global and i == 0:
                    symbols.append(symbol)
                elif not parameter.is_global:
                    symbols.append(symbol + _shortened_run_id(run_id))

        return symbols

    def get_adjusted_global_values(self):
        values = []
        for i, run_id in enumerate(self.parameters.keys()):
            for _, parameter in self.parameters[run_id].items():
                if parameter.is_fixed:
                    continue
                if (parameter.is_global and i == 0) or (not parameter.is_global):
                    values.append(float(parameter.get_value()))

        return np.array(values, dtype=float)

    def get_adjusted_global_lowers(self):
        lowers = []
        for i, run_id in enumerate(self.parameters.keys()):
            for _, parameter in self.parameters[run_id].items():
                if parameter.is_fixed:
                    continue
                if (parameter.is_global and i == 0) or (not parameter.is_global):
                    lowers.append(float(parameter.lower))

        return np.array(lowers, dtype=float)

    def get_adjusted_global_uppers(self):
        uppers = []
        for i, run_id in enumerate(self.parameters.keys()):
            for _, parameter in self.parameters[run_id].items():
                if parameter.is_fixed:
                    continue
                if (parameter.is_global and i == 0) or (not parameter.is_global):
                    uppers.append(float(parameter.upper))

        return np.array(uppers, dtype=float)

    def get_kwargs(self, run_id):
        kwargs = {}
        for symbol, parameter in self.parameters[run_id].items():
            if symbol != ALPHA:
                kwargs[symbol] = parameter.get_value()
        return kwargs

    def set_outputs(self, run_id, symbol, output, uncertainty):
        self.parameters[run_id][symbol].value = output
        self.parameters[run_id][symbol].output = output
        self.parameters[run_id][symbol].fixed_value = output
        self.parameters[run_id][symbol].uncertainty = uncertainty


class FitEngine:
    def __init__(self):
        self.__logger = logging.getLogger(__name__)

    def fit(self, config: FitConfig) -> objects.FitDataset:
        report.log_debug("Config passed to FitEngine: {}".format(str(config)))

        if len(set([len(asymmetry) for asymmetry in config.data.values()])) != 1:
            raise ValueError("Must have one or more datasets all of equal length to fit")

        if config.expression == '':
            raise ValueError("Empty function attribute")

        if config.is_plus():
            return self._fit_global_plus(config)
        elif config.is_global():
            return self._fit_global(config)
        elif config.is_batch():
            return self._fit_batch(config)
        else:
            return self._fit_non_global(config)

    def _fit_global_plus(self, config: FitConfig):
        dataset = self._fit_batch(config)
        # FIXME how will truly run dependent fixed values affect this line below?
        mean_values = {symbol: np.mean([f.parameters[symbol].output for f in dataset.fits.values()]) for symbol in
                       list(dataset.fits.values())[0].parameters.keys()}
        for _, parameters in config.parameters.items():
            for symbol, par in parameters.items():
                if par.is_global:
                    par.value = mean_values[par.symbol]

        dataset = self._fit_global(config)
        dataset.flags |= objects.FitDataset.Flags.GLOBAL_PLUS

        return dataset

    def _fit_batch(self, config: FitConfig):
        dataset = objects.FitDataset()
        dataset.flags |= objects.FitDataset.Flags.BATCH

        for run_id, (time, asymmetry, uncertainty, meta) in config.data.items():
            # We create a separate lambda expression for each run in case they set separate run dependant fixed values.
            function = alpha_correction(config.expression)

            # Replace the symbols with fixed values with their actual values. This way they don't throw off uncertainty.
            fixed_symbols = config.get_symbols_for_run(run_id, is_fixed=True)
            fixed_values = config.get_values_for_run(run_id, is_fixed=True)
            function = FitEngine._replace_fixed(function, fixed_symbols, fixed_values)

            # Create a residual expression for the least squares fit
            lambda_expression = FitExpression(function, variables=config.get_symbols_for_run(run_id, is_fixed=False))
            residual = FitEngine._residual(lambda_expression)

            guesses = config.get_values_for_run(run_id, is_fixed=False)
            lowers = config.get_lower_values_for_run(run_id, is_fixed=False)
            uppers = config.get_upper_values_for_run(run_id, is_fixed=False)

            # 6) Perform a least squares fit
            try:
                opt = least_squares(residual, guesses, bounds=[lowers, uppers],
                                    args=(time, asymmetry, uncertainty))
            except Exception:
                raise Exception(str(sys.exc_info()))

            try:
                unc, chi_sq = get_std_unc(opt, asymmetry)
            except (np.linalg.LinAlgError, NameError):  # Fit did not converge
                unc = [-1 for _ in opt.x]
                chi_sq = 0.0

            # 7) Replace initial values with fitted values for unfixed variables
            for i, symbol in enumerate(config.get_symbols_for_run(run_id, is_fixed=False)):
                for o_run_id in config.data.keys():
                    config.set_outputs(o_run_id, symbol, opt.x[i], unc[i])

            for symbol, value in zip(fixed_symbols, fixed_values):
                for o_run_id in config.data.keys():
                    config.set_outputs(o_run_id, symbol, value, 0)

            # 9) Fill in all values for our new fit object
            new_fit = objects.Fit(copy.deepcopy(config.parameters[run_id]), config.expression, config.titles[run_id], run_id, meta, asymmetry, goodness=chi_sq)

            # 10) Add fit to our dataset
            dataset.fits[run_id] = new_fit

        # 11) Attach fit spec options and function to dataset (mostly for debugging purposes)
        dataset.expression = config.expression
        return dataset

    def _fit_global(self, config: FitConfig):
        # The methods from config will get the adjusted symbols, values, etc. in the same order every time for a global
        #   fit (which is necessary because we can't specify which value belongs to which symbol in the scipy least
        #   squares function.
        guesses = config.get_adjusted_global_values()
        lowers = config.get_adjusted_global_lowers()
        uppers = config.get_adjusted_global_uppers()

        # We are essentially doing one big fit where you will have global and local (local to a specific section of the
        #   concatenated asymmetry) parameters being refined.
        concatenated_asymmetry = np.array([])
        concatenated_uncertainty = np.array([])
        concatenated_time = np.array([])
        for _, (time, asymmetry, uncertainty, _) in config.data.items():
            concatenated_asymmetry = np.concatenate((concatenated_asymmetry, asymmetry))
            concatenated_uncertainty = np.concatenate((concatenated_uncertainty, uncertainty))
            concatenated_time = np.concatenate((concatenated_time, time))

        # Create a single global lambda function for all the datasets. Essentially, it acts like a
        #    stepwise function, once you pass into the asymmetry of another dataset, a separate function
        #    in the lambda will start being used. See its definition for more on why.
        global_lambda_expression = self._lambdify_global(config)
        residual = FitEngine._residual(global_lambda_expression)

        # Run a lease squares fit with the global lambda and concatenated datasets
        try:
            opt = least_squares(residual, guesses, bounds=[lowers, uppers],
                                args=(concatenated_time, concatenated_asymmetry, concatenated_uncertainty))
        except Exception:
            raise Exception(str(sys.exc_info()))

        try:
            unc, chi_sq = get_std_unc(opt, concatenated_asymmetry)
        except (np.linalg.LinAlgError, NameError):  # Fit did not converge
            unc = [-1 for _ in opt.x]
            chi_sq = 0.0

        # Assemble the Fit object, first by updating the parameters in the config with the outputs from
        #   the fit, as well as adding a FitExpression object that can be called.
        dataset = objects.FitDataset()
        dataset.flags |= objects.FitDataset.Flags.GLOBAL

        values = {}
        uncertainties = {}
        for i, symbol in enumerate(config.get_adjusted_global_symbols()):
            values[symbol] = opt.x[i]
            uncertainties[symbol] = unc[i]

        for run_id, (_, asymmetry, _, meta) in config.data.items():
            for symbol, parameter in config.parameters[run_id].items():
                if parameter.is_fixed:
                    continue

                if not parameter.is_global:
                    config.set_outputs(run_id, symbol,
                                       values[symbol + _shortened_run_id(run_id)],
                                       uncertainties[symbol + _shortened_run_id(run_id)])
                else:
                    config.set_outputs(run_id, symbol, values[symbol], uncertainties[symbol])

            fixed_symbols = config.get_symbols_for_run(run_id, is_fixed=True)
            fixed_values = config.get_values_for_run(run_id, is_fixed=True)
            for symbol, value in zip(fixed_symbols, fixed_values):
                config.set_outputs(run_id, symbol, value, 0)

            new_fit = objects.Fit(config.parameters[run_id], config.expression, config.titles[run_id], run_id, meta, asymmetry, goodness=chi_sq)

            dataset.fits[run_id] = new_fit

        dataset.expression = config.expression

        return dataset

    def _fit_non_global(self, config) -> objects.FitDataset:
        dataset = objects.FitDataset()

        for run_id, (time, asymmetry,  uncertainty, meta) in config.data.items():
            # We create a separate lambda expression for each run in case they set separate run dependant fixed values.
            function = alpha_correction(config.expression)

            # Replace the symbols with fixed values with their actual values. This way they don't throw off uncertainty.
            fixed_symbols = config.get_symbols_for_run(run_id, is_fixed=True)
            fixed_values = config.get_values_for_run(run_id, is_fixed=True)
            function = FitEngine._replace_fixed(function, fixed_symbols, fixed_values)

            # Create a residual expression for the least squares fit
            lambda_expression = FitExpression(function, variables=config.get_symbols_for_run(run_id, is_fixed=False))
            residual = FitEngine._residual(lambda_expression)

            guesses = config.get_values_for_run(run_id, is_fixed=False)
            lowers = config.get_lower_values_for_run(run_id, is_fixed=False)
            uppers = config.get_upper_values_for_run(run_id, is_fixed=False)

            # 6) Perform a least squares fit
            try:
                opt = least_squares(residual, guesses, bounds=[lowers, uppers],
                                    args=(time, asymmetry, uncertainty))
            except Exception:
                raise Exception(str(sys.exc_info()))

            try:
                unc, chi_sq = get_std_unc(opt, asymmetry)
            except (np.linalg.LinAlgError, NameError):  # Fit did not converge
                unc = [-1 for _ in opt.x]
                chi_sq = 0.0

            # 7) Replace initial values with fitted values for unfixed variables
            for i, symbol in enumerate(config.get_symbols_for_run(run_id, is_fixed=False)):
                config.set_outputs(run_id, symbol, opt.x[i], unc[i])

            for symbol, value in zip(fixed_symbols, fixed_values):
                config.set_outputs(run_id, symbol, value, 0)

            # 9) Fill in all values for our new fit object
            new_fit = objects.Fit(config.parameters[run_id], config.expression, config.titles[run_id], run_id, meta, asymmetry, goodness=chi_sq)

            # 10) Add fit to our dataset
            dataset.fits[run_id] = new_fit

        # 11) Attach fit spec options and function to dataset (mostly for debugging purposes)
        dataset.expression = config.expression
        return dataset

    @staticmethod
    def _lambdify_global(config: FitConfig):
        """ Creates a single lambda expression for a global fit.

            In a global fit we will have some parameters that are fit locally, for a single run, and some that are fit
            across all runs. To get this to work with a single residual function for scipy least_squares we essentially
            create a piecewise function where we apply different lambdas to different sections of the concatenated
            arrays.

            Example:
                Fitting three asymmetries.

                a * t + b / c
                a, b are local parameters
                c is a global parameter

                arr = a1 | a2 | a3

                The lambda that is created would essentially look like this.

                f(arr, pars) = {
                    a1 => a1 * t + b1 / c
                    a2 => a2 * t + b2 / c
                    a3 => a3 * t + b3 / c

                So you can see we append some unique value (a piece of the run id) to end of the local parameters so
                they are only fit to that specific section while we use the global parameter throughout.
        """

        function = alpha_correction(config.expression)

        lambdas = []
        lengths = []
        ends = []
        starts = []
        number_runs = len(config.data.items())

        for i, (run_id, asymmetry) in enumerate(config.data.items()):
            fixed_symbols = config.get_symbols_for_run(run_id, is_fixed=True)
            fixed_values = config.get_values_for_run(run_id, is_fixed=True)
            new_function = FitEngine._replace_fixed(function, fixed_symbols, fixed_values)

            for symbol in config.get_symbols_for_run(run_id, is_fixed=False, is_global=False):
                new_function = FitEngine._replace_var_with(new_function, symbol, symbol + _shortened_run_id(run_id))

            new_lambda_expression = FitExpression(new_function, variables=config.get_adjusted_global_symbols())
            new_lambda_expression.safe = False  # No type checks, speeds up the fit dramatically.
            lambdas.append(new_lambda_expression)

            starts.append(sum(lengths))
            lengths.append(int(len(asymmetry[0])))
            ends.append(starts[-1] + lengths[-1])

        def _lambda_expression(arr, *pars, **kwargs):
            values = [lambdas[j](arr[starts[j]: ends[j]], *pars, **kwargs) for j in range(number_runs)]
            return np.hstack(values)

        return _lambda_expression

    @staticmethod
    def _residual(lambda_expression):
        def residual(pars, x, y_data, dy_data):
            y_calc = lambda_expression(np.array(x, dtype=complex), *pars).real
            return np.divide(np.subtract(y_data, y_calc), dy_data)

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


def parse(s: str) -> set:
    f""" Takes in an expression as a string and returns a set of the free variables. 
    
    Note that this means it will not return {INDEPENDENT_VARIABLE} in the set. This method also expects
    that the expression will NOT be in the form 'a(t) = x*t' but simply 'x*t'. 
    
    Parameters
    ----------
        s : str
            The string form of the expression we are to parse.
            
    Returns
    -------
        symbols : set[str]
            A set of strings; one for each free variable in the expression.
    """
    try:
        symbols = {str(v) for v in sp.sympify(s).atoms(sp.Symbol)}
        symbols.discard(INDEPENDENT_VARIABLE)
        symbols.discard(PI)
        return symbols
    except (SyntaxError, ValueError):
        raise ImproperlyFormattedExpressionError(f"The expression '{s}' is not properly formatted.")
    except Exception as e:
        raise InvalidExpressionError(f'Expression invalid due to "{str(e)}".')


def is_accepted_expression(expression: str) -> bool:
    """ Checks if the provided expression is properly formatted and valid.

    PARAMETERS
    ----------
        expression : str
            The string form of the expression we are to check.

    RETURNS
    -------
        accepted : bool
            A boolean indicating if the expression is properly formatted and valid
    """
    try:
        parse(expression)
        return True
    except (ImproperlyFormattedExpressionError, InvalidExpressionError):
        return False


_UNSUPPORTED_UNICODE_CHARACTER_DICTIONARY = {
    PI: "pi",
    NAUGHT: '0'
}


def _replace_unsupported_unicode_characters(expression: str) -> str:
    f"""Replaces unsupported unicode characters with valid alternates. Meant for internal use only.
    
    There are some characters we include in beams for purely visual purposes (the unicode for pi or naught for
    example) and sometimes these will throw errors in sympy. So we need to replace them with alternate symbols.
    Note that {PI} would become 'pi' and {PI}2 would become 'pi2'. Currently this method is only applied immediately
    before and after lambdifying and in the call method of the fit expression so the user never sees an altered
    expression. That's also why this is a protected method, it shouldn't be called outside this module.
    
    PARAMETERS
    ----------
        expression : str
        
    RETURNS
    -------
        expression : str
            The expression with unsupported characters replaced.
    """
    for uc, c in _UNSUPPORTED_UNICODE_CHARACTER_DICTIONARY.items():
        expression = expression.replace(uc, c)
    return expression


def alpha_correction(expression):
    return f'((1-{ALPHA})+((1+{ALPHA})*({expression})))/((1+{ALPHA})+((1-{ALPHA})*({expression})))'


def lambdify(expression, variables):
    """ Takes a string representation of an expression and returns a callable lambda.

    PARAMETERS
    ----------
        expression: str
            The string representation of the expression

    RETURNS
    -------
        lambda_expression: lambda
            A callable lambda representation of the expression
    """
    expression_string = _replace_unsupported_unicode_characters(expression)

    variables = variables if variables is not None else parse(expression)
    var_names = [INDEPENDENT_VARIABLE]
    var_names.extend([_replace_unsupported_unicode_characters(var) for var in variables])

    lambda_expression = sp.lambdify(var_names, sp.sympify(expression_string), ["numpy", "scipy", "sympy"])
    return lambda_expression


def _shortened_run_id(run_id):
    return "_" + run_id.split('-')[0]


def _residual(lambda_expression):
    def residual(pars, x, y_data, dy_data):
        y_calc = lambda_expression(x, *pars)
        return (y_data - y_calc) / dy_data
    return residual


class ImproperlyFormattedExpressionError(Exception):
    """
    The expression is not properly formatted (e.g. 'x=3*y' or 'x*')
    """
    def __init__(self, *args):
        super(ImproperlyFormattedExpressionError, self).__init__(*args)


class InvalidExpressionError(Exception):
    """
    The expression is properly formatted but logically incorrect (e.g. a function that takes
    two args was only given one).
    """
    def __init__(self, *args):
        super(InvalidExpressionError, self).__init__(*args)
