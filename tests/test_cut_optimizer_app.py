import unittest
import io
import os
import pathlib
import tempfile
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.cut_optimizer_app import (
    parse_length,
    parse_parts,
    parse_stock,
    parse_parts_csv,
    parse_stock_csv,
    optimize_cuts,
    export_cutting_plan_pdf,
    export_cutting_plan_csv,
    export_cutting_plan_json,
    generate_layout_data,
    app,
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

    def test_parse_csv_negative_values(self):
        bad_parts = io.StringIO('qty,mark,length\n0,A,5\'\n')
        with self.assertRaises(ValueError):
            parse_parts_csv(bad_parts)
        bad_parts_len = io.StringIO('qty,mark,length\n1,A,-5\n')
        with self.assertRaises(ValueError):
            parse_parts_csv(bad_parts_len)
        bad_stock = io.StringIO('qty,length\n0,10\'\n')
        with self.assertRaises(ValueError):
            parse_stock_csv(bad_stock)
        bad_stock_len = io.StringIO('qty,length\n1,-10\n')
        with self.assertRaises(ValueError):
            parse_stock_csv(bad_stock_len)

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

    def test_export_cutting_plan_pdf(self):
        bins = [
            {
                'stock_length': 120,
                'used': 120,
                'remaining': 0,
                'parts': [{'mark': 'A', 'length': 120, 'length_str': "10'"}],
            }
        ]
        uncut = []
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / 'report.pdf'
            export_cutting_plan_pdf(bins, uncut, 0.0, str(path))
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

    def test_export_cutting_plan_csv(self):
        bins = [
            {
                'stock_length': 120,
                'used': 120,
                'remaining': 0,
                'parts': [{'mark': 'A', 'length': 120, 'length_str': "10'"}],
            }
        ]
        uncut = []
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / 'report.csv'
            export_cutting_plan_csv(bins, uncut, 0.0, str(path))
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

    def test_generate_layout_data(self):
        bins = [
            {
                'stock_length': 100,
                'remaining': 20,
                'parts': [
                    {'mark': 'A', 'length': 40},
                    {'mark': 'B', 'length': 40},
                ],
            }
        ]
        layout = generate_layout_data(bins, 0.0)
        self.assertEqual(len(layout), 1)
        segments = layout[0]
        total = sum(s['length'] for s in segments)
        self.assertAlmostEqual(total, 100)

    def test_download_pdf_route(self):
        client = app.test_client()
        bins = [
            {
                'stock_length': 120,
                'used': 120,
                'remaining': 0,
                'parts': [{'mark': 'A', 'length': 120, 'length_str': "10'"}],
            }
        ]
        uncut = []
        path = os.path.join(tempfile.gettempdir(), 'route_test.pdf')
        export_cutting_plan_pdf(bins, uncut, 0.0, path)
        resp = client.get(f'/download_pdf/{os.path.basename(path)}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'application/pdf')
        os.remove(path)

    def test_download_csv_route(self):
        client = app.test_client()
        bins = [
            {
                'stock_length': 120,
                'used': 120,
                'remaining': 0,
                'parts': [{'mark': 'A', 'length': 120, 'length_str': "10'"}],
            }
        ]
        uncut = []
        path = os.path.join(tempfile.gettempdir(), 'route_test.csv')
        export_cutting_plan_csv(bins, uncut, 0.0, path)
        resp = client.get(f'/download_csv/{os.path.basename(path)}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'text/csv')
        os.remove(path)

    def test_download_json_route(self):
        client = app.test_client()
        bins = [
            {
                'stock_length': 120,
                'used': 120,
                'remaining': 0,
                'parts': [{'mark': 'A', 'length': 120, 'length_str': "10'"}],
            }
        ]
        uncut = []
        path = os.path.join(tempfile.gettempdir(), 'route_test.json')
        export_cutting_plan_json(bins, uncut, 0.0, path)
        resp = client.get(f'/download_json/{os.path.basename(path)}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'application/json')
        os.remove(path)

    def test_invalid_parts_input(self):
        with self.assertRaises(ValueError):
            parse_parts("bad line")

    def test_invalid_stock_input(self):
        with self.assertRaises(ValueError):
            parse_stock("x y")

    def test_negative_values(self):
        with self.assertRaises(ValueError):
            parse_parts("0 A 5'")
        with self.assertRaises(ValueError):
            parse_parts("1 A -5")
        with self.assertRaises(ValueError):
            parse_stock("0 10'")
        with self.assertRaises(ValueError):
            parse_stock("1 -10")

    def test_optimize_route_invalid_input(self):
        client = app.test_client()
        resp = client.post(
            "/optimize",
            data={"parts": "bad", "stock": "1 10'"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"Invalid", resp.data)


if __name__ == '__main__':
    unittest.main()
