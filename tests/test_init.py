import unittest
from firebase_functions import core


class TestInit(unittest.TestCase):
    def test_init_is_initialized(self):
        @core.init
        def fn():
            pass

        self.assertIsNotNone(core._initCallback)
        self.assertFalse(core._didInit)
