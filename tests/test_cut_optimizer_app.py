import unittest
import io
from app.cut_optimizer_app import (
    parse_length,
    parse_parts,
    parse_stock,
    parse_parts_csv,
    parse_stock_csv,
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

    def test_parse_csv(self):
        parts_csv = io.StringIO('qty,mark,length\n1,A,5\'\n')
        stock_csv = io.StringIO('qty,length\n1,10\'\n')
        parts = parse_parts_csv(parts_csv)
        stock = parse_stock_csv(stock_csv)
        self.assertEqual(len(parts), 1)
        self.assertEqual(len(stock), 1)

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

    def test_optimize_cuts_with_kerf(self):
        parts = [
            {'mark': 'A', 'length': 50, 'length_str': "50"},
            {'mark': 'B', 'length': 50, 'length_str': "50"},
        ]
        stock = [{'length': 100, 'length_str': "100"}]
        bins, uncut = optimize_cuts(parts, stock, kerf_width=0.125)
        self.assertEqual(len(uncut), 1)


if __name__ == '__main__':
    unittest.main()
