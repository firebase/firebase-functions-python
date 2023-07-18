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

    def test_log_should_have_message(self, capsys: pytest.CaptureFixture[str]):
        logger.log(foo="bar")
        raw_log_output = capsys.readouterr().out
        log_output = json.loads(raw_log_output)
        assert "message" in log_output
