# mypy: ignore-errors
"""
Logger module tests.
"""

import json

import pytest

from firebase_functions import logger


class TestLogger:
    """
    Tests for the logger module.
    """

    def test_format_should_be_valid_json(self, capsys: pytest.CaptureFixture[str]):
        logger.log(foo="bar")
        raw_log_output = capsys.readouterr().out
        try:
            json.loads(raw_log_output)
        except json.JSONDecodeError:
            pytest.fail("Log output was not valid JSON.")

    def test_log_should_have_severity(self, capsys: pytest.CaptureFixture[str]):
        logger.log(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert "severity" in log_output

    def test_severity_should_be_debug(self, capsys: pytest.CaptureFixture[str]):
        logger.debug(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert log_output["severity"] == "DEBUG"

    def test_severity_should_be_notice(self, capsys: pytest.CaptureFixture[str]):
        logger.log(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert log_output["severity"] == "NOTICE"

    def test_severity_should_be_info(self, capsys: pytest.CaptureFixture[str]):
        logger.info(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert log_output["severity"] == "INFO"

    def test_severity_should_be_warning(self, capsys: pytest.CaptureFixture[str]):
        logger.warn(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert log_output["severity"] == "WARNING"

    def test_severity_should_be_error(self, capsys: pytest.CaptureFixture[str]):
        logger.error(foo="bar")
        raw_log_output = capsys.readouterr().err
        log_output = json.loads(raw_log_output)
        assert log_output["severity"] == "ERROR"

    def test_error_should_accept_exception(self, capsys: pytest.CaptureFixture[str]):
        try:
            raise ValueError("boom")
        except ValueError as exception:
            logger.error("failed", error=exception)

        raw_log_output = capsys.readouterr().err
        log_output = json.loads(raw_log_output)

        assert log_output["severity"] == "ERROR"
        assert log_output["message"] == "failed"
        assert log_output["error"]["type"] == "ValueError"
        assert log_output["error"]["message"] == "boom"
        assert "stack_trace" in log_output["error"]
        assert "ValueError: boom" in log_output["error"]["stack_trace"]

    def test_error_should_accept_self_referential_exception(
        self, capsys: pytest.CaptureFixture[str]
    ):
        class SelfArgError(Exception):
            pass

        exception = SelfArgError("boom")
        exception.args = (exception,)

        logger.error("failed", error=exception)

        raw_log_output = capsys.readouterr().err
        log_output = json.loads(raw_log_output)

        assert log_output["severity"] == "ERROR"
        assert log_output["message"] == "failed"
        assert log_output["error"]["type"] == "SelfArgError"
        assert log_output["error"]["args"] == ["[CIRCULAR]"]

    def test_error_should_accept_exception_with_cyclic_payload(
        self, capsys: pytest.CaptureFixture[str]
    ):
        payload = {}
        payload["self"] = payload
        exception = ValueError(payload)

        logger.error("failed", error=exception)

        raw_log_output = capsys.readouterr().err
        log_output = json.loads(raw_log_output)

        assert log_output["severity"] == "ERROR"
        assert log_output["message"] == "failed"
        assert log_output["error"]["type"] == "ValueError"
        assert log_output["error"]["args"] == [{"self": "[CIRCULAR]"}]

    def test_log_should_have_message(self, capsys: pytest.CaptureFixture[str]):
        logger.log("bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert "message" in log_output

    def test_log_should_have_other_keys(self, capsys: pytest.CaptureFixture[str]):
        logger.log(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert "foo" in log_output

    def test_message_should_be_space_separated(self, capsys: pytest.CaptureFixture[str]):
        logger.log("bar", "qux")
        expected_message = "bar qux"
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert log_output["message"] == expected_message

    def test_exception_should_include_stack_trace(self, capsys: pytest.CaptureFixture[str]):
        try:
            raise ValueError("boom")
        except ValueError:
            logger.exception("failed")

        raw_log_output = capsys.readouterr().err
        log_output = json.loads(raw_log_output)

        assert log_output["severity"] == "ERROR"
        assert log_output["message"] == "failed"
        assert "stack_trace" in log_output
        assert "ValueError: boom" in log_output["stack_trace"]

    def test_remove_circular_references(self, capsys: pytest.CaptureFixture[str]):
        # Create an object with a circular reference.
        circ = {"b": "foo"}
        circ["circ"] = circ

        entry = {
            "severity": "ERROR",
            "message": "testing circular",
            "circ": circ,
        }
        logger.write(entry)
        raw_log_output = capsys.readouterr().err
        log_output = json.loads(raw_log_output)

        expected = {
            "severity": "ERROR",
            "message": "testing circular",
            "circ": {"b": "foo", "circ": "[CIRCULAR]"},
        }
        assert log_output == expected

    def test_remove_circular_references_in_arrays(self, capsys: pytest.CaptureFixture[str]):
        # Create an object with a circular reference inside an array.
        circ = {"b": "foo"}
        circ["circ"] = [circ]

        entry = {
            "severity": "ERROR",
            "message": "testing circular",
            "circ": circ,
        }
        logger.write(entry)
        raw_log_output = capsys.readouterr().err
        log_output = json.loads(raw_log_output)

        expected = {
            "severity": "ERROR",
            "message": "testing circular",
            "circ": {"b": "foo", "circ": ["[CIRCULAR]"]},
        }
        assert log_output == expected

    def test_no_false_circular_for_duplicates(self, capsys: pytest.CaptureFixture[str]):
        # Ensure that duplicate objects (used in multiple keys) are not marked as circular.
        obj = {"a": "foo"}
        entry = {
            "severity": "ERROR",
            "message": "testing circular",
            "a": obj,
            "b": obj,
        }
        logger.write(entry)
        raw_log_output = capsys.readouterr().err
        log_output = json.loads(raw_log_output)

        expected = {
            "severity": "ERROR",
            "message": "testing circular",
            "a": {"a": "foo"},
            "b": {"a": "foo"},
        }
        assert log_output == expected

    def test_no_false_circular_in_array_duplicates(self, capsys: pytest.CaptureFixture[str]):
        # Ensure that duplicate objects in arrays are not falsely detected as circular.
        obj = {"a": "foo"}
        arr = [
            {"a": obj, "b": obj},
            {"a": obj, "b": obj},
        ]
        entry = {
            "severity": "ERROR",
            "message": "testing circular",
            "a": arr,
            "b": arr,
        }
        logger.write(entry)
        raw_log_output = capsys.readouterr().err
        log_output = json.loads(raw_log_output)

        expected = {
            "severity": "ERROR",
            "message": "testing circular",
            "a": [
                {"a": {"a": "foo"}, "b": {"a": "foo"}},
                {"a": {"a": "foo"}, "b": {"a": "foo"}},
            ],
            "b": [
                {"a": {"a": "foo"}, "b": {"a": "foo"}},
                {"a": {"a": "foo"}, "b": {"a": "foo"}},
            ],
        }
        assert log_output == expected
