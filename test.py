import sympy as sp
import numpy as np
import importlib.util
import sys


if __name__ == '__main__':
    # print(lamb(4, 2))
    file = "testmodule.py"
    funcname = "func1"
    spec = importlib.util.spec_from_file_location(funcname, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[funcname] = module
    spec.loader.exec_module(module)
    exts = {funcname: getattr(module, funcname)}
    lamb = sp.lambdify(['t', 'omega'], sp.sympify('func1(t, omega)', evaluate=True, locals=exts), ["numpy"])
    print(lamb(4, 3))
