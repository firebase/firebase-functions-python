"""
Logger module tests.
"""

import pytest
import json
from firebase_functions import logger


class TestLogger:
    """
    Tests for the logger module.
    """

    def test_format_should_be_valid_json(self,
                                         capsys: pytest.CaptureFixture[str]):
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

    def test_severity_should_be_notice(self,
                                       capsys: pytest.CaptureFixture[str]):
        logger.log(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert log_output["severity"] == "NOTICE"

    def test_severity_should_be_info(self, capsys: pytest.CaptureFixture[str]):
        logger.info(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert log_output["severity"] == "INFO"

    def test_severity_should_be_warning(self,
                                        capsys: pytest.CaptureFixture[str]):
        logger.warn(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert log_output["severity"] == "WARNING"

    def test_severity_should_be_error(self, capsys: pytest.CaptureFixture[str]):
        logger.error(foo="bar")
        raw_log_output = capsys.readouterr().err
        log_output = json.loads(raw_log_output)
        assert log_output["severity"] == "ERROR"

    def test_log_should_have_message(self, capsys: pytest.CaptureFixture[str]):
        logger.log("bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert "message" in log_output

    def test_log_should_have_other_keys(self,
                                        capsys: pytest.CaptureFixture[str]):
        logger.log(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert "foo" in log_output

    def test_message_should_be_space_separated(
            self, capsys: pytest.CaptureFixture[str]):
        logger.log("bar", "qux")
        expected_message = "bar qux"
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert log_output["message"] == expected_message
