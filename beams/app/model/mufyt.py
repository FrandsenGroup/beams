
import traceback

import sympy as sp
import numpy as np
from scipy.optimize import least_squares, curve_fit

DELTA = "\u0394"
LAMBDA = "\u03BB"
BETA = "\u03B2"
SIGMA = "\u03C3"
ALPHA = "\u03B1"
PHI = "\u03D5"
PI = "\u03C0"

SIMPLE_EXPONENTIAL = "f(t) = exp(-\u03BB*t)"
STRETCHED_EXPONENTIAL = "f(t) = exp(-(\u03BB*t)^\u03B2)"
SIMPLE_GAUSSIAN = "f(t) = exp(-1/2*(\u03C3*t)^2)"
GAUSSIAN_KT = "f(t) = 1/3 + 2/3*(1 - (\u03C3*t)^2)*exp(-1/2*(\u03C3*t)^2)"
LORENTZIAN_KT = "f(t) = 1/3 + 2/3*(1 - \u03BB*t)*exp(-\u03BB*t)"
COMBINED_KT = "f(t) = 1/3 + 2/3*(1-\u03C3^2*t^2-\u03BB*t)*exp(-\u03C3^2*t^2/2-\u03BB*t)"
STRETCHED_KT = "f(t) = 1/3 + 2/3(1-(\u03C3*t)^\u03B2)*exp(-(\u03C3*t)^\u03B2/\u03B2"
COSINE = "f(t) = cos(2*\u03C0*v*t + \u03C0*\u03D5/180)"
INTERNAL_COSINE = "f(t) = \u03B1*cos(2*\u03C0*v*t + \u03C0*\u03D5/180)*exp(-\u03BB*t) + (1-\u03B1)*exp(-\u03BB*t)"
BESSEL = "f(t) = j0*(2*\u03C0*v*t + \u03C0*\u03D5/180)"
INTERNAL_BESSEL = "f(t) = \u03B1*j0*(2*\u03C0*v*t + \u03C0*\u03D5/180)*exp(-\u03BB*t) + (1-\u03B1)*exp(-\u03BB*t)"

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


class Fit:
    def __init__(self):
        self.is_fitted = False
        self.fit_calculated = False  # If this is false then it will optimize again
        self.full_function = None
        self.independent_variable = None
        self.expression = None
        self.free_variables = None
        self.parameters = None
        self.cov = None
        self.include_alpha = True
        self.lambda_expression = None
        self.refine = True

    def __str__(self):
        return "Fit=[\n\tExpression={}\n\tIndependent={}\n\tVariables={}\n]".format(self.expression, self.independent_variable, self.free_variables)


def parse(s):
    """ Takes in an expression as a string and returns a set of the free variables. """

    # Add to these sets any keywords you want to be recognized as not variables.
    # Keep keywords lowercase, user input will be cast to lowercase for comparison.
    oper_set = ('+', '-', '/', '*', '(', ')', '[', ']', '{', '}', '^', '!')
    key_1_char_set = ('e', 'i', '\u03C0')
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

        if character.isspace() or character in oper_set:
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
            elif len(free_variable) == 0 and (s[i] in key_1_char_set or s[i].lower() in key_1_char_set) and (i == len(s) - 1 or s[i + 1] in oper_set or s[i + 1].isspace()):
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
                            traceback.print_exc()
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


def fit(expression, time, asymmetry, uncertainty, variables: dict, independent_variable):

    expression_string = ""

    for c in expression:
        if c == '\u03C0':
            expression_string += "pi"
        elif c == '^':
            expression_string += "**"
        else:
            expression_string += c

    return fit_least_squares(expression_string, time, asymmetry, uncertainty, variables, independent_variable)


def lambdify(expression, variables: dict, independent_variable):
    expression_string = ""

    for c in expression:
        if c == '\u03C0':
            expression_string += "pi"
        elif c == '^':
            expression_string += "**"
        else:
            expression_string += c

    var_names = [independent_variable]
    var_names.extend([var for var in variables.keys()])
    var_guesses = [float(data[0]) for data in variables.values()]

    lambda_expression = sp.lambdify(var_names, sp.sympify(expression), "numpy")

    return var_guesses, None, lambda_expression


