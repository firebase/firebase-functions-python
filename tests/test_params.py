"""Param unit tests."""
from os import environ

import pytest
from firebase_functions import params


class TestBoolParams:
    """BoolParam unit tests."""

    def test_bool_param_value_true_or_false(self):
        """Testing if bool params correctly returns a true or false value."""
        for value_true, value_false in zip(["true", "t", "1", "y", "yes"],
                                           ["false", "f", "0", "n", "no"]):
            environ["bool_value_test"] = value_true
            assert (params.BoolParam("bool_value_test").value() is
                    True), "Failure, params returned False"
            environ["bool_value_test"] = value_false
            assert (params.BoolParam("bool_value_test").value() is
                    False), "Failure, params returned True"

    def test_bool_param_value_error(self):
        """Testing if bool params throws a value error if invalid value."""
        with pytest.raises(ValueError):
            environ["bool_value_test"] = "bad_value"
            params.BoolParam("bool_value_test").value()

    def test_bool_param_empty_default(self):
        """Testing if bool params defaults to False if no value and no default."""
        assert (params.BoolParam("bool_default_test").value() is
                False), "Failure, params returned True"

    def test_bool_param_default(self):
        """Testing if bool params defaults to provided default value."""
        assert (params.BoolParam("bool_default_test", default=False).value() is
                False), "Failure, params returned True"
        assert (params.BoolParam("bool_default_test", default=True).value() is
                True), "Failure, params returned False"

    def test_bool_param_equality(self):
        """Test bool equality."""
        assert (params.BoolParam("bool_test",
                                 default=False).equals(False).value() is
                True), "Failure, equality check returned False"
        assert (params.BoolParam("bool_test",
                                 default=True).equals(False).value() is
                False), "Failure, equality check returned False"


class TestFloatParams:
    """FloatParam unit tests."""

    def test_float_param_value(self):
        """Testing if float params correctly returns a value."""
        environ["float_value_test"] = "123.456"
        assert params.FloatParam("float_value_test",).value() == 123.456, \
            "Failure, params value != 123.456"

    def test_float_param_empty_default(self):
        """Testing if float params defaults to empty float if no value and no default."""
        assert params.FloatParam("float_default_test").value() == float(), \
            "Failure, params value is not float"

    def test_float_param_default(self):
        """Testing if float param defaults to provided default value."""
        assert params.FloatParam("float_default_test", default=float(456.789)).value() == 456.789, \
            "Failure, params default value != 456.789"

    def test_float_param_equality(self):
        """Test float equality."""
        assert (params.FloatParam("float_test",
                                  default=123.456).equals(123.456).value() is
                True), "Failure, equality check returned False"
        assert (params.FloatParam("float_test",
                                  default=456.789).equals(123.456).value() is
                False), "Failure, equality check returned False"


class TestIntParams:
    """IntParam unit tests."""

    def test_int_param_value(self):
        """Testing if int param correctly returns a value."""
        environ["int_value_test"] = "123"
        assert params.IntParam(
            "int_value_test").value() == 123, "Failure, params value != 123"

    def test_int_param_empty_default(self):
        """Testing if int param defaults to empty int if no value and no default."""
        assert params.IntParam("int_default_test").value() == int(
        ), "Failure, params value is not int"

    def test_int_param_default(self):
        """Testing if int param defaults to provided default value."""
        assert params.IntParam("int_default_test", default=456).value() == 456, \
            "Failure, params default value != 456"

    def test_int_param_equality(self):
        """Test int equality."""
        assert (params.IntParam("int_test", default=123).equals(123).value() is
                True), "Failure, equality check returned False"
        assert (params.IntParam("int_test", default=456).equals(123).value() is
                False), "Failure, equality check returned False"


class TestStringParams:
    """StringParam unit tests."""

    def test_string_param_value(self):
        """Testing if string param correctly returns a value."""
        environ["string_value_test"] = "string_test"
        assert params.StringParam("string_value_test").value() == "string_test", \
            'Failure, params value != "string_test"'

    def test_string_param_empty_default(self):
        """Testing if string param defaults to empty string if no value and no default."""
        assert params.StringParam("string_default_test").value() == str(), \
            "Failure, params value is not a string"

    def test_string_param_default(self):
        """Testing if string param defaults to provided default value."""
        assert (params.StringParam("string_default_test", default="string_override_default").value()
                == "string_override_default"), \
            'Failure, params default value != "string_override_default"'

    def test_string_param_equality(self):
        """Test string equality."""
        assert (params.StringParam("string_test",
                                   default="123").equals("123").value() is
                True), "Failure, equality check returned False"
        assert (params.StringParam("string_test",
                                   default="456").equals("123").value() is
                False), "Failure, equality check returned False"


class TestListParams:
    """ListParam unit tests."""

    def test_list_param_value(self):
        """Testing if list param correctly returns list values."""
        environ["list_value_test"] = "item1,item2"
        assert params.ListParam("list_value_test").value() == ["item1","item2"], \
            'Failure, params value != ["item1","item2"]'

    def test_list_param_filter_empty_strings(self):
        """Testing if list param correctly returns list values wth empty strings excluded."""
        environ["list_value_test"] = ",,item1,item2,,,item3,"
        assert params.ListParam("list_value_test").value() == ["item1","item2", "item3"], \
            'Failure, params value != ["item1","item2", "item3"]'

    def test_list_param_empty_default(self):
        """Testing if list param defaults to an empty list if no value and no default."""
        assert params.ListParam("list_default_test").value() == [], \
            "Failure, params value is not an empty list"

    def test_list_param_default(self):
        """Testing if list param defaults to the provided default value."""
        assert (params.ListParam("list_default_test", default=["1", "2"]).value()
                == ["1", "2"]), \
            'Failure, params default value != ["1", "2"]'

    def test_list_param_equality(self):
        """Test list equality."""
        assert (params.ListParam("list_test", default=["123"]).equals(
            ["123"]).value() is True), "Failure, equality check returned False"
        assert (params.ListParam("list_test", default=["456"]).equals(
            ["123"]).value() is False), "Failure, equality check returned False"
