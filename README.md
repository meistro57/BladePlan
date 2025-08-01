# 🪓 BladePlan

**Smart steel cutting optimizer powered by Flask.**

BladePlan helps fabricators, makers, and metal sorcerers minimize material waste by calculating the most efficient way to cut a list of parts from your available stock lengths.

![image](https://github.com/user-attachments/assets/8d0e64b4-a4dd-43e5-9ed7-d5e3fcacb378)
![image](https://github.com/user-attachments/assets/7ef730f6-1d69-4c0d-b824-7c6504416ab5)


---

## ✨ Features

🔢 **Flexible Input Format**  
Enter your parts list and stock inventory using real-world formats like `14' 3 1/4"` or `5 48'`. BladePlan handles feet/inch/fraction conversions seamlessly.

🧠 **Smart Cut Optimization**  
Uses a First-Fit Decreasing (FFD) nesting algorithm to assign parts to stock lengths while minimizing waste. Simple, fast, and effective.

📊 **Clear, Interactive Output**
Get a complete breakdown of which parts are cut from which sticks, how much material is used, and how much is left.

📄 **CSV Cut Plan Export**
Download the optimized plan as a CSV file for use in spreadsheets or other tools.

📑 **JSON Cut Plan Export**
Grab the results in JSON format for programmatic use.

📊 **Material Totals**
See total stock length, used material, and scrap summarized in the results page.

📐 **Stick Layout Diagram**
Visual diagram showing where each part fits on a stock stick right in the results page.

📝 **Web Interface**  
Lightweight Flask-based interface. No installation mess. Enter your data, hit optimize, and go.

📦 **CSV-Friendly Format**
Import your parts and stock lists from CSV files or type them in manually.

🏷️ **Material Shape**
Optionally specify a shape like `W12x65` to label your reports.

⚔️ **Wasteless Warrior Mode** *(In development)*
Kerf width input supported. Trim order visualization and printable cut sheets still in progress.

---

## 📁 Folder Structure
```
BladePlan/
├── app/
│   ├── __init__.py
│   ├── cut_optimizer_app.py
│   ├── static/
│   │   ├── sample_parts.csv
│   │   ├── sample_stock.csv
│   │   └── style.css
│   └── templates/
│       ├── index.html
│       └── results.html
├── tests/
├── forgecore/
├── requirements.txt
├── README.md
├── .gitignore
```

---

## 🚀 Getting Started

### 1. Clone the Repo
```bash
git clone https://github.com/meistro57/BladePlan.git
cd BladePlan
```

### 2. Set Up Virtual Environment *(Optional but clean)*
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Flask
```bash
pip install --upgrade -r requirements.txt
```

### 4. Run the App
```bash
python app/cut_optimizer_app.py [--dev|--prod]
```

Ensure the following environment variables are set before running:
`FORGECORE_DB_HOST`, `FORGECORE_DB_USER`, `FORGECORE_DB_PASSWORD`, and `FORGECORE_DB_NAME`.

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser 🧠💥

---

## 🧪 Example Input

**Parts List**:
```
1 CA195 14' 3 1/4"
2 CA114 11' 9 15/16"
1 CA130 11' 8 5/8"
```

**Stock Inventory**:
```
5 48'
2 40'
2 24'
```

---

## 🧭 Roadmap
- [x] Kerf width input
- [x] Visual stick layout diagram
- [x] CSV import/export
- [x] PDF cut sheet generator
- [x] Mobile-friendly layout
- [ ] Auto-saving job history

---

## ⚖️ License
MIT. Steal it. Use it. Improve it. Just don’t waste material doing it. 😎

---

## 🧙‍♂️ Created by Meistro57 + Eli the AI
Turning raw stock into optimized art.
