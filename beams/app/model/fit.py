
import sympy as sp
import numpy as np
from scipy.optimize import least_squares, curve_fit
import matplotlib.pyplot as plt


class Fit:
    def __init__(self):
        self.is_fitted = False

        self.fit_expression = None
        self.fit_variables = None
        self.fit = None


def parse(s):
    """ Takes in an expression as a string and returns a set of the free variables. """

    # Add to these sets any keywords you want to be recognized as not variables.
    # Keep keywords lowercase, user input will be cast to lowercase for comparison.
    oper_set = ('+', '-', '/', '*', '(', ')', '[', ']', '{', '}', '^', '!')
    key_1_char_set = ('e', 'i')
    key_2_char_set = ('pi')
    key_3_char_set = ('sin', 'cos', 'tan')
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
            elif s[i].lower() in key_1_char_set and (s[i + 1] in oper_set or s[i + 1].isspace()):
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


def fit(expression, time, asymmetry, uncertainty, variables):
    def residual(params, tArray, data, dataErr):
        calc = lambda_expression(*params, tArray)  # params unpacks the params list into individual pieces
        for i, n in enumerate(dataErr):
            if n == 0:
                dataErr[i] = 0.1
        return (data - calc) / dataErr**2

    var_func = "a0*cos(2*pi*f*t+phi)*2.718**(-lam*t)"
    variables = {'a0': 1, 'f': 1, 'phi': 1, 'lam': 1}
    var_list_1 = ['t']
    var_list_1.extend(list(variables.keys()))
    var_list_2 = list(variables.values())

    print('func = {}\nvar_list_1 = {}\nvar_list_2 = {}'.format(var_func, var_list_1, var_list_2))

    new_fit = Fit()
    lambda_expression = sp.lambdify(var_list_1, sp.sympify(var_func), "numpy")

    pars, cov = curve_fit(f=lambda_expression, xdata=time, ydata=asymmetry, maxfev=3000,
                          bounds=([0.5, 0.1, -30, 0], [1.5, 3, 30, 50]))

    print('curve fit = {}, {}'.format(pars, cov))

    new_fit.fit = lambda_expression(np.array(time), *pars)
    new_fit.fit_expression = lambda_expression
    new_fit.fit_variables = variables
    new_fit.is_fitted = True

    print(new_fit.fit)
    return new_fit


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


var_func = "AS(t) = a0*cos(2*pi*f*t+phi)*2.718**(-lam*t)"

ind, exp = split_expression(var_func)
print("Function = {}\nIndependent Variable = {}\nExpression = {}\nFree Constants = {}".format(var_func, ind, exp, parse(exp)))