import os
import socket
import sys
import unittest
import urllib.error
from unittest import mock

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "pc"))
from cases import load_cases  # noqa: E402
from nucleo import Failure, NetworkError, translate  # noqa: E402
import rede  # noqa: E402

CASES = load_cases("network_errors.json")


def failure(d):
    if d["type"] == "timeout":
        return NetworkError.timeout()
    if d["type"] == "no_connection":
        return NetworkError.no_connection()
    if d["type"] == "http":
        return NetworkError.http(d["code"])
    return NetworkError.other(d["detail"])


# the cases live in casos/network_errors.json and also apply to Android (NetworkErrorsTest.kt)
class MessagesTest(unittest.TestCase):
    def test_shared_cases(self):
        self.assertTrue(CASES)
        for case in CASES:
            with self.subTest(case=case["name"]):
                def fetch(_):
                    raise failure(case["failure"])
                self.assertEqual(Failure(case["expected"]), translate("x", fetch))

    def test_unknown_exception_becomes_other(self):
        def fetch(_):
            raise OSError("boom")
        self.assertEqual(Failure("boom"), translate("x", fetch))


class ConversionTest(unittest.TestCase):
    def kind(self, e):
        r = rede.convert_exception(e)
        self.assertIsInstance(r, NetworkError)
        return (r.kind, r.code, r.detail)

    def test_timeout(self):
        self.assertEqual(("timeout", None, None), self.kind(TimeoutError()))
        self.assertEqual(("timeout", None, None), self.kind(socket.timeout()))
        self.assertEqual(("timeout", None, None),
                         self.kind(urllib.error.URLError(TimeoutError())))

    def test_no_connection(self):
        for e in (urllib.error.URLError(socket.gaierror(-2, "Name or service not known")),
                  urllib.error.URLError(ConnectionRefusedError(111, "refused")),
                  urllib.error.URLError(OSError(101, "Network is unreachable")),
                  urllib.error.URLError(OSError(113, "No route to host")),
                  ConnectionResetError()):
            with self.subTest(e=e):
                self.assertEqual(("no_connection", None, None), self.kind(e))

    def test_http(self):
        e = urllib.error.HTTPError("u", 503, "x", {}, None)
        self.assertEqual(("http", 503, None), self.kind(e))

    def test_rest_becomes_other_with_detail(self):
        self.assertEqual(("other", None, "boom"), self.kind(ValueError("boom")))
        self.assertEqual(("other", None, "ValueError"), self.kind(ValueError()))

    def test_fetch_converts_urllib_exceptions(self):
        error = urllib.error.URLError(socket.gaierror(-2, "x"))
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(NetworkError) as c:
                rede.fetch("http://x")
        self.assertEqual("no_connection", c.exception.kind)

    def test_non_200_status_becomes_http(self):
        r = mock.MagicMock()
        r.__enter__.return_value = r
        r.status = 204
        with mock.patch("urllib.request.urlopen", return_value=r):
            with self.assertRaises(NetworkError) as c:
                rede.fetch("http://x")
        self.assertEqual(("http", 204), (c.exception.kind, c.exception.code))


if __name__ == "__main__":
    unittest.main()
