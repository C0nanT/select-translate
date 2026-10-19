import json
import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "pc"))
from cases import load_cases  # noqa: E402
from nucleo import (Empty, NoLetters, TooLarge, Translation,  # noqa: E402
                    translate, validate)

CASES = load_cases("validation.json")

BASE = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=pt&dt=t&q="


def response(*parts):
    return json.dumps([[[p, "x"] for p in parts], None, "en"])


# the cases live in casos/validation.json and also apply to Android (TranslatorTest.kt)
class ValidationTest(unittest.TestCase):
    def test_shared_cases(self):
        self.assertTrue(CASES)
        for case in CASES:
            with self.subTest(case=case["name"]):
                urls = []

                def fetch(url):
                    urls.append(url)
                    return response("ok")

                times = case.get("times", 1)
                r = translate(case["input"] * times, fetch)
                exp = case["expected"]
                if exp["type"] == "ok":
                    self.assertEqual(Translation("ok"), r)
                    self.assertEqual([BASE + exp["q"] * times], urls)
                    continue
                self.assertEqual([], urls, "must not call fetch")
                if exp["type"] == "too_large":
                    self.assertEqual(TooLarge(exp["n"]), r)
                else:
                    self.assertIs({"empty": Empty, "no_letters": NoLetters}[exp["type"]], r)


class ResultsTest(unittest.TestCase):
    def test_too_large_message(self):
        self.assertEqual("Texto grande demais (3001 caracteres)", TooLarge(3001).message)

    def test_validate_does_not_hit_network_and_returns_none_if_ok(self):
        self.assertIs(Empty, validate("  "))
        self.assertIs(NoLetters, validate("42"))
        self.assertEqual(TooLarge(3001), validate("a" * 3001))
        self.assertIsNone(validate("hello"))


if __name__ == "__main__":
    unittest.main()
