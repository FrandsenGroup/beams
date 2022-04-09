import pytest

import numpy as np

from app.model import fit


class TestHelperMethods:
    @pytest.mark.parametrize("expression, expected_variables",
                             [
                                 ('x', {'x'}),
                                 ('x+1', {'x'}),
                                 (f'x*{fit.INDEPENDENT_VARIABLE}', {'x'}),
                                 ('x*y', {'x', 'y'}),
                                 (f'x*sin(y*{fit.INDEPENDENT_VARIABLE})', {'x', 'y'}),
                                 ('jn(0,x*x*y*y-3)', {'x', 'y'}),  # known function
                                 ('jklol(x)*3', {'x'}),  # unknown function
                                 ('exp(I*x)', {'x'}),
                                 (f'I*pi*{fit.INDEPENDENT_VARIABLE}', set())
                             ])
    def test_parse_valid(self, expression, expected_variables):
        parsed_variables = fit.parse(expression)
        assert parsed_variables == expected_variables

    @pytest.mark.parametrize("expression, error",
                             [
                                 ('jn(x)', fit.InvalidExpressionError),  # jn is a known function that has two args
                                 ('x=3+y', fit.ImproperlyFormattedExpressionError),
                                 ('x*', fit.ImproperlyFormattedExpressionError)
                             ])
    def test_parse_invalid(self, expression, error):
        with pytest.raises(error):
            fit.parse(expression)

    @pytest.mark.parametrize("expression, expected",
                             [
                                 ('x', True),
                                 ('x+1', True),
                                 (f'x*{fit.INDEPENDENT_VARIABLE}', True),
                                 ('x*y', True),
                                 (f'x*sin(y*{fit.INDEPENDENT_VARIABLE})', True),
                                 ('jn(0,x*x*y*y-3)', True),
                                 ('jklol(x)*3', True),
                                 ('exp(I*x)', True),
                                 (f'I*pi*{fit.INDEPENDENT_VARIABLE}', True),
                                 ('jn(x)', False),
                                 ('x=3+y', False),
                                 ('x*', False)
                             ])
    def test_accepted_expression(self, expression, expected):
        # Yep, this is essentially identical to tests for parse and is in fact implemented with parse BUT
        # that could always change, right? ;)
        assert fit.is_accepted_expression(expression) == expected

    @pytest.mark.parametrize("expression, expected_expression",
                             [
                                 ("x*t/sin(x+3)", "x*t/sin(x+3)"),
                                 (f"{fit.LAMBDA}*t/sin({fit.BETA}+3)", f"{fit.LAMBDA}*t/sin({fit.BETA}+3)"),
                                 (f"{fit.PI}*t/sin({fit.BETA}+3)", f"pi*t/sin({fit.BETA}+3)"),
                                 (f"{fit.PI}lfer*t/sin({fit.BETA}+3)", f"pilfer*t/sin({fit.BETA}+3)"),
                                 (f"j{fit.NAUGHT}*t/sin({fit.BETA}+3)", f"j0*t/sin({fit.BETA}+3)")
                             ])
    def test_replace_unsupported_unicode_characters(self, expression, expected_expression):
        assert fit._replace_unsupported_unicode_characters(expression) == expected_expression

    def test_alpha_correct_parse(self):
        parsed_variables = fit.parse(fit.alpha_correction('x'))
        assert parsed_variables == {fit.ALPHA, 'x'}

    def test_alpha_correct_exact(self):
        assert fit.alpha_correction('x+1') == '((1-\u03B1)+((1+\u03B1)*(x+1)))/((1+\u03B1)+((1-\u03B1)*(x+1)))'

    @pytest.mark.parametrize("expression, variables, args, kwargs, result",
                             [
                                 ("x", ["x"], [1], {}, 1),
                                 ("sin(pi*y)", None, [1], {}, 0),
                                 ("jn(0, x)", ['x'], [np.pi], {}, 0),
                                 ("2*t", [], [np.array([1, 2, 3, 4])], {}, [2, 4, 6, 8]),
                                 ("x+t*y", None, [np.array([1, 2, 3, 4]), 2, 3], {}, [5, 8, 11, 14]),
                                 ("x+t*y", None, [np.array([1, 2, 3, 4])], {'x': 2, 'y': 3}, [5, 8, 11, 14]),
                                 ("x+t*y", ['x', 'y'], [np.array([1, 2, 3, 4])], {'x': 2, 'y': 3}, [5, 8, 11, 14])
                             ])
    def test_lambdify(self, expression, variables, args, kwargs, result):
        calculated_result = fit.lambdify(expression, variables)(*args, **kwargs)

        if isinstance(calculated_result, np.ndarray):
            assert np.array_equal(calculated_result, result)
        else:
            assert abs(float(calculated_result) - result) < 0.000001


class TestPreDefinedEquations:
    @pytest.mark.parametrize("expression, expected_variables",
                             list((f, set(fit.DEFAULT_VALUES[n].keys())) for n, f in fit.EQUATION_DICTIONARY.items()))
    def test_equation_valid(self, expression, expected_variables):
        parsed_variables = fit.parse(expression)
        assert parsed_variables == expected_variables



