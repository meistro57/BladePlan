from flask import Flask, render_template, request, send_file
import csv
import io
import os
import re
import tempfile
import uuid

app = Flask(__name__)
# Expose Python's ``zip`` function to Jinja templates so they can iterate
# over multiple sequences in parallel.
app.jinja_env.globals.update(zip=zip)


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


def generate_layout_data(bins, kerf_width: float) -> list:
    """Return visual layout information for each bin.

    Each bin is represented as a list of segments with ``label`` and ``length``
    keys. ``Kerf`` and remaining scrap are included as separate segments so the
    caller can render a proportional layout.
    """
    layout_bins = []
    for b in [b for b in bins if b['parts']]:
        segments = []
        remaining = b['stock_length']
        for i, part in enumerate(b['parts']):
            segments.append({'label': part['mark'], 'length': part['length']})
            remaining -= part['length']
            if kerf_width and i < len(b['parts']) - 1:
                segments.append({'label': 'Kerf', 'length': kerf_width})
                remaining -= kerf_width
        if remaining > 0:
            segments.append({'label': 'Scrap', 'length': remaining})
        layout_bins.append(segments)
    return layout_bins


def export_cutting_plan_pdf(bins, uncut, kerf_width: float, filename: str, shape: str = "") -> None:
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
    ]
    if shape:
        elements.append(Paragraph(f"Shape: {shape}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [[
        "Stick #",
        "Stock Length",
        "Total Used",
        "Remaining Scrap",
        "Parts",
    ]]

    used_bins = [b for b in bins if b['parts']]
    for idx, b in enumerate(used_bins, start=1):
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


def export_cutting_plan_csv(bins, uncut, kerf_width: float, filename: str, shape: str = "") -> None:
    """Generate a CSV report of the optimized cut plan."""
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Kerf width", format_length(kerf_width)])
        if shape:
            writer.writerow(["Shape", shape])
        writer.writerow([])
        writer.writerow(["Stick #", "Stock Length", "Total Used", "Remaining Scrap", "Parts"])
        used_bins = [b for b in bins if b['parts']]
        for idx, b in enumerate(used_bins, start=1):
            parts_list = ", ".join(
                f"{p['mark']} - {format_length(p['length'])}" for p in b["parts"]
            )
            writer.writerow(
                [
                    idx,
                    format_length(b["stock_length"]),
                    format_length(b["used"]),
                    format_length(b["remaining"]),
                    parts_list,
                ]
            )

        if uncut:
            writer.writerow([])
            writer.writerow(["Uncut Parts"])
            for p in uncut:
                writer.writerow([p["mark"], format_length(p["length"])])


@app.route('/download_pdf/<filename>', methods=['GET'])
def download_pdf(filename: str):
    """Serve the generated PDF file as a download."""
    pdf_path = os.path.join(tempfile.gettempdir(), filename)
    return send_file(pdf_path, as_attachment=True, download_name='cut_plan.pdf')


@app.route('/download_csv/<filename>', methods=['GET'])
def download_csv(filename: str):
    """Serve the generated CSV file as a download."""
    csv_path = os.path.join(tempfile.gettempdir(), filename)
    return send_file(csv_path, as_attachment=True, download_name='cut_plan.csv')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/optimize', methods=['POST'])
def optimize():
    parts_file = request.files.get('parts_file')
    stock_file = request.files.get('stock_file')
    shape = request.form.get('shape', '')

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

    # Remove any stock sticks that ended up unused so they don't clutter
    # the results tables or diagrams.
    bins = [b for b in bins if b['parts']]

    layout = generate_layout_data(bins, kerf_width)
    pdf_name = f"{uuid.uuid4()}.pdf"
    pdf_path = os.path.join(tempfile.gettempdir(), pdf_name)
    export_cutting_plan_pdf(bins, uncut, kerf_width, pdf_path, shape)
    csv_name = f"{uuid.uuid4()}.csv"
    csv_path = os.path.join(tempfile.gettempdir(), csv_name)
    export_cutting_plan_csv(bins, uncut, kerf_width, csv_path, shape)
    return render_template(
        'results.html',
        bins=bins,
        uncut=uncut,
        kerf_width=kerf_width,
        layout=layout,
        shape=shape,
        pdf_filename=pdf_name,
        csv_filename=csv_name,
        format_length=format_length,
    )


if __name__ == '__main__':
    app.run(debug=True)
