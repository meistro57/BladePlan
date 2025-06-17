# 🪓 BladePlan

**Smart steel cutting optimizer powered by Flask.**

BladePlan helps fabricators, makers, and metal sorcerers minimize material waste by calculating the most efficient way to cut a list of parts from your available stock lengths.

![image](https://github.com/user-attachments/assets/8d0e64b4-a4dd-43e5-9ed7-d5e3fcacb378)

---

## ✨ Features

🔢 **Flexible Input Format**  
Enter your parts list and stock inventory using real-world formats like `14' 3 1/4"` or `5 48'`. BladePlan handles feet/inch/fraction conversions seamlessly.

🧠 **Smart Cut Optimization**  
Uses a First-Fit Decreasing (FFD) nesting algorithm to assign parts to stock lengths while minimizing waste. Simple, fast, and effective.

📊 **Clear, Interactive Output**
Get a complete breakdown of which parts are cut from which sticks, how much material is used, and how much is left.

📐 **Stick Layout Diagram**
Visual diagram showing where each part fits on a stock stick right in the results page.

📝 **Web Interface**  
Lightweight Flask-based interface. No installation mess. Enter your data, hit optimize, and go.

📦 **CSV-Friendly Format**
Import your parts and stock lists from CSV files or type them in manually.

⚔️ **Wasteless Warrior Mode** *(In development)*
Kerf width input supported. Trim order visualization and printable cut sheets still in progress.

---

## 📁 Folder Structure
```
BladePlan/
├── app/
│   ├── __init__.py
│   ├── cut_optimizer_app.py
│   └── templates/
│       ├── index.html
│       └── results.html
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
pip install -r requirements.txt
```

### 4. Run the App
```bash
python app/cut_optimizer_app.py
```

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
- [ ] Mobile-friendly layout
- [ ] Auto-saving job history

---

## ⚖️ License
MIT. Steal it. Use it. Improve it. Just don’t waste material doing it. 😎

---

## 🧙‍♂️ Created by Meistro57 + Eli the AI
Turning raw stock into optimized art.
