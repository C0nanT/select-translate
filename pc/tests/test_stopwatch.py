import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core import Stopwatch  # noqa: E402


# mirrors android/.../StopwatchTest.kt
class StopwatchTest(unittest.TestCase):
    def test_counts_down_to_zero(self):
        s = Stopwatch(15_000)
        s.start(1_000)
        self.assertEqual(10_000, s.elapse(6_000))
        self.assertFalse(s.finished)
        self.assertEqual(0, s.elapse(16_000))
        self.assertTrue(s.finished)

    def test_pause_and_resume_neither_lose_nor_gain_time(self):
        s = Stopwatch(15_000)
        s.start(0)
        s.pause(4_000)
        self.assertEqual(11_000, s.elapse(60_000))
        s.resume(60_000)
        self.assertEqual(8_000, s.elapse(63_000))

    def test_restart_while_paused_does_not_run(self):
        s = Stopwatch(15_000)
        s.start(0)
        s.pause(2_000)
        s.start(5_000)
        self.assertEqual(15_000, s.elapse(50_000))
        self.assertEqual(1.0, s.fraction)
        s.resume(50_000)
        self.assertEqual(14_000, s.elapse(51_000))

    def test_idle_does_not_count_down_and_pause_resume_does_not_start(self):
        s = Stopwatch(15_000)
        self.assertEqual(15_000, s.elapse(99_000))
        s.pause(100_000)
        s.resume(200_000)
        self.assertEqual(15_000, s.elapse(300_000))
        self.assertFalse(s.finished)

    def test_restart_resets_to_full_time(self):
        s = Stopwatch(15_000)
        s.start(0)
        s.elapse(10_000)
        s.start(10_000)
        self.assertEqual(15_000, s.elapse(10_000))

    def test_bar_fraction(self):
        s = Stopwatch(10_000)
        self.assertEqual(1.0, s.fraction)
        s.start(0)
        s.elapse(2_500)
        self.assertEqual(0.75, s.fraction)
        s.elapse(20_000)
        self.assertEqual(0.0, s.fraction)

    def test_stop_returns_to_idle_loading_state(self):
        s = Stopwatch(15_000)
        self.assertFalse(s.started)
        s.start(0)
        s.elapse(5_000)
        self.assertTrue(s.started)
        s.stop()
        self.assertFalse(s.started)
        self.assertEqual(15_000, s.elapse(99_000))
        self.assertFalse(s.finished)

    def test_result_with_finger_down_during_loading_only_runs_after_release(self):
        s = Stopwatch(15_000)
        s.stop()
        s.pause(1_000)
        s.start(8_000)
        self.assertEqual(15_000, s.elapse(30_000))
        s.resume(30_000)
        self.assertEqual(13_000, s.elapse(32_000))


if __name__ == "__main__":
    unittest.main()