def fit_least_squares(expression, time, asymmetry, uncertainty, variables: dict, independent_variable):

    # Since we divide by the uncertainty which has zeros I replace the occasional zero with the value before it.
    uncertainty = np.array([u if u != 0 else uncertainty[i-1] for i, u in enumerate(uncertainty)])

    def residual(parameters, t, a, u):
        calc = lambda_expression(*parameters, t)
        return (a - calc) / u

    var_names = [independent_variable]
    var_names.extend([var for var in variables.keys()])
    var_guesses = [float(data[0]) for data in variables.values()]
    var_lowers = [data[1] for data in variables.values()]
    var_uppers = [data[2] for data in variables.values()]

    for i, bound in enumerate(var_lowers):
        if bound.lower() == '-inf' or bound.lower() == '-infinity':
            var_lowers[i] = -np.inf
        else:
            var_lowers[i] = float(bound)

    for i, bound in enumerate(var_uppers):
        if bound.lower() == 'inf' or bound.lower() == 'infinity':
            var_uppers[i] = np.inf
        else:
            var_uppers[i] = float(bound)

    lambda_expression = sp.lambdify(var_names, sp.sympify(expression), "numpy")

    try:
        pars = least_squares(fun=residual, x0=var_guesses, bounds=(var_lowers, var_uppers), args=(time, asymmetry, uncertainty)).x
    except ValueError:
        return var_guesses, None, lambda_expression

    for p, k in zip(pars, variables.keys()):
        variables[k][0] = p

    return pars, None, lambda_expression


def fit_lm(expression, time, asymmetry, uncertainty, variables: dict, independent_variable):

    def error():
        pass

    var_names = [independent_variable]
    var_names.extend([var for var in variables.keys()])
    var_guesses = [float(data[0]) for data in variables.values()]
    var_lowers = [data[1] for data in variables.values()]
    var_uppers = [data[2] for data in variables.values()]

    for i, bound in enumerate(var_lowers):
        if bound.lower() == '-inf' or bound.lower() == '-infinity':
            var_lowers[i] = -np.inf
        else:
            var_lowers[i] = float(bound)

    for i, bound in enumerate(var_uppers):
        if bound.lower() == 'inf' or bound.lower() == 'infinity':
            var_uppers[i] = np.inf
        else:
            var_uppers[i] = float(bound)

    # print("Expression={}\nIndependent={}\nVariables={}\nGuesses={}\nLowers={}\nUppers={}".format(expression, independent_variable, var_names, var_guesses, var_lowers, var_uppers))

    lambda_expression = sp.lambdify(var_names, sp.sympify(expression), "numpy")

    pars, cov = curve_fit(f=lambda_expression, xdata=time, ydata=asymmetry, maxfev=10000,
                          bounds=(var_lowers, var_uppers), p0=var_guesses)

    # print("Fit={}\nCov={}\n".format(pars, cov))

    for p, k in zip(pars, variables.keys()):
        variables[k][0] = p

    return pars, cov, lambda_expression


# def func(x, a, b, c):
#     return a * np.exp(-b * x) + c

# xdata = np.linspace(0, 4, 50)
# y = func(xdata, 2.5, 1.3, 0.5)
# np.random.seed(1729)
# y_noise = 0.2 * np.random.normal(size=xdata.size)
# ydata = y + y_noise
# plt.plot(xdata, ydata, 'b-', label='data')
# popt, pcov = curve_fit(func, xdata, ydata)
#
# plt.plot(xdata, func(xdata, *popt), 'r-',
#     label='fit: a=%5.3f, b=%5.3f, c=%5.3f' % tuple(popt))
# popt, pcov = curve_fit(func, xdata, ydata, bounds=(0, [3., 1., 0.5]))
#
# plt.plot(xdata, func(xdata, *popt), 'g--',
#     label='fit: a=%5.3f, b=%5.3f, c=%5.3f' % tuple(popt))
# plt.xlabel('x')
# plt.ylabel('y')
# plt.legend()
# plt.show()

# ind, exp = split_expression(var_func)
# print("Function = {}\nIndependent Variable = {}\nExpression = {}\nFree Constants = {}".format(var_func, ind, exp, parse(exp)))