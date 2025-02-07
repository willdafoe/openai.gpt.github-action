import unittest
from src import self_healing

class TestSelfHealing(unittest.TestCase):

    def test_debug_mode(self):
        self.assertTrue(self_healing.DEBUG_ONLY)

if __name__ == "__main__":
    unittest.main()
