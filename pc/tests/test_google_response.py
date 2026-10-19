import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "pc"))
from cases import load_cases  # noqa: E402
from nucleo import Failure, Translation, translate  # noqa: E402

CASES = load_cases("google_response.json")


# the cases live in casos/google_response.json and also apply to Android (GoogleResponseTest.kt)
class GoogleResponseTest(unittest.TestCase):
    def test_shared_cases(self):
        self.assertTrue(CASES)
        for case in CASES:
            with self.subTest(case=case["name"]):
                exp = case["expected"]
                r = translate("x", lambda _: case["body"])
                if exp["type"] == "translation":
                    self.assertEqual(Translation(exp["text"]), r)
                else:
                    self.assertEqual(Failure(exp["reason"]), r)


if __name__ == "__main__":
    unittest.main()
