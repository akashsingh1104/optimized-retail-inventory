# Optimized Retail Inventory Management System

An intelligent, data-driven inventory management and demand forecasting web application designed for modern retail operations. Built using **Python**, **Streamlit**, **SQLite**, and **scikit-learn**.

---

## 📌 Overview

The **Optimized Retail Inventory Management System** bridges traditional inventory tracking with machine learning. It provides store managers and inventory teams with real-time stock control, stockout prevention, automated transaction auditing, Pareto (ABC) revenue classification, and **7-day AI demand forecasting** with automated reorder calculations.

---

## 🛠️ Tech Stack

- **Frontend & App Framework:** [Streamlit](https://streamlit.io/)
- **Backend & Database:** SQLite (built-in `sqlite3` module)
- **Data Analysis & Processing:** pandas & numpy
- **Machine Learning / AI:** scikit-learn (`LinearRegression`)
- **Data Visualization:** matplotlib & Streamlit Native Visualizations

---

## 📁 Repository Structure

```text
├── app.py            # Streamlit web application & interface
├── database.py       # SQLite database layer, schema, CRUD & queries
├── forecasting.py    # scikit-learn Linear Regression models & ABC classification
├── seed_data.py      # Database generator (20 retail products + 90 days sales data)
├── requirements.txt  # Python package dependencies
├── .gitignore        # Git ignore rules
└── README.md         # Project documentation
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/akashsingh1104/optimized-retail-inventory.git
cd optimized-retail-inventory
```

### 2. Install Dependencies
Make sure you have Python 3.10+ installed. Then install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Initialize and Populate the Database
Run the seeding script to create the SQLite database with 20 realistic products across 4 categories and 90 days of transactions:
```bash
python seed_data.py
```

### 4. Run the Application
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 🔑 Pre-configured Accounts

The database comes pre-configured with two user roles:

| Role | Username | Password |
|---|---|---|
| **Store Manager** | `admin` | `admin123` |
| **Inventory Staff** | `staff` | `staff123` |

*(New user accounts can also be created directly via the **Register New Account** tab on the login screen).*

---

## ✨ Features

### 1. Role-Based Authentication
- Secure login and registration powered by **SHA-256 cryptographic password hashing**.
- Protected views with persistent user session state and one-click logout.

### 2. Executive Dashboard
- Live operational metrics: **Total Products**, **Total Stock Value**, **Active Low-Stock Alerts**, and **Today's Sales Revenue**.
- Category-level inventory breakdown chart.
- Real-time stream of latest sales and restock activities.

### 3. Catalogue & Product Management
- Full CRUD capabilities: Add, view, search, filter, edit, and delete products.
- Fields tracked: Product ID, Name, Category, Price, Stock Level, Reorder Level, and Supplier.
- Automatic stock health flags (`In Stock` vs. `Low Stock`).

### 4. Stock Transactions & Inventory Protection
- **Sales Logging:** Deducts inventory and automatically **blocks transactions if requested quantity exceeds stock on hand**, preventing negative inventory anomalies.
- **Restock / Purchase:** Increases stock with unit purchase cost tracking.
- Filterable transaction history with revenue/cost summaries.

### 5. Automated Low-Stock Alerts
- Real-time detection of any product where $\text{Current Stock} \le \text{Reorder Level}$.
- Soft-red alert styling for immediate operational visibility.
- Integrated **Quick Restock Assistant** to trigger replenishment orders directly from the alert screen.

### 6. AI Demand Forecasting & Smart Reorder
- Uses scikit-learn's **Linear Regression** trained on continuous daily sales history to model trends and predict demand for the next 7 days.
- Interactive line charts displaying historical actual sales alongside the 7-day predicted demand trajectory.
- **Dynamic Reorder Formula:**
  $$\text{Suggested Order} = \text{Forecasted 7-Day Demand} - \text{Current Stock} + \text{Safety Stock}$$
  $$\text{Safety Stock} = 20\% \times \text{Forecasted 7-Day Demand}$$
- Automatically outputs *"No reorder needed"* when current stock is sufficient.

### 7. ABC Inventory Classification
- Segments catalog products based on cumulative sales revenue:
  - **Class A (Top 70% Revenue):** High-value critical products requiring tight control and frequent reviews.
  - **Class B (Next 20% Revenue):** Moderate-priority products with periodic checks.
  - **Class C (Remaining 10% Revenue):** Low-value bulk items with minimal management overhead.
- Visual category distribution chart and tailored inventory policy recommendations.

### 8. Data Export & Reporting
- One-click CSV export options for:
  - Complete Product Catalogue
  - Detailed Transaction Audit Log
  - Low Stock Replenishment Report
  - ABC Revenue Classification Dataset

---

## 🧠 Demand Forecasting Methodology

1. **Data Preprocessing:** Daily sales records are aggregated per product. Missing transaction dates in the time horizon are normalized with zero-sales entries to maintain a continuous time series.
2. **Regression Training:** An ordinary least squares linear regression model maps sequential day indices ($X$) against unit sales ($y$).
3. **Horizon Prediction:** The fitted trendline projects expected daily demand for $t + 1$ to $t + 7$, clipping negative projections to zero.
4. **Buffer Optimization:** A 20% safety margin buffers against unexpected demand surges and vendor lead-time delays before calculating net purchase requirements.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
