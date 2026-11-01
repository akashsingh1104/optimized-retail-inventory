"""
forecasting.py - AI Demand Forecasting and Inventory Optimization.
Uses scikit-learn's LinearRegression to forecast 7-day demand and computes
smart reorder quantities and ABC revenue classifications.
"""

import numpy as np
import pandas as pd
from datetime import timedelta
from sklearn.linear_model import LinearRegression

# Import database helper functions
try:
    from database import get_sales_history_by_product, get_all_products, get_all_transactions, get_product_by_id, DEFAULT_DB_PATH
except ImportError:
    from .database import get_sales_history_by_product, get_all_products, get_all_transactions, get_product_by_id, DEFAULT_DB_PATH


def forecast_product_demand(product_id, db_path=DEFAULT_DB_PATH):
    """
    Predicts next 7 days of demand for a selected product using Linear Regression
    and computes the recommended reorder quantity using safety stock formula.
    """
    # 1. Fetch product info and past sales
    product = get_product_by_id(product_id, db_path=db_path)
    if not product:
        return None, "Product not found."

    current_stock = int(product["stock"])
    sales_df = get_sales_history_by_product(product_id, db_path=db_path)

    # 2. Check if we have enough historical data
    if sales_df.empty or len(sales_df) < 2:
        return {
            "has_data": False,
            "product_name": product["name"],
            "current_stock": current_stock,
            "message": f"Insufficient sales history for '{product['name']}'. At least 2 days of sales are required to generate an AI forecast."
        }, None

    # 3. Prepare continuous daily timeline so missing days count as 0 sales
    sales_df["date"] = pd.to_datetime(sales_df["date"])
    sales_df = sales_df.sort_values("date").reset_index(drop=True)

    start_date = sales_df["date"].min()
    end_date = sales_df["date"].max()
    full_date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    
    # Reindex to full daily range and fill days without sales with 0
    daily_sales = (
        sales_df.set_index("date")
        .reindex(full_date_range, fill_value=0)
        .rename_axis("date")
        .reset_index()
    )
    daily_sales["units_sold"] = daily_sales["units_sold"].fillna(0)

    # 4. Train Linear Regression model (X = day index, y = units sold)
    n_days = len(daily_sales)
    X_train = np.arange(n_days).reshape(-1, 1)
    y_train = daily_sales["units_sold"].values

    model = LinearRegression()
    model.fit(X_train, y_train)

    # 5. Predict demand for the next 7 days
    future_X = np.arange(n_days, n_days + 7).reshape(-1, 1)
    future_preds = model.predict(future_X)
    
    # Clip negative predictions to zero (sales cannot be negative)
    future_preds = np.maximum(0, future_preds)
    future_dates = [end_date + timedelta(days=i) for i in range(1, 8)]

    # 6. Apply the reorder formula:
    # forecasted_demand_for_7_days = sum of predicted daily sales
    # safety_stock = 20% of forecasted demand
    # suggested_order = forecasted_demand - current_stock + safety_stock
    forecasted_demand = float(np.sum(future_preds))
    safety_stock = 0.20 * forecasted_demand
    raw_suggested = forecasted_demand - current_stock + safety_stock

    if raw_suggested <= 0:
        suggested_order = 0
        reorder_status = "No reorder needed"
        reorder_needed = False
    else:
        suggested_order = int(np.ceil(raw_suggested))
        reorder_status = f"Reorder Suggested: {suggested_order} units"
        reorder_needed = True

    # 7. Build chart-friendly combined DataFrame
    past_chart_data = pd.DataFrame({
        "Date": daily_sales["date"].dt.strftime("%Y-%m-%d"),
        "Historical Sales": daily_sales["units_sold"],
        "Forecasted Sales": np.nan,
        "Type": "Historical"
    })

    future_chart_data = pd.DataFrame({
        "Date": [d.strftime("%Y-%m-%d") for d in future_dates],
        "Historical Sales": np.nan,
        "Forecasted Sales": np.round(future_preds, 1),
        "Type": "Forecast"
    })

    combined_df = pd.concat([past_chart_data, future_chart_data], ignore_index=True)

    # Daily breakdown of 7-day forecast
    forecast_breakdown_df = pd.DataFrame({
        "Day": [f"Day +{i}" for i in range(1, 8)],
        "Date": [d.strftime("%Y-%m-%d") for d in future_dates],
        "Predicted Demand (Units)": np.round(future_preds, 1)
    })

    result = {
        "has_data": True,
        "product_id": product_id,
        "product_name": product["name"],
        "category": product["category"],
        "current_stock": current_stock,
        "reorder_level": int(product["reorder_level"]),
        "forecasted_demand_7_days": round(forecasted_demand, 1),
        "safety_stock": round(safety_stock, 1),
        "suggested_order": suggested_order,
        "reorder_status": reorder_status,
        "reorder_needed": reorder_needed,
        "trend_slope": round(float(model.coef_[0]), 4),
        "avg_daily_sales": round(float(np.mean(y_train)), 2),
        "forecast_breakdown": forecast_breakdown_df,
        "combined_chart_df": combined_df
    }

    return result, None


