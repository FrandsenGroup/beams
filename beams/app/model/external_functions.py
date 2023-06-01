import importlib.util
import inspect
import sys

from app.model.files import BeamsFileReadError


class ExternalModule:
    @staticmethod
    def get_external_function_invocation(filename, full_file_path):
        spec = importlib.util.spec_from_file_location(filename, full_file_path)
        module = importlib.util.module_from_spec(spec)
        try:
            sys.modules[filename] = module
            spec.loader.exec_module(module)
            func = getattr(module, filename)
        except (KeyError, AttributeError) as e:
            raise BeamsFileReadError("Filename must match the name of a function in the file.")
        except SyntaxError:
            raise BeamsFileReadError("Invalid python file; syntax error found")
        sig = inspect.signature(func)
        return filename + str(sig)

    @staticmethod
    def load_external_function(full_file_path, filename):
        spec = importlib.util.spec_from_file_location(filename, full_file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[filename] = module
        spec.loader.exec_module(module)
        return getattr(module, filename)

    @staticmethod
    def load_external_functions(external_function_dict):
        loaded_external_functions = {}
        for filename, full_file_path in external_function_dict.items():
            spec = importlib.util.spec_from_file_location(filename, full_file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[filename] = module
            spec.loader.exec_module(module)
            func = getattr(module, filename)
            loaded_external_functions[filename] = func
        return loaded_external_functions

    @staticmethod
    def is_external_function(function, external_function_dict):
        return function.split('(')[0] in external_function_dict.keys()
