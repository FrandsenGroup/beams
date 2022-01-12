import pytest


# @pytest.mark.one
# def test_method_one():
#     x = 5
#     y = 10
#     assert x == y
#
#
# @pytest.mark.two
# def test_method_two():
#     a = 15
#     b = 20
#     assert a + b == 35


# class TestClass:
#     def test_one(self):
#         assert 2 == 2
#
#     def test_two(self):
#         assert 2 == 3

# @pytest.fixture
# def useful_numbers():
#     return [1, 1, 2, 3, 5]
#
#
# @pytest.fixture
# def numbers(useful_numbers):
#     a = 10
#     b = 20
#     c = 30
#     x = [a, b, c]
#     x.extend(useful_numbers)
#     return x
#
#
# def test_method_one(numbers):
#     numbers[1] = 50
#     assert numbers[5] == 10
#
#
# def test_method_two(numbers):
#     assert numbers[1] == 20
#
#
# def test_method_three(numbers):
#     assert numbers[1] == 20


@pytest.mark.parametrize("x, y, z", [(1, 2, 3), (4, 5, 6)])
def test_method_one(x, y, z):
    assert x == x


