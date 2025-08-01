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
    """Convert length strings like ``"11' 9 15/16\""`` to inches.

    Raises
    ------
    ValueError
        If ``length_str`` contains malformed numeric values.
    """
    length_str = length_str.strip().lower()
    if not length_str:
        raise ValueError("Length value is missing")

    metric = re.fullmatch(r"([0-9]*\.?[0-9]+)\s*(mm|cm|m)", length_str)
    if metric:
        val = float(metric.group(1))
        unit = metric.group(2)
        if unit == "mm":
            return val / 25.4
        if unit == "cm":
            return (val * 10) / 25.4
        return (val * 1000) / 25.4

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
                try:
                    num, denom = p.split('/')
                    frac += int(num) / int(denom)
                except (ValueError, ZeroDivisionError) as exc:
                    raise ValueError(f"Invalid fraction '{p}' in length '{length_str}'") from exc
            else:
                try:
                    whole += float(p)
                except ValueError as exc:
                    raise ValueError(f"Invalid number '{p}' in length '{length_str}'") from exc
        inches = whole + frac


    return feet * 12 + inches


DEFAULT_KERF = 0.0
if 'DEFAULT_KERF' in os.environ:
    try:
        DEFAULT_KERF = parse_length(os.environ['DEFAULT_KERF'])
    except ValueError:
        DEFAULT_KERF = 0.0

def parse_parts(text: str):
    parts = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        tokens = line.split()
        if len(tokens) < 3:
            raise ValueError(f"Invalid part line: '{line}'")

        qty_str = tokens[0]
        if not qty_str.isdigit() or int(qty_str) <= 0:
            raise ValueError(f"Invalid quantity '{qty_str}' in line: '{line}'")
        qty = int(qty_str)

        mark = tokens[1]
        length_str = ' '.join(tokens[2:])
        try:
            length = parse_length(length_str)
            if length <= 0:
                raise ValueError("length must be positive")
        except ValueError as exc:
            raise ValueError(f"Invalid length in line '{line}': {exc}") from exc

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
        if len(tokens) < 2:
            raise ValueError(f"Invalid stock line: '{line}'")

        qty_str = tokens[0]
        if not qty_str.isdigit() or int(qty_str) <= 0:
            raise ValueError(f"Invalid quantity '{qty_str}' in line: '{line}'")
        qty = int(qty_str)

        length_str = ' '.join(tokens[1:])
        try:
            length = parse_length(length_str)
            if length <= 0:
                raise ValueError("length must be positive")
        except ValueError as exc:
            raise ValueError(f"Invalid length in line '{line}': {exc}") from exc

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
        qty_str = row.get('qty', '').strip()
        if not qty_str.isdigit() or int(qty_str) <= 0:
            raise ValueError(f"Invalid quantity '{qty_str}' in parts CSV")
        qty = int(qty_str)

        mark = row.get('mark', '').strip()
        length_str = row.get('length', '').strip()
        if not length_str:
            raise ValueError("Missing length in parts CSV")
        try:
            length = parse_length(length_str)
            if length <= 0:
                raise ValueError("length must be positive")
        except ValueError as exc:
            raise ValueError(f"Invalid length '{length_str}' in parts CSV: {exc}") from exc

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
        qty_str = row.get('qty', '').strip()
        if not qty_str.isdigit() or int(qty_str) <= 0:
            raise ValueError(f"Invalid quantity '{qty_str}' in stock CSV")
        qty = int(qty_str)

        length_str = row.get('length', '').strip()
        if not length_str:
            raise ValueError("Missing length in stock CSV")
        try:
            length = parse_length(length_str)
            if length <= 0:
                raise ValueError("length must be positive")
        except ValueError as exc:
            raise ValueError(f"Invalid length '{length_str}' in stock CSV: {exc}") from exc

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
        writer.writerow(["Stick #", "Stock Length", "Total Used", "Remaining Scrap", "Scrap %", "Parts"])
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
                    f"{b.get('scrap_pct', 0.0):.1f}%",
                    parts_list,
                ]
            )

        if uncut:
            writer.writerow([])
            writer.writerow(["Uncut Parts"])
            for p in uncut:
                writer.writerow([p["mark"], format_length(p["length"])])


def export_cutting_plan_json(bins, uncut, kerf_width: float, filename: str, shape: str = "") -> None:
    """Generate a JSON report of the optimized cut plan."""
    import json
    data = {
        "kerf_width": format_length(kerf_width),
        "shape": shape,
        "sticks": [],
        "uncut": [
            {"mark": p["mark"], "length": format_length(p["length"])} for p in uncut
        ],
    }
    used_bins = [b for b in bins if b['parts']]
    for idx, b in enumerate(used_bins, start=1):
        parts_list = [
            {"mark": p["mark"], "length": format_length(p["length"])} for p in b["parts"]
        ]
        data["sticks"].append(
            {
                "stick": idx,
                "stock_length": format_length(b["stock_length"]),
                "used": format_length(b["used"]),
                "remaining": format_length(b["remaining"]),
                "scrap_pct": round(b.get("scrap_pct", 0.0), 1),
                "parts": parts_list,
            }
        )
    total_stock = sum(b["stock_length"] for b in used_bins)
    total_scrap = sum(b["remaining"] for b in used_bins)
    data["total_scrap_pct"] = round((total_scrap / total_stock) * 100, 1) if total_stock else 0.0
    with open(filename, "w") as fh:
        json.dump(data, fh, indent=2)


