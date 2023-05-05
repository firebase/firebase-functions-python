# Copyright 2022 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Param unit tests."""
from os import environ

import pytest
from firebase_functions import params


class TestBoolParams:
    """BoolParam unit tests."""

    def test_bool_param_value_true_or_false(self):
        """Testing if bool params correctly returns a true or false value."""
        bool_param = params.BoolParam("BOOL_VALUE_TEST1")
        for value_true, value_false in zip(["true"],
                                           ["false", "anything", "else"]):
            environ["BOOL_VALUE_TEST1"] = value_true
            assert (bool_param.value is True), "Failure, params returned False"
            environ["BOOL_VALUE_TEST1"] = value_false
            assert (bool_param.value is False), "Failure, params returned True"

    def test_bool_param_empty_default(self):
        """Testing if bool params defaults to False if no value and no default."""
        assert (params.BoolParam("BOOL_DEFAULT_TEST").value
                is False), "Failure, params returned True"

    def test_bool_param_default(self):
        """Testing if bool params defaults to provided default value."""
        assert (params.BoolParam("BOOL_DEFAULT_TEST_FALSE", default=False).value
                is False), "Failure, params returned True"
        assert (params.BoolParam("BOOL_DEFAULT_TEST_TRUE", default=True).value
                is True), "Failure, params returned False"

    def test_bool_param_equality(self):
        """Test bool equality."""
        assert (params.BoolParam("BOOL_TEST1",
                                 default=False).equals(False).value
                is True), "Failure, equality check returned False"
        assert (params.BoolParam("BOOL_TEST2", default=True).equals(False).value
                is False), "Failure, equality check returned False"


class TestFloatParams:
    """FloatParam unit tests."""

    def test_float_param_value(self):
        """Testing if float params correctly returns a value."""
        environ["FLOAT_VALUE_TEST"] = "123.456"
        assert params.FloatParam("FLOAT_VALUE_TEST",).value == 123.456, \
            "Failure, params value != 123.456"

    def test_float_param_empty_default(self):
        """Testing if float params defaults to empty float if no value and no default."""
        assert params.FloatParam("FLOAT_DEFAULT_TEST1").value == float(), \
            "Failure, params value is not float"

    def test_float_param_default(self):
        """Testing if float param defaults to provided default value."""
        assert params.FloatParam("FLOAT_DEFAULT_TEST2",
        default=float(456.789)).value == 456.789, \
            "Failure, params default value != 456.789"

    def test_float_param_equality(self):
        """Test float equality."""
        assert (params.FloatParam("FLOAT_TEST1",
                                  default=123.456).equals(123.456).value
                is True), "Failure, equality check returned False"
        assert (params.FloatParam("FLOAT_TEST2",
                                  default=456.789).equals(123.456).value
                is False), "Failure, equality check returned False"


class TestIntParams:
    """IntParam unit tests."""

    def test_int_param_value(self):
        """Testing if int param correctly returns a value."""
        environ["INT_VALUE_TEST"] = "123"
        assert params.IntParam(
            "INT_VALUE_TEST").value == 123, "Failure, params value != 123"

    def test_int_param_empty_default(self):
        """Testing if int param defaults to empty int if no value and no default."""
        assert params.IntParam("INT_DEFAULT_TEST1").value == int(
        ), "Failure, params value is not int"

    def test_int_param_default(self):
        """Testing if int param defaults to provided default value."""
        assert params.IntParam("INT_DEFAULT_TEST2", default=456).value == 456, \
            "Failure, params default value != 456"

    def test_int_param_equality(self):
        """Test int equality."""
        assert (params.IntParam("INT_TEST1", default=123).equals(123).value
                is True), "Failure, equality check returned False"
        assert (params.IntParam("INT_TEST2", default=456).equals(123).value
                is False), "Failure, equality check returned False"


class TestStringParams:
    """StringParam unit tests."""

    def test_string_param_value(self):
        """Testing if string param correctly returns a value."""
        environ["STRING_VALUE_TEST"] = "STRING_TEST"
        assert params.StringParam("STRING_VALUE_TEST").value == "STRING_TEST", \
            'Failure, params value != "STRING_TEST"'

    def test_param_name_upper_snake_case(self):
        """Testing if param names are validated to be upper snake case."""
        with pytest.raises(ValueError) as context:
            params.StringParam("lower")
        assert "UPPER_SNAKE_CASE" in str(context)

    def test_string_param_empty_default(self):
        """Testing if string param defaults to empty string if no value and no default."""
        assert params.StringParam("STRING_DEFAULT_TEST1").value == str(), \
            "Failure, params value is not a string"

    def test_string_param_default(self):
        """Testing if string param defaults to provided default value."""
        assert (params.StringParam("STRING_DEFAULT_TEST2",
        default="string_override_default").value
                == "string_override_default"), \
            'Failure, params default value != "string_override_default"'

    def test_string_param_equality(self):
        """Test string equality."""
        assert (params.StringParam("STRING_TEST1",
                                   default="123").equals("123").value
                is True), "Failure, equality check returned False"
        assert (params.StringParam("STRING_TEST2",
                                   default="456").equals("123").value
                is False), "Failure, equality check returned False"


class TestParamsManifest:
    """
    Tests any created params are tracked for the purposes
    of outputting to the generated manifest.
    """

    def test_params_stored(self):
        """Testing if params are internally stored."""
        environ["TEST_STORING"] = "TEST_STORING_VALUE"
        param = params.StringParam("TEST_STORING")
        assert param.value == "TEST_STORING_VALUE", \
            'Failure, params value != "TEST_STORING_VALUE"'
        # pylint: disable=protected-access
        assert params._params["TEST_STORING"] == param, \
            "Failure, param was not stored"

    def test_default_params_not_stored(self):
        """Testing if default params are skipped from being stored."""
        environ["GCLOUD_PROJECT"] = "python-testing-project"

        assert params.PROJECT_ID.value == "python-testing-project", \
            'Failure, params value != "python-testing-project"'
        # pylint: disable=protected-access
        assert params._params.get("GCLOUD_PROJECT") is None, \
            "Failure, default param was stored when it should not have been"
