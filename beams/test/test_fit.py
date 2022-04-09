import pytest

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


class TestPreDefinedEquations:
    @pytest.mark.parametrize("expression, expected_variables",
                             list((f, set(fit.DEFAULT_VALUES[n].keys())) for n, f in fit.EQUATION_DICTIONARY.items()))
    def test_equation_valid(self, expression, expected_variables):
        parsed_variables = fit.parse(expression)
        assert parsed_variables == expected_variables

    def test_alpha_correct(self):
        parsed_variables = fit.parse(fit.ALPHA_CORRECTION)
        assert parsed_variables == {fit.ALPHA}

