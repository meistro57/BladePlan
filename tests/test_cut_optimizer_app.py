import unittest
from app.cut_optimizer_app import (
    parse_length,
    parse_parts,
    parse_stock,
    optimize_cuts,
)


class TestCutOptimizer(unittest.TestCase):
    def test_parse_length(self):
        self.assertAlmostEqual(parse_length("7' 6"), 90.0)
        self.assertAlmostEqual(parse_length("10'"), 120.0)
        self.assertAlmostEqual(parse_length("18 3/8"), 18.375)

    def test_parse_parts_and_stock(self):
        parts_text = """1 CA195 7'
2 CA100 3' 6"""
        stock_text = "1 10'\n1 8'"
        parts = parse_parts(parts_text)
        self.assertEqual(len(parts), 3)
        stock = parse_stock(stock_text)
        self.assertEqual(len(stock), 2)

    def test_optimize_cuts(self):
        parts = [
            {'mark': 'A', 'length': 60, 'length_str': "5'"},
            {'mark': 'B', 'length': 48, 'length_str': "4'"},
        ]
        stock = [{'length': 120, 'length_str': "10'"}]
        bins, uncut = optimize_cuts(parts, stock)
        self.assertEqual(len(uncut), 0)
        self.assertEqual(len(bins[0]['parts']), 2)
        self.assertAlmostEqual(bins[0]['remaining'], 12)


if __name__ == '__main__':
    unittest.main()
