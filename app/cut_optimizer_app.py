from flask import Flask, render_template, request
import csv
import io
import re

app = Flask(__name__)


def parse_length(length_str: str) -> float:
    """Convert length strings like "11' 9 15/16\"" to inches."""
    length_str = length_str.strip().lower()
    feet = 0
    feet_match = re.search(r"(\d+)\s*'", length_str)
    if feet_match:
        feet = int(feet_match.group(1))
        length_str = length_str[feet_match.end():]
    length_str = length_str.replace('"', '').strip()
    inches = 0.0
    if length_str:
        parts = length_str.split()
        whole = 0
        frac = 0.0
        for p in parts:
            if '/' in p:
                num, denom = p.split('/')
                frac += int(num) / int(denom)
            else:
                whole += float(p)
        inches = whole + frac
    return feet * 12 + inches


def parse_parts(text: str):
    parts = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        tokens = line.split()
        qty = int(tokens[0])
        mark = tokens[1]
        length_str = ' '.join(tokens[2:])
        length = parse_length(length_str)
        for _ in range(qty):
            parts.append({'mark': mark, 'length': length, 'length_str': length_str})
    return parts


def parse_stock(text: str):
    stocks = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        tokens = line.split()
        qty = int(tokens[0])
        length_str = ' '.join(tokens[1:])
        length = parse_length(length_str)
        for _ in range(qty):
            stocks.append({'length': length, 'length_str': length_str})
    # Sort stock by length descending for FFD
    stocks.sort(key=lambda x: -x['length'])
    return stocks


def parse_parts_csv(file) -> list:
    """Parse parts from a CSV file stream."""
    parts = []
    data = file.read()
    if not data:
        return parts
    text = data.decode() if isinstance(data, bytes) else data
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        qty = int(row.get('qty', '0'))
        mark = row.get('mark', '').strip()
        length_str = row.get('length', '').strip()
        length = parse_length(length_str)
        for _ in range(qty):
            parts.append({'mark': mark, 'length': length, 'length_str': length_str})
    return parts


def parse_stock_csv(file) -> list:
    """Parse stock lengths from a CSV file stream."""
    stocks = []
    data = file.read()
    if not data:
        return stocks
    text = data.decode() if isinstance(data, bytes) else data
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        qty = int(row.get('qty', '0'))
        length_str = row.get('length', '').strip()
        length = parse_length(length_str)
        for _ in range(qty):
            stocks.append({'length': length, 'length_str': length_str})
    stocks.sort(key=lambda x: -x['length'])
    return stocks


def optimize_cuts(parts, stocks, kerf_width: float = 0.0):
    bins = []
    for stock in stocks:
        bins.append({
            'stock_length': stock['length'],
            'stock_str': stock['length_str'],
            'remaining': stock['length'],
            'parts': []
        })
    parts_sorted = sorted(parts, key=lambda p: -p['length'])
    uncut = []
    for part in parts_sorted:
        placed = False
        for b in bins:
            required = part['length']
            if b['parts']:
                required += kerf_width
            if required <= b['remaining']:
                b['parts'].append(part)
                b['remaining'] -= required
                placed = True
                break
        if not placed:
            uncut.append(part)
    return bins, uncut


def format_length(inches: float) -> str:
    feet = int(inches // 12)
    remaining = inches - feet * 12
    whole = int(remaining)
    frac = remaining - whole
    denom = 16
    num = int(round(frac * denom))
    if num == denom:
        whole += 1
        num = 0

    parts = []
    if feet:
        parts.append(f"{feet}'")

    inch_part = ''
    if whole or num:
        inch_part = f"{whole}" if whole else '0'
        if num:
            from math import gcd
            g = gcd(num, denom)
            simple_num = num // g
            simple_denom = denom // g
            inch_part += f" {simple_num}/{simple_denom}"
        inch_part += '"'

    if inch_part:
        parts.append(inch_part)

    return ' '.join(parts) if parts else '0"'


def export_cutting_plan_pdf(bins, uncut, kerf_width: float, filename: str) -> None:
    """Generate a PDF report of the optimized cut plan.

    Parameters
    ----------
    bins : list
        List of bins returned by :func:`optimize_cuts`.
    uncut : list
        Parts that could not be assigned to a stock length.
    kerf_width : float
        Kerf width in inches.
    filename : str
        Destination path for the generated PDF file.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )

    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Optimized Cut Plan", styles["Heading1"]),
        Paragraph(f"Kerf width: {format_length(kerf_width)}", styles["Normal"]),
        Spacer(1, 12),
    ]

    data = [[
        "Stick #",
        "Stock Length",
        "Total Used",
        "Remaining Scrap",
        "Parts",
    ]]

    for idx, b in enumerate(bins, start=1):
        parts_list = ", ".join(
            f"{p['mark']} - {format_length(p['length'])}" for p in b["parts"]
        )
        data.append(
            [
                str(idx),
                format_length(b["stock_length"]),
                format_length(b["used"]),
                format_length(b["remaining"]),
                parts_list,
            ]
        )

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    elements.append(table)

    if uncut:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Uncut Parts", styles["Heading2"]))
        for p in uncut:
            elements.append(
                Paragraph(
                    f"{p['mark']} - {format_length(p['length'])}",
                    styles["Normal"],
                )
            )

    doc.build(elements)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/optimize', methods=['POST'])
def optimize():
    parts_file = request.files.get('parts_file')
    stock_file = request.files.get('stock_file')

    if parts_file and parts_file.filename:
        parts = parse_parts_csv(parts_file)
    else:
        parts_input = request.form.get('parts', '')
        parts = parse_parts(parts_input)

    if stock_file and stock_file.filename:
        stocks = parse_stock_csv(stock_file)
    else:
        stock_input = request.form.get('stock', '')
        stocks = parse_stock(stock_input)

    kerf_str = request.form.get('kerf_width', '0')
    kerf_width = parse_length(kerf_str) if kerf_str.strip() else 0.0

    bins, uncut = optimize_cuts(parts, stocks, kerf_width)
    for b in bins:
        b['used'] = b['stock_length'] - b['remaining']
    return render_template('results.html', bins=bins, uncut=uncut, kerf_width=kerf_width, format_length=format_length)


if __name__ == '__main__':
    app.run(debug=True)
