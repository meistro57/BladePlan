from flask import render_template, request
from . import app
import re


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


def optimize_cuts(parts, stocks):
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
            if part['length'] <= b['remaining']:
                b['parts'].append(part)
                b['remaining'] -= part['length']
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
            inch_part += f" {num}/{denom}"
        inch_part += '"'
    if inch_part:
        if feet:
            parts.append(inch_part)
        else:
            parts.append(inch_part)
    return ' '.join(parts) if parts else '0"'


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/optimize', methods=['POST'])
def optimize():
    parts_input = request.form.get('parts', '')
    stock_input = request.form.get('stock', '')
    parts = parse_parts(parts_input)
    stocks = parse_stock(stock_input)
    bins, uncut = optimize_cuts(parts, stocks)
    for b in bins:
        b['used'] = b['stock_length'] - b['remaining']
    return render_template('results.html', bins=bins, uncut=uncut, format_length=format_length)


if __name__ == '__main__':
    app.run(debug=True)
