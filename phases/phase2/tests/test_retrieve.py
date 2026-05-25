import unittest

from phases.phase2.src.retrieve import parse_budget


class TestPhase2BudgetParsing(unittest.TestCase):
    def test_band_budget(self):
        b = parse_budget("low")
        self.assertEqual(b.kind, "band")
        self.assertEqual(b.band, "low")

    def test_range_budget(self):
        b = parse_budget("900-400")
        self.assertEqual(b.kind, "range")
        self.assertEqual(b.min_cost, 400.0)
        self.assertEqual(b.max_cost, 900.0)

    def test_max_budget(self):
        b = parse_budget("800")
        self.assertEqual(b.kind, "max")
        self.assertEqual(b.max_cost, 800.0)


if __name__ == "__main__":
    unittest.main()