def export_cutting_plan_text(bins, uncut, kerf_width: float, filename: str, shape: str = "") -> None:
    """Generate a plain text report of the optimized cut plan."""
    with open(filename, "w") as fh:
        fh.write(f"Kerf width: {format_length(kerf_width)}\n")
        if shape:
            fh.write(f"Shape: {shape}\n")
        used_bins = [b for b in bins if b['parts']]
        for idx, b in enumerate(used_bins, start=1):
            fh.write(
                f"Stick {idx}: {format_length(b['stock_length'])} used {format_length(b['used'])} remaining {format_length(b['remaining'])} ({b.get('scrap_pct', 0.0):.1f}% scrap)\n"
            )
            for p in b['parts']:
                fh.write(f"  - {p['mark']} {format_length(p['length'])}\n")
        if uncut:
            fh.write("Uncut Parts:\n")
            for p in uncut:
                fh.write(f"  - {p['mark']} {format_length(p['length'])}\n")


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


@app.route('/download_json/<filename>', methods=['GET'])
def download_json(filename: str):
    """Serve the generated JSON file as a download."""
    json_path = os.path.join(tempfile.gettempdir(), filename)
    return send_file(json_path, as_attachment=True, download_name='cut_plan.json')


@app.route('/download_txt/<filename>', methods=['GET'])
def download_txt(filename: str):
    """Serve the generated text file as a download."""
    txt_path = os.path.join(tempfile.gettempdir(), filename)
    return send_file(txt_path, as_attachment=True, download_name='cut_plan.txt')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', kerf_width=format_length(DEFAULT_KERF))


@app.route('/optimize', methods=['POST'])
def optimize():
    parts_file = request.files.get('parts_file')
    stock_file = request.files.get('stock_file')
    shape = request.form.get('shape', '')
    error = None

    try:
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

        kerf_str = request.form.get('kerf_width', '')
        if kerf_str.strip():
            kerf_width = parse_length(kerf_str)
        else:
            kerf_width = DEFAULT_KERF
    except ValueError as exc:
        error = str(exc)
        return render_template(
            'index.html',
            error=error,
            parts=request.form.get('parts', ''),
            stock=request.form.get('stock', ''),
            shape=shape,
            kerf_width=request.form.get('kerf_width', '0'),
        ), 400

    bins, uncut = optimize_cuts(parts, stocks, kerf_width)
    for b in bins:
        b['used'] = b['stock_length'] - b['remaining']
        b['scrap_pct'] = (
            (b['remaining'] / b['stock_length']) * 100 if b['stock_length'] else 0.0
        )

    # Remove any stock sticks that ended up unused so they don't clutter
    # the results tables or diagrams.
    bins = [b for b in bins if b['parts']]

    total_stock = sum(b['stock_length'] for b in bins)
    total_used = sum(b['used'] for b in bins)
    total_scrap = sum(b['remaining'] for b in bins)
    total_scrap_pct = (total_scrap / total_stock) * 100 if total_stock else 0.0

    layout = generate_layout_data(bins, kerf_width)
    pdf_name = f"{uuid.uuid4()}.pdf"
    pdf_path = os.path.join(tempfile.gettempdir(), pdf_name)
    export_cutting_plan_pdf(bins, uncut, kerf_width, pdf_path, shape)
    csv_name = f"{uuid.uuid4()}.csv"
    csv_path = os.path.join(tempfile.gettempdir(), csv_name)
    export_cutting_plan_csv(bins, uncut, kerf_width, csv_path, shape)
    json_name = f"{uuid.uuid4()}.json"
    json_path = os.path.join(tempfile.gettempdir(), json_name)
    export_cutting_plan_json(bins, uncut, kerf_width, json_path, shape)
    txt_name = f"{uuid.uuid4()}.txt"
    txt_path = os.path.join(tempfile.gettempdir(), txt_name)
    export_cutting_plan_text(bins, uncut, kerf_width, txt_path, shape)
    return render_template(
        'results.html',
        bins=bins,
        uncut=uncut,
        kerf_width=kerf_width,
        layout=layout,
        shape=shape,
        pdf_filename=pdf_name,
        csv_filename=csv_name,
        json_filename=json_name,
        txt_filename=txt_name,
        total_stock=total_stock,
        total_used=total_used,
        total_scrap=total_scrap,
        total_scrap_pct=total_scrap_pct,
        format_length=format_length,
    )


if __name__ == '__main__':
    import argparse

    def check_env_vars():
        required = [
            'FORGECORE_DB_HOST',
            'FORGECORE_DB_USER',
            'FORGECORE_DB_PASSWORD',
            'FORGECORE_DB_NAME',
        ]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    parser = argparse.ArgumentParser(description='Run the BladePlan Flask app')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dev', action='store_true', help='Run in development mode')
    group.add_argument('--prod', action='store_true', help='Run in production mode')
    args = parser.parse_args()

    check_env_vars()

    if args.dev:
        os.environ['FLASK_ENV'] = 'development'
        debug = True
    else:
        os.environ['FLASK_ENV'] = 'production'
        debug = False

    app.run(debug=debug)
