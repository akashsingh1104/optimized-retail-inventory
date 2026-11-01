"""
app.py - Streamlit Web Application for Optimized Retail Inventory Management System.
Features: Dashboard, Product Management, Stock Transactions, Low Stock Alerts,
AI Demand Forecasting (Linear Regression), Smart Reorder Suggestions, ABC Analysis, and CSV Reports.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date

# Database and forecasting imports
from database import (
    init_db,
    get_all_products,
    get_product_by_id,
    add_product,
    update_product,
    delete_product,
    record_transaction,
    get_all_transactions,
    get_low_stock_products,
    get_dashboard_metrics,
    add_user,
    authenticate_user,
    DEFAULT_DB_PATH
)
from forecasting import forecast_product_demand, perform_abc_analysis

# Configure Streamlit page settings
st.set_page_config(
    page_title="Optimized Retail Inventory Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure database tables exist upon startup
init_db()


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def convert_df_to_csv(df):
    """Converts a pandas DataFrame into utf-8 encoded CSV bytes for downloading."""
    return df.to_csv(index=False).encode("utf-8")


# -----------------------------------------------------------------------------
# SESSION STATE & AUTHENTICATION
# -----------------------------------------------------------------------------

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None


# If the user is not authenticated, display the Login & Registration screen
if not st.session_state["authenticated"]:
    # Center the login form using column layout
    _, col_center, _ = st.columns([1, 2, 1])

    with col_center:
        st.markdown("<h2 style='text-align: center;'>🔐 Retail Inventory System</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Optimized AI-Driven Inventory & Demand Forecasting</p>", unsafe_allow_html=True)

        login_tab, register_tab = st.tabs(["🔑 Sign In", "📝 Register New Account"])

        # TAB 1: LOGIN FORM
        with login_tab:
            st.markdown("### Access Store Portal")
            with st.form("login_form"):
                username_input = st.text_input("Username", placeholder="e.g. admin or staff")
                password_input = st.text_input("Password", type="password", placeholder="Enter your password")
                login_btn = st.form_submit_button("Sign In to System", use_container_width=True, type="primary")

                if login_btn:
                    success, result = authenticate_user(username_input, password_input)
                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["user"] = result
                        st.success(f"Welcome back, {result['full_name']}!")
                        st.rerun()
                    else:
                        st.error(result)

            st.markdown("---")
            st.info(
                "💡 **Default College Demo Credentials:**\n\n"
                "- 👤 **Manager Account:** Username: `admin` | Password: `admin123`\n"
                "- 👤 **Staff Account:** Username: `staff` | Password: `staff123`"
            )

        # TAB 2: REGISTER NEW ACCOUNT FORM
        with register_tab:
            st.markdown("### Create New User")
            with st.form("register_form"):
                new_user = st.text_input("Choose Username", placeholder="e.g. john_doe")
                new_name = st.text_input("Full Name", placeholder="e.g. John Doe")
                new_role = st.selectbox("Role", ["Store Manager", "Inventory Staff"])
                new_pass = st.text_input("Password (min. 4 characters)", type="password")
                confirm_pass = st.text_input("Confirm Password", type="password")
                reg_btn = st.form_submit_button("Create Account", use_container_width=True)

                if reg_btn:
                    if new_pass != confirm_pass:
                        st.error("Passwords do not match. Please re-enter carefully.")
                    else:
                        reg_ok, reg_msg = add_user(new_user, new_pass, new_name, new_role)
                        if reg_ok:
                            st.success(reg_msg)
                        else:
                            st.error(reg_msg)

    # Stop rendering the rest of the application until authenticated
    st.stop()


# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION (LOGGED-IN USERS)
# -----------------------------------------------------------------------------

current_user = st.session_state["user"]
st.sidebar.title("📦 Retail Inventory AI")
st.sidebar.markdown(f"👤 **{current_user['full_name']}**")
st.sidebar.caption(f"Role: **{current_user['role']}** | @{current_user['username']}")

if st.sidebar.button("🚪 Log Out", use_container_width=True, type="secondary"):
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()

st.sidebar.markdown("---")

menu_choice = st.sidebar.radio(
    "Navigation Menu",
    [
        "Dashboard",
        "Products",
        "Sales/Purchase",
        "Low Stock",
        "Forecast and Reorder",
        "ABC Analysis",
        "Reports"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Quick Tip:** Use the *Forecast and Reorder* page to see AI predictions powered by scikit-learn Linear Regression."
)


# -----------------------------------------------------------------------------
# PAGE 1: DASHBOARD
# -----------------------------------------------------------------------------
if menu_choice == "Dashboard":
    st.title("📊 Executive Inventory Dashboard")
    st.markdown("Real-time operational overview of retail stock levels, sales, and inventory valuation.")

    # Retrieve dashboard metrics from SQLite database
    metrics = get_dashboard_metrics()

    # 4 Metric Cards in Columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Products", value=f"{metrics['total_products']}")
    with col2:
        st.metric(label="Total Stock Value", value=f"${metrics['total_stock_value']:,.2f}")
    with col3:
        # Highlight low stock items count with warning indication
        st.metric(
            label="Low Stock Alerts",
            value=f"{metrics['low_stock_count']}",
            delta="- Action Needed" if metrics['low_stock_count'] > 0 else "Optimal",
            delta_color="inverse"
        )
    with col4:
        st.metric(
            label="Today's Sales Revenue",
            value=f"${metrics['today_sales_value']:,.2f}",
            help=f"{metrics['today_sales_units']} units sold today"
        )

    st.markdown("---")

    # Layout: Chart on left, Recent Activity on right
    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.subheader("📦 Stock by Category")
        cat_df = metrics["category_df"]
        if not cat_df.empty:
            # Bar chart of stock quantity by category
            fig, ax = plt.subplots(figsize=(7, 4))
            bars = ax.bar(cat_df["category"], cat_df["total_stock"], color="#1f77b4", edgecolor="#0e4e7a", width=0.5)
            ax.set_ylabel("Total Units in Stock", fontsize=10)
            ax.set_xlabel("Category", fontsize=10)
            ax.grid(axis="y", linestyle="--", alpha=0.5)
            # Annotate bar values
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f"{int(height)}",
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha="center", va="bottom", fontsize=9, fontweight="bold")
            plt.xticks(rotation=15, ha="right")
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("No product categories available. Please seed or add products.")

    with right_col:
        st.subheader("⚡ Recent Transactions")
        tx_df = get_all_transactions()
        if not tx_df.empty:
            recent_display = tx_df[["date", "product_name", "transaction_type", "quantity", "total_amount"]].head(6)
            st.dataframe(recent_display, use_container_width=True, hide_index=True)
        else:
            st.info("No transaction records found yet.")

    # Low stock notification banner if any product needs attention
    if metrics["low_stock_count"] > 0:
        st.warning(f"⚠️ **Attention:** {metrics['low_stock_count']} product(s) are at or below their reorder level. Visit the **Low Stock** page for replenishment details.")


# -----------------------------------------------------------------------------
# PAGE 2: PRODUCT MANAGEMENT
# -----------------------------------------------------------------------------
elif menu_choice == "Products":
    st.title("📦 Product Management")
    st.markdown("Add new products, inspect catalogue details, update prices/stock, or remove obsolete items.")

    prod_tab1, prod_tab2, prod_tab3, prod_tab4 = st.tabs([
        "📋 View All Products",
        "➕ Add Product",
        "✏️ Edit Product",
        "🗑️ Delete Product"
    ])

    # TAB 1: View Products
    with prod_tab1:
        df_products = get_all_products()
        if not df_products.empty:
            # Search & Filter
            search_query = st.text_input("🔍 Search products by name or ID:", "")
            categories = ["All"] + sorted(df_products["category"].unique().tolist())
            selected_cat = st.selectbox("Filter by Category:", categories)

            filtered_df = df_products.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df["name"].str.contains(search_query, case=False, na=False) |
                    filtered_df["product_id"].str.contains(search_query, case=False, na=False)
                ]
            if selected_cat != "All":
                filtered_df = filtered_df[filtered_df["category"] == selected_cat]

            # Format price column for cleaner display
            display_df = filtered_df.copy()
            display_df["price"] = display_df["price"].apply(lambda x: f"${x:.2f}")
            display_df["status"] = display_df.apply(
                lambda row: "⚠️ Low Stock" if row["stock"] <= row["reorder_level"] else "✅ In Stock", axis=1
            )

            st.dataframe(
                display_df[[
                    "product_id", "name", "category", "price", "stock", "reorder_level", "status", "supplier"
                ]],
                use_container_width=True,
                hide_index=True
            )
            st.caption(f"Showing {len(display_df)} of {len(df_products)} total products.")
        else:
            st.warning("No products found in the database. Add one below or run `seed_data.py`!")

    # TAB 2: Add Product
    with prod_tab2:
        st.subheader("Add a New Product")
        with st.form("add_product_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                new_id = st.text_input("Product ID (e.g. P121)*")
                new_name = st.text_input("Product Name*")
                new_category = st.text_input("Category (e.g. Electronics, Grocery)*")
                new_supplier = st.text_input("Supplier Name*")
            with col_b:
                new_price = st.number_input("Unit Price ($)*", min_value=0.01, value=19.99, step=0.50)
                new_stock = st.number_input("Current Stock (Units)*", min_value=0, value=20, step=1)
                new_reorder = st.number_input("Reorder Threshold (Units)*", min_value=0, value=10, step=1)

            submit_add = st.form_submit_button("Add Product to Inventory")
            if submit_add:
                success, msg = add_product(new_id, new_name, new_category, new_price, new_stock, new_reorder, new_supplier)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # TAB 3: Edit Product
    with prod_tab3:
        st.subheader("Edit Existing Product")
        df_for_edit = get_all_products()
        if not df_for_edit.empty:
            edit_options = {f"{row['product_id']} - {row['name']}": row['product_id'] for _, row in df_for_edit.iterrows()}
            selected_edit_label = st.selectbox("Select Product to Edit:", list(edit_options.keys()))
            selected_edit_id = edit_options[selected_edit_label]
            current_prod = get_product_by_id(selected_edit_id)

            if current_prod:
                with st.form("edit_product_form"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        st.text_input("Product ID (Cannot be changed)", value=current_prod["product_id"], disabled=True)
                        edit_name = st.text_input("Product Name", value=current_prod["name"])
                        edit_category = st.text_input("Category", value=current_prod["category"])
                        edit_supplier = st.text_input("Supplier Name", value=current_prod["supplier"])
                    with col_e2:
                        edit_price = st.number_input("Unit Price ($)", min_value=0.01, value=float(current_prod["price"]), step=0.50)
                        edit_stock = st.number_input("Current Stock", min_value=0, value=int(current_prod["stock"]), step=1)
                        edit_reorder = st.number_input("Reorder Level", min_value=0, value=int(current_prod["reorder_level"]), step=1)

                    submit_edit = st.form_submit_button("Save Changes")
                    if submit_edit:
                        success, msg = update_product(selected_edit_id, edit_name, edit_category, edit_price, edit_stock, edit_reorder, edit_supplier)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            st.info("No products to edit.")

    # TAB 4: Delete Product
    with prod_tab4:
        st.subheader("Delete Product")
        df_for_del = get_all_products()
        if not df_for_del.empty:
            del_options = {f"{row['product_id']} - {row['name']}": row['product_id'] for _, row in df_for_del.iterrows()}
            selected_del_label = st.selectbox("Select Product to Remove:", list(del_options.keys()), key="del_select")
            selected_del_id = del_options[selected_del_label]

            st.warning(f"⚠️ Are you sure you want to permanently delete `{selected_del_label}`? This will also remove its associated sales logs.")
            confirm_del = st.checkbox("Yes, I understand and confirm deletion.")
            if st.button("Delete Product", type="primary", disabled=not confirm_del):
                success, msg = delete_product(selected_del_id)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.info("No products to delete.")


# -----------------------------------------------------------------------------
# PAGE 3: STOCK TRANSACTIONS (SALES & PURCHASES)
# -----------------------------------------------------------------------------
elif menu_choice == "Sales/Purchase":
    st.title("💳 Stock Transactions")
    st.markdown("Record retail sales (deducts stock) or incoming supplier restocks (increases stock).")

    tx_tab1, tx_tab2, tx_tab3 = st.tabs(["🛒 Record a Sale", "📥 Record Restock / Purchase", "📜 Transaction History"])

    # TAB 1: Record Sale
    with tx_tab1:
        st.subheader("Record a Customer Sale")
        products_df = get_all_products()

        if not products_df.empty:
            # Map product selector with stock info
            sale_choices = {
                f"{r['product_id']} - {r['name']} (Stock: {r['stock']}, Price: ${r['price']:.2f})": r['product_id']
                for _, r in products_df.iterrows()
            }
            selected_sale_label = st.selectbox("Select Product for Sale:", list(sale_choices.keys()))
            sale_pid = sale_choices[selected_sale_label]
            target_prod = get_product_by_id(sale_pid)

            with st.form("record_sale_form"):
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    sale_qty = st.number_input("Quantity Sold", min_value=1, value=1, step=1)
                    sale_date = st.date_input("Sale Date", value=date.today())
                with col_s2:
                    sale_price = st.number_input("Sale Unit Price ($)", min_value=0.01, value=float(target_prod["price"]), step=0.50)
                    total_sale_preview = sale_qty * sale_price
                    st.write(f"**Total Transaction Value:** ${total_sale_preview:.2f}")

                submit_sale = st.form_submit_button("Confirm Sale Transaction")
                if submit_sale:
                    success, msg = record_transaction(
                        product_id=sale_pid,
                        transaction_type="Sale",
                        quantity=sale_qty,
                        tx_date=sale_date.strftime("%Y-%m-%d"),
                        unit_price=sale_price
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.warning("No products available to sell.")

    # TAB 2: Record Purchase / Restock
    with tx_tab2:
        st.subheader("Record Restock / Supplier Purchase")
        products_df = get_all_products()

        if not products_df.empty:
            restock_choices = {
                f"{r['product_id']} - {r['name']} (Current Stock: {r['stock']})": r['product_id']
                for _, r in products_df.iterrows()
            }
            selected_restock_label = st.selectbox("Select Product to Restock:", list(restock_choices.keys()))
            restock_pid = restock_choices[selected_restock_label]
            target_prod = get_product_by_id(restock_pid)

            with st.form("record_purchase_form"):
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    restock_qty = st.number_input("Restock Quantity", min_value=1, value=20, step=1)
                    restock_date = st.date_input("Purchase Date", value=date.today(), key="purchase_date")
                with col_p2:
                    default_cost = round(float(target_prod["price"]) * 0.6, 2)
                    purchase_cost = st.number_input("Unit Cost ($)", min_value=0.01, value=default_cost, step=0.50)
                    total_cost_preview = restock_qty * purchase_cost
                    st.write(f"**Total Restock Cost:** ${total_cost_preview:.2f}")

                submit_purchase = st.form_submit_button("Receive and Update Stock")
                if submit_purchase:
                    success, msg = record_transaction(
                        product_id=restock_pid,
                        transaction_type="Purchase",
                        quantity=restock_qty,
                        tx_date=restock_date.strftime("%Y-%m-%d"),
                        unit_price=purchase_cost
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.warning("No products available to restock.")

    # TAB 3: Transaction History Log
    with tx_tab3:
        st.subheader("All Transaction Records")
        all_tx = get_all_transactions()
        if not all_tx.empty:
            filter_type = st.radio("Filter Type:", ["All", "Sale", "Purchase"], horizontal=True)
            if filter_type != "All":
                display_tx = all_tx[all_tx["transaction_type"] == filter_type]
            else:
                display_tx = all_tx

            # Format money columns
            formatted_tx = display_tx.copy()
            formatted_tx["unit_price"] = formatted_tx["unit_price"].apply(lambda x: f"${x:.2f}")
            formatted_tx["total_amount"] = formatted_tx["total_amount"].apply(lambda x: f"${x:.2f}")

            st.dataframe(formatted_tx, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(formatted_tx)} transactions.")
        else:
            st.info("No transaction records recorded yet.")


# -----------------------------------------------------------------------------
# PAGE 4: LOW STOCK ALERTS
# -----------------------------------------------------------------------------
elif menu_choice == "Low Stock":
    st.title("🚨 Low Stock Alerts")
    st.markdown("Products where **Current Stock <= Reorder Level**. Immediate restocking is recommended to prevent stockouts.")

    low_df = get_low_stock_products()

    if low_df.empty:
        st.success("🎉 All inventory levels are healthy! No products are currently at or below their reorder threshold.")
    else:
        st.error(f"⚠️ **Action Required:** {len(low_df)} product(s) require replenishment!")

        # Highlighting low stock in red using pandas styling
        styled_low_df = low_df.copy()
        styled_low_df["price"] = styled_low_df["price"].apply(lambda x: f"${x:.2f}")

        def highlight_low_stock(row):
            """Applies soft red background highlighting to critical low-stock items."""
            return ["background-color: #ffcccc; color: #900; font-weight: bold;" for _ in row]

        st.dataframe(
            styled_low_df.style.apply(highlight_low_stock, axis=1),
            use_container_width=True,
            hide_index=True
        )

        # Quick Restock Section
        st.markdown("---")
        st.subheader("⚡ Quick Restock Assistant")
        st.caption("Quickly place a restock order for any flagged low-stock item right here.")

        quick_options = {
            f"{row['product_id']} - {row['name']} (Current Stock: {row['stock']} | Reorder Level: {row['reorder_level']})": row['product_id']
            for _, row in low_df.iterrows()
        }
        selected_quick_label = st.selectbox("Select Flagged Product to Restock:", list(quick_options.keys()))
        quick_pid = quick_options[selected_quick_label]

        col_q1, col_q2 = st.columns(2)
        with col_q1:
            restock_units = st.number_input("Units to Add to Stock", min_value=1, value=25, step=1)
        with col_q2:
            st.write("")
            st.write("")
            if st.button("Restock This Product Now", type="primary"):
                success, msg = record_transaction(
                    product_id=quick_pid,
                    transaction_type="Purchase",
                    quantity=restock_units
                )
                if success:
                    st.success(f"Restocked successfully! {msg}")
                    st.rerun()
                else:
                    st.error(msg)


# -----------------------------------------------------------------------------
# PAGE 5: FORECAST AND REORDER (AI DEMAND FORECASTING)
# -----------------------------------------------------------------------------
elif menu_choice == "Forecast and Reorder":
    st.title("🤖 AI Demand Forecasting & Smart Reorder")
    st.markdown("Uses **Linear Regression (scikit-learn)** on past sales history to project customer demand for the next 7 days and compute optimal restock quantities.")

    products_df = get_all_products()
    if products_df.empty:
        st.warning("No products available to forecast.")
    else:
        # Product selector
        prod_select_map = {f"{r['product_id']} - {r['name']} ({r['category']})": r['product_id'] for _, r in products_df.iterrows()}
        selected_label = st.selectbox("Select Product to Analyze:", list(prod_select_map.keys()))
        selected_pid = prod_select_map[selected_label]

        # Run AI Forecast and Reorder analysis
        forecast_result, error = forecast_product_demand(selected_pid)

        if error:
            st.error(error)
        elif not forecast_result["has_data"]:
            st.info(forecast_result["message"])
        else:
            # Display Forecast Summary Cards
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                st.metric("Current Stock", f"{forecast_result['current_stock']} units")
            with col_f2:
                st.metric("7-Day Forecast Demand", f"{forecast_result['forecasted_demand_7_days']} units")
            with col_f3:
                st.metric("Safety Stock Buffer (20%)", f"{forecast_result['safety_stock']} units")
            with col_f4:
                order_qty = forecast_result["suggested_order"]
                st.metric(
                    label="Suggested Reorder",
                    value=f"{order_qty} units" if order_qty > 0 else "0 units",
                    delta="Order Required" if order_qty > 0 else "Sufficient",
                    delta_color="inverse"
                )

            # Reorder Decision Banner
            st.markdown("---")
            if forecast_result["reorder_needed"]:
                st.warning(
                    f"📦 **Reorder Recommendation:** `{forecast_result['suggested_order']} units`\n\n"
                    f"**Formula Explanation:** `Forecast ({forecast_result['forecasted_demand_7_days']}) - Current Stock ({forecast_result['current_stock']}) + Safety Stock ({forecast_result['safety_stock']}) = {forecast_result['suggested_order']} units`"
                )
            else:
                st.success(
                    f"✅ **No reorder needed!** Current inventory ({forecast_result['current_stock']} units) is sufficient to cover projected 7-day demand ({forecast_result['forecasted_demand_7_days']} units) and 20% safety stock."
                )

            # Visual Chart: Historical Sales vs 7-Day AI Forecast
            st.subheader(f"📈 Sales History vs. Next 7 Days Forecast: {forecast_result['product_name']}")

            chart_df = forecast_result["combined_chart_df"]
            fig, ax = plt.subplots(figsize=(10, 4.5))

            # Split past and future for plotting
            hist_mask = chart_df["Type"] == "Historical"
            fore_mask = chart_df["Type"] == "Forecast"

            # Historical Sales line
            ax.plot(
                chart_df.loc[hist_mask, "Date"],
                chart_df.loc[hist_mask, "Historical Sales"],
                label="Historical Sales (Actual)",
                color="#1f77b4",
                marker="o",
                markersize=3,
                linewidth=1.8
            )

            # Connect the last historical point to the forecast line for visual continuity
            last_hist_date = chart_df.loc[hist_mask, "Date"].iloc[-1]
            last_hist_val = chart_df.loc[hist_mask, "Historical Sales"].iloc[-1]

            fore_dates = [last_hist_date] + list(chart_df.loc[fore_mask, "Date"])
            fore_vals = [last_hist_val] + list(chart_df.loc[fore_mask, "Forecasted Sales"])

            # Forecast Line (Dashed)
            ax.plot(
                fore_dates,
                fore_vals,
                label="AI Forecast (Linear Regression)",
                color="#ff7f0e",
                linestyle="--",
                marker="s",
                markersize=6,
                linewidth=2.2
            )

            ax.axvline(x=last_hist_date, color="gray", linestyle=":", alpha=0.8, label="Forecast Horizon Start")
            ax.set_ylabel("Units Sold", fontsize=10)
            ax.set_xlabel("Date", fontsize=10)
            ax.grid(True, linestyle="--", alpha=0.4)
            ax.legend(loc="upper left")

            # Simplify x-axis ticks to avoid crowding
            all_dates = chart_df["Date"].tolist()
            tick_step = max(1, len(all_dates) // 10)
            ax.set_xticks(range(0, len(all_dates), tick_step))
            ax.set_xticklabels([all_dates[i] for i in range(0, len(all_dates), tick_step)], rotation=25, ha="right")

            plt.tight_layout()
            st.pyplot(fig)

            # Detailed 7-Day Table Breakdown
            with st.expander("🔍 View Day-by-Day Forecast Breakdown"):
                st.table(forecast_result["forecast_breakdown"])


# -----------------------------------------------------------------------------
# PAGE 6: ABC ANALYSIS
# -----------------------------------------------------------------------------
elif menu_choice == "ABC Analysis":
    st.title("🏷️ ABC Inventory Classification")
    st.markdown(
        "ABC Analysis segments inventory based on Pareto's Principle to prioritize stock control by sales revenue:\n"
        "- **Class A (Top 70% Revenue):** High-value critical products. Require tight control and frequent reviews.\n"
        "- **Class B (Next 20% Revenue):** Moderate-value items. Require periodic monitoring.\n"
        "- **Class C (Bottom 10% Revenue):** Low-value bulk items. Require simple, automated reorders."
    )

    abc_df, summary = perform_abc_analysis()

    if abc_df.empty:
        st.info("No sales data available to perform ABC Analysis.")
    else:
        # Metrics summary
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Total Store Revenue", f"${summary['total_revenue']:,.2f}")
        with col_m2:
            st.metric("Class A Products", f"{summary['A']} items", "High Value (Top 70%)")
        with col_m3:
            st.metric("Class B Products", f"{summary['B']} items", "Medium Value (Next 20%)")
        with col_m4:
            st.metric("Class C Products", f"{summary['C']} items", "Low Value (Last 10%)")

        st.markdown("---")

        # Visual Breakdown of Categories
        col_chart, col_legend = st.columns([2, 1])
        with col_chart:
            # Distribution of products count per category
            fig, ax = plt.subplots(figsize=(6, 3))
            counts = [summary['A'], summary['B'], summary['C']]
            colors = ["#2ca02c", "#1f77b4", "#ff7f0e"]
            bars = ax.bar(["Class A", "Class B", "Class C"], counts, color=colors, width=0.45)
            ax.set_ylabel("Product Count", fontsize=10)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            for b in bars:
                h = b.get_height()
                ax.annotate(f"{int(h)}", xy=(b.get_x() + b.get_width() / 2, h),
                            xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontweight="bold")
            plt.tight_layout()
            st.pyplot(fig)

        with col_legend:
            st.markdown("### Inventory Policies")
            st.markdown("🟢 **Class A:** Keep buffer low, restock frequently, track daily.")
            st.markdown("🔵 **Class B:** Maintain standard safety buffer, weekly checks.")
            st.markdown("🟠 **Class C:** Large batch orders, prevent stockouts with bulk reserves.")

        # Display full ABC table
        st.subheader("ABC Classification Table")
        table_view = abc_df[[
            "product_id", "name", "category", "units_sold", "total_revenue",
            "revenue_share_pct", "cum_share_pct", "ABC_Category", "Inventory_Strategy"
        ]].copy()

        table_view["total_revenue"] = table_view["total_revenue"].apply(lambda x: f"${x:,.2f}")
        table_view["revenue_share_pct"] = table_view["revenue_share_pct"].apply(lambda x: f"{x:.1f}%")
        table_view["cum_share_pct"] = table_view["cum_share_pct"].apply(lambda x: f"{x:.1f}%")

        def color_abc(val):
            """Applies color coding to ABC classification category."""
            if val == "A":
                return "color: #2ca02c; font-weight: bold;"
            elif val == "B":
                return "color: #1f77b4; font-weight: bold;"
            else:
                return "color: #ff7f0e; font-weight: bold;"

        st.dataframe(
            table_view.style.map(color_abc, subset=["ABC_Category"]),
            use_container_width=True,
            hide_index=True
        )


# -----------------------------------------------------------------------------
# PAGE 7: REPORTS & EXPORTS
# -----------------------------------------------------------------------------
elif menu_choice == "Reports":
    st.title("📥 Reports & CSV Data Export")
    st.markdown("Download full inventory datasets and historical transaction logs as CSV files for backup or external analysis.")

    rep_col1, rep_col2 = st.columns(2)

    with rep_col1:
        st.subheader("📦 Inventory Stock Report")
        products_df = get_all_products()
        if not products_df.empty:
            csv_products = convert_df_to_csv(products_df)
            st.download_button(
                label="⬇️ Download Products CSV",
                data=csv_products,
                file_name=f"inventory_products_{date.today()}.csv",
                mime="text/csv"
            )
            with st.expander("Preview Products Data"):
                st.dataframe(products_df.head(10), hide_index=True)
        else:
            st.info("No product data available.")

    with rep_col2:
        st.subheader("💳 Transactions Log Report")
        transactions_df = get_all_transactions()
        if not transactions_df.empty:
            csv_transactions = convert_df_to_csv(transactions_df)
            st.download_button(
                label="⬇️ Download Transactions CSV",
                data=csv_transactions,
                file_name=f"inventory_transactions_{date.today()}.csv",
                mime="text/csv"
            )
            with st.expander("Preview Transactions Data"):
                st.dataframe(transactions_df.head(10), hide_index=True)
        else:
            st.info("No transaction data available.")

    st.markdown("---")
    rep_col3, rep_col4 = st.columns(2)

    with rep_col3:
        st.subheader("🚨 Low Stock Report")
        low_stock_df = get_low_stock_products()
        if not low_stock_df.empty:
            csv_low = convert_df_to_csv(low_stock_df)
            st.download_button(
                label="⬇️ Download Low Stock Alert CSV",
                data=csv_low,
                file_name=f"low_stock_report_{date.today()}.csv",
                mime="text/csv"
            )
            with st.expander("Preview Low Stock Data"):
                st.dataframe(low_stock_df, hide_index=True)
        else:
            st.success("No low-stock items right now.")

    with rep_col4:
        st.subheader("🏷️ ABC Classification Report")
        abc_data, _ = perform_abc_analysis()
        if not abc_data.empty:
            csv_abc = convert_df_to_csv(abc_data)
            st.download_button(
                label="⬇️ Download ABC Analysis CSV",
                data=csv_abc,
                file_name=f"abc_analysis_report_{date.today()}.csv",
                mime="text/csv"
            )
            with st.expander("Preview ABC Data"):
                st.dataframe(abc_data[["product_id", "name", "total_revenue", "ABC_Category"]].head(10), hide_index=True)
        else:
            st.info("No ABC data available.")

