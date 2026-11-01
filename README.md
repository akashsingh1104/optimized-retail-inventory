# Optimized Retail Inventory Management System
> **College Mini Project — Digital AI Domain**  
> Built with Python, Streamlit, SQLite, and scikit-learn.

---

## 📌 Project Overview
The **Optimized Retail Inventory Management System** is a streamlined, intelligent inventory control platform built specifically for retail store operations. It combines intuitive inventory tracking with **Machine Learning (scikit-learn Linear Regression)** to accurately forecast customer demand over the next 7 days and recommend mathematically grounded reorder quantities.

---

## 🛠️ Tech Stack
- **Programming Language:** Python 3.10+
- **User Interface:** Streamlit (single-stack full-app framework)
- **Database:** SQLite (built-in `sqlite3` module, local database)
- **Data Manipulation:** pandas & numpy
- **Machine Learning / AI:** scikit-learn (`LinearRegression`)
- **Data Visualization:** matplotlib & Streamlit native components

---

## 📁 Project Structure
```text
inventory_system/
├── app.py            # Streamlit application with interactive sidebar navigation
├── database.py       # SQLite database initialization, CRUD operations & queries
├── forecasting.py    # AI Linear Regression forecasting, Reorder logic & ABC Analysis
├── seed_data.py      # Sample data generator (20 realistic products + 90 days sales)
├── requirements.txt  # Python package dependencies
└── README.md         # Full project documentation and presentation guide
```

---

## 🚀 Quick Start Guide

### 1. Open Terminal or PowerShell
Navigate into the `inventory_system` directory:
```bash
cd "d:\AKASH\PROJECT\Optimized Retail Inventory 1\inventory_system"
```

### 2. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize and Seed the Database
Populates 20 realistic retail products across 4 categories with 90 days of sales history:
```bash
python seed_data.py
```

### 4. Launch the Streamlit Web Application
```bash
streamlit run app.py
```
The app will automatically open in your web browser at `http://localhost:8501`.

### 🔑 Demo Login Credentials
| Role | Username | Password |
|---|---|---|
| **Store Manager** | `admin` | `admin123` |
| **Inventory Staff** | `staff` | `staff123` |

*(You can also click the **"Register New Account"** tab on the login screen to create a custom account!)*

---

## ✨ Core Features

1. **Executive Dashboard:**
   - Real-time KPI cards: Total Products, Total Inventory Valuation, Low-Stock Alerts, and Today's Sales Revenue.
   - Interactive bar chart displaying stock levels categorized by department (Electronics, Grocery, Apparel, Home & Kitchen).
   - Live stream of recent sales and purchase transactions.

2. **Product Management:**
   - Add new products with validation (Product ID, Name, Category, Unit Price, Stock, Reorder Level, Supplier).
   - Search, filter, and view product catalogue with live stock health indicators.
   - Edit pricing, stock levels, or supplier details.
   - Safe product deletion with cascading cleanup.

3. **Stock Transactions (Sales & Purchases):**
   - **Sales:** Enforces stock validation—automatically **blocks sales if inventory is insufficient**, preventing negative stock.
   - **Purchases / Restocks:** Logs incoming stock with supplier purchase cost and increments available inventory.
   - Full transaction audit log with date filters.

4. **Low Stock Alerts:**
   - Automatic alert table flagging all items where `Current Stock <= Reorder Level`.
   - Table rows highlighted in red for quick identification.
   - Built-in **Quick Restock Assistant** to immediately replenish depleted items.

5. **AI Demand Forecasting:**
   - Aggregates daily sales history for any selected item.
   - Uses scikit-learn's `LinearRegression` to learn sales trajectories and predict daily demand for the upcoming 7 days.
   - Visual plot displaying historical actual sales vs. the projected 7-day AI forecast curve.

6. **Smart Reorder Suggestion:**
   - Calculates the exact restock recommendation using safety stock optimization:
     $$\text{Suggested Order} = \text{Forecasted Demand (7 Days)} - \text{Current Stock} + \text{Safety Stock}$$
     $$\text{Safety Stock} = 20\% \times \text{Forecasted Demand (7 Days)}$$
   - Displays *"No reorder needed"* if existing stock covers forecasted demand plus safety buffer.

7. **ABC Inventory Classification:**
   - Evaluates products by sales revenue using Pareto's 80/20 principle:
     - **Class A (Top 70% Revenue):** High-value critical products requiring tight stock control.
     - **Class B (Next 20% Revenue):** Moderate-priority products requiring periodic checks.
     - **Class C (Remaining 10% Revenue):** Low-value bulk items with minimal management overhead.
   - Includes summary breakdown charts and actionable inventory policy recommendations.

8. **Reports & CSV Data Export:**
   - One-click CSV export buttons for Products Inventory, Transactions Audit Log, Low Stock Alerts, and ABC Classification.

---

## 🎯 5-Line Presentation Summary (For Project Defense)

> 1. Our system uses a **Linear Regression** machine learning model from scikit-learn trained on historical daily sales to capture buying trends.
> 2. The AI model projects exact customer demand for each product across the upcoming **7-day planning horizon**.
> 3. To protect against sudden demand spikes, the system automatically calculates a **20% safety stock buffer**.
> 4. The smart reorder formula subtracts current on-hand stock from the projected demand plus safety buffer, recommending the exact replenishment quantity or flagging "No reorder needed".
> 5. Coupled with **ABC revenue classification**, the system enables retailers to prevent costly stockouts while minimizing tied-up capital.

