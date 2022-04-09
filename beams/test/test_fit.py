import pytest

from app.model import fit


class TestParse:
    @pytest.mark.parametrize("expression, expected_variables",
                             [
                                 ('x', {'x'}),
                                 ('x+1', {'x'}),
                                 ('x*t', {'x'}),
                                 ('x*y', {'x', 'y'}),
                                 ('x*sin(y*t)', {'x', 'y'}),
                                 ('jn(0,t*t*x*x*y*y-3)', {'x', 'y'}),  # known function
                                 ('jklol(x)*3', {'x'}),  # unknown function
                                 ('exp(I*x)', {'x'}),
                                 ('I*pi*t', set())
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