def perform_abc_analysis(db_path=DEFAULT_DB_PATH):
    """
    Classifies products into A, B, and C categories based on sales revenue.
    - Top 70% of cumulative revenue -> Class A (High priority)
    - Next 20% of cumulative revenue -> Class B (Medium priority)
    - Bottom 10% of cumulative revenue -> Class C (Low priority)
    """
    products_df = get_all_products(db_path=db_path)
    if products_df.empty:
        return pd.DataFrame(), {"A": 0, "B": 0, "C": 0}

    # Fetch sales transactions
    tx_df = get_all_transactions(db_path=db_path)
    sales_tx = tx_df[tx_df["transaction_type"] == "Sale"] if not tx_df.empty else pd.DataFrame()

    if not sales_tx.empty:
        # Group revenue and units sold by product
        revenue_by_product = (
            sales_tx.groupby("product_id")
            .agg(units_sold=("quantity", "sum"), total_revenue=("total_amount", "sum"))
            .reset_index()
        )
        merged = pd.merge(products_df, revenue_by_product, on="product_id", how="left")
    else:
        merged = products_df.copy()
        merged["units_sold"] = 0
        merged["total_revenue"] = 0.0

    # Fill NaN for products with no sales
    merged["units_sold"] = merged["units_sold"].fillna(0).astype(int)
    merged["total_revenue"] = merged["total_revenue"].fillna(0.0).round(2)

    # Sort descending by total revenue
    merged = merged.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)

    total_revenue_all = merged["total_revenue"].sum()

    if total_revenue_all > 0:
        merged["revenue_share_pct"] = (merged["total_revenue"] / total_revenue_all) * 100
        merged["cum_revenue"] = merged["total_revenue"].cumsum()
        merged["cum_share_pct"] = (merged["cum_revenue"] / total_revenue_all) * 100
    else:
        merged["revenue_share_pct"] = 0.0
        merged["cum_revenue"] = 0.0
        merged["cum_share_pct"] = 0.0

    # Classify into A, B, and C
    def classify(row_idx, cum_share, revenue):
        if revenue == 0:
            return "C"
        # If the previous row's cum_share was already >= 70, then this is B or C
        prev_cum = merged.loc[row_idx - 1, "cum_share_pct"] if row_idx > 0 else 0.0
        if prev_cum < 70.0:
            return "A"
        elif prev_cum < 90.0:
            return "B"
        else:
            return "C"

    categories = []
    strategies = []
    for idx in range(len(merged)):
        cat = classify(idx, merged.loc[idx, "cum_share_pct"], merged.loc[idx, "total_revenue"])
        categories.append(cat)
        if cat == "A":
            strategies.append("Tight control, high priority, frequent review")
        elif cat == "B":
            strategies.append("Moderate control, periodic review")
        else:
            strategies.append("Simple control, bulk purchase, minimum overhead")

    merged["ABC_Category"] = categories
    merged["Inventory_Strategy"] = strategies
    merged["revenue_share_pct"] = merged["revenue_share_pct"].round(2)
    merged["cum_share_pct"] = merged["cum_share_pct"].round(2)

    # Summary counts
    counts = merged["ABC_Category"].value_counts().to_dict()
    summary = {
        "A": counts.get("A", 0),
        "B": counts.get("B", 0),
        "C": counts.get("C", 0),
        "total_revenue": round(total_revenue_all, 2)
    }

    return merged, summary

