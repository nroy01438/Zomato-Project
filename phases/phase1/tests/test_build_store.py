import unittest

from phases.phase1.src.build_store import (
    normalize_cuisines,
    parse_cost_for_two,
    parse_int,
    parse_rating,
)


class TestPhase1Parsing(unittest.TestCase):
    def test_parse_rating(self):
        self.assertEqual(parse_rating("4.2/5"), 4.2)
        self.assertIsNone(parse_rating("NEW"))
        self.assertIsNone(parse_rating("-"))
        self.assertIsNone(parse_rating("6.0"))

    def test_parse_cost_for_two(self):
        self.assertEqual(parse_cost_for_two("₹500 for two"), 500.0)
        self.assertEqual(parse_cost_for_two("1,600"), 1600.0)
        self.assertIsNone(parse_cost_for_two("0"))

    def test_parse_int(self):
        self.assertEqual(parse_int("1,234 votes"), 1234)
        self.assertIsNone(parse_int(""))

    def test_normalize_cuisines(self):
        self.assertEqual(normalize_cuisines("Italian, Pizza"), "Italian|Pizza")
        self.assertEqual(normalize_cuisines("North Indian & Chinese"), "North Indian|Chinese")


if __name__ == "__main__":
    unittest.main()

