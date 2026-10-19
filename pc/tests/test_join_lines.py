import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "pc"))
from cases import load_cases  # noqa: E402
from nucleo import join_lines  # noqa: E402

CASES = load_cases("join_lines.json")


# the cases live in casos/join_lines.json and also apply to Android (TranslatorTest.kt)
class JoinLinesTest(unittest.TestCase):
    def test_shared_cases(self):
        self.assertTrue(CASES)
        for case in CASES:
            with self.subTest(case=case["name"]):
                self.assertEqual(case["expected"], join_lines(case["input"]),
                                 "broken case: " + case["name"])


if __name__ == "__main__":
    unittest.main()
