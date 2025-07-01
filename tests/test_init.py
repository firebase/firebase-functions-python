"""
Test the init decorator.
"""

import unittest

from firebase_functions import core


class TestInit(unittest.TestCase):
    """
    Test the init decorator.
    """

    def test_init_is_initialized(self):
        @core.init
        def fn():
            pass

        # pylint: disable=protected-access
        self.assertIsNotNone(core._init_callback)
        # pylint: disable=protected-access
        self.assertFalse(core._did_init)
