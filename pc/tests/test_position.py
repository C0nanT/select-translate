import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core import Position, Size, clamp_position  # noqa: E402

SCREEN = Size(1000, 600)
WINDOW = Size(400, 100)


# mirrors android/.../PositionTest.kt
class PositionTest(unittest.TestCase):
    def test_inside_screen_does_not_move(self):
        self.assertEqual(Position(20, 30), clamp_position(Position(20, 30), SCREEN, WINDOW, centered_x=False))

    def test_clamps_at_right_and_bottom_edges_and_at_left_and_top(self):
        self.assertEqual(Position(600, 500), clamp_position(Position(900, 580), SCREEN, WINDOW, centered_x=False))
        self.assertEqual(Position(0, 0), clamp_position(Position(-50, -5), SCREEN, WINDOW, centered_x=False))

    def test_centered_x_measures_offset_from_center(self):
        self.assertEqual(Position(300, 500), clamp_position(Position(900, 700), SCREEN, WINDOW, centered_x=True))
        self.assertEqual(Position(-300, 0), clamp_position(Position(-900, -10), SCREEN, WINDOW, centered_x=True))

    def test_window_larger_than_screen_stays_in_corner(self):
        small = Size(300, 80)
        self.assertEqual(Position(0, 0), clamp_position(Position(50, 50), small, WINDOW, centered_x=True))
        self.assertEqual(Position(0, 0), clamp_position(Position(50, 50), small, WINDOW, centered_x=False))


if __name__ == "__main__":
    unittest.main()
