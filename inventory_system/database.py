"""
database.py - Database operations for Optimized Retail Inventory Management System.
Handles SQLite connection, schema setup, CRUD for products, and transaction records.
"""

import os
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, date

# Default database file path in the same directory as this script
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")


def get_connection(db_path=DEFAULT_DB_PATH):
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DEFAULT_DB_PATH):
    """Initializes database tables for products and stock transactions."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Table 1: Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            stock INTEGER NOT NULL CHECK(stock >= 0),
            reorder_level INTEGER NOT NULL CHECK(reorder_level >= 0),
            supplier TEXT NOT NULL
        )
    """)

    # Table 2: Stock Transactions (Sales & Restocks)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL CHECK(transaction_type IN ('Sale', 'Purchase')),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            total_amount REAL NOT NULL CHECK(total_amount >= 0),
            date TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        )
    """)

    # Table 3: Users Authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Seed default admin and staff accounts if table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            ("admin", hash_password("admin123"), "Store Administrator", "Store Manager"),
            ("staff", hash_password("staff123"), "Inventory Associate", "Inventory Staff")
        ]
        cursor.executemany(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            default_users
        )

    conn.commit()
    conn.close()


def hash_password(password):
    """Generates a secure SHA-256 hash for a plaintext password."""
    return hashlib.sha256(str(password).encode("utf-8")).hexdigest()


def add_user(username, password, full_name, role="Store Manager", db_path=DEFAULT_DB_PATH):
    """Registers a new user account with hashed password in SQLite."""
    username = str(username).strip().lower()
    full_name = str(full_name).strip()
    password = str(password).strip()

    if not username or not password or not full_name:
        return False, "Username, Full Name, and Password cannot be empty."

    if len(password) < 4:
        return False, "Password must be at least 4 characters long."

    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), full_name, role)
        )
        conn.commit()
        return True, f"User account '{username}' registered successfully! You can now log in."
    except sqlite3.IntegrityError:
        return False, f"Username '{username}' is already taken. Please choose another username."
    except Exception as e:
        return False, f"Failed to register user: {str(e)}"
    finally:
        conn.close()


def authenticate_user(username, password, db_path=DEFAULT_DB_PATH):
    """Validates user credentials against stored SHA-256 password hash."""
    username = str(username).strip().lower()
    password = str(password).strip()

    if not username or not password:
        return False, "Please enter both username and password."

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password_hash, full_name, role FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False, "Username not found. Please check your credentials or register."

    if row["password_hash"] != hash_password(password):
        return False, "Incorrect password. Please try again."

    user_info = {
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"]
    }
    return True, user_info


def add_product(product_id, name, category, price, stock, reorder_level, supplier, db_path=DEFAULT_DB_PATH):
    """Adds a new product to the database after validation."""
    product_id = str(product_id).strip()
    name = str(name).strip()
    category = str(category).strip()
    supplier = str(supplier).strip()

    if not product_id or not name or not category or not supplier:
        return False, "All fields (Product ID, Name, Category, Supplier) are required."

    if price <= 0:
        return False, "Price must be greater than 0."

    if stock < 0 or reorder_level < 0:
        return False, "Stock and Reorder Level cannot be negative."

    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO products (product_id, name, category, price, stock, reorder_level, supplier) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (product_id, name, category, float(price), int(stock), int(reorder_level), supplier)
        )
        conn.commit()
        return True, f"Product '{name}' (ID: {product_id}) added successfully!"
    except sqlite3.IntegrityError:
        return False, f"Product ID '{product_id}' already exists. Please choose a unique ID."
    except Exception as e:
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def get_all_products(db_path=DEFAULT_DB_PATH):
    """Retrieves all products as a pandas DataFrame."""
    conn = get_connection(db_path)
    query = "SELECT product_id, name, category, price, stock, reorder_level, supplier FROM products ORDER BY name ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_product_by_id(product_id, db_path=DEFAULT_DB_PATH):
    """Retrieves a single product by ID as a dictionary."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_product(product_id, name, category, price, stock, reorder_level, supplier, db_path=DEFAULT_DB_PATH):
    """Updates an existing product in the database."""
    name = str(name).strip()
    category = str(category).strip()
    supplier = str(supplier).strip()

    if not name or not category or not supplier:
        return False, "Name, Category, and Supplier cannot be blank."

    if price <= 0:
        return False, "Price must be greater than 0."

    if stock < 0 or reorder_level < 0:
        return False, "Stock and Reorder Level cannot be negative."

    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE products
            SET name = ?, category = ?, price = ?, stock = ?, reorder_level = ?, supplier = ?
            WHERE product_id = ?
            """,
            (name, category, float(price), int(stock), int(reorder_level), supplier, product_id)
        )
        conn.commit()
        return True, f"Product '{product_id}' updated successfully!"
    except Exception as e:
        return False, f"Failed to update product: {str(e)}"
    finally:
        conn.close()


def delete_product(product_id, db_path=DEFAULT_DB_PATH):
    """Deletes a product and its associated transaction history."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM transactions WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
        return True, f"Product '{product_id}' and related records were deleted."
    except Exception as e:
        return False, f"Failed to delete product: {str(e)}"
    finally:
        conn.close()


def record_transaction(product_id, transaction_type, quantity, tx_date=None, unit_price=None, db_path=DEFAULT_DB_PATH):
    """Records a sale or purchase transaction and updates the product stock."""
    quantity = int(quantity)
    if quantity <= 0:
        return False, "Quantity must be greater than 0."

    if transaction_type not in ("Sale", "Purchase"):
        return False, "Transaction type must be 'Sale' or 'Purchase'."

    if not tx_date:
        tx_date = date.today().strftime("%Y-%m-%d")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Fetch current product details
        cursor.execute("SELECT name, stock, price FROM products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            return False, f"Product ID '{product_id}' not found."

        current_stock = product["stock"]
        product_name = product["name"]
        if unit_price is None or unit_price <= 0:
            unit_price = product["price"]

        total_amount = round(quantity * unit_price, 2)

        # Enforce business rules for sales vs purchases
        if transaction_type == "Sale":
            if current_stock < quantity:
                return False, f"Sale blocked! Insufficient stock for '{product_name}'. Current stock: {current_stock}, Requested: {quantity}."
            new_stock = current_stock - quantity
        else:  # Purchase / Restock
            new_stock = current_stock + quantity

        # Update stock in products table
        cursor.execute("UPDATE products SET stock = ? WHERE product_id = ?", (new_stock, product_id))

        # Insert transaction record
        cursor.execute(
            """
            INSERT INTO transactions (product_id, transaction_type, quantity, unit_price, total_amount, date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (product_id, transaction_type, quantity, float(unit_price), total_amount, str(tx_date))
        )

        conn.commit()
        action_verb = "sold" if transaction_type == "Sale" else "restocked"
        return True, f"Successfully {action_verb} {quantity} units of '{product_name}'. Updated stock: {new_stock}."

    except Exception as e:
        conn.rollback()
        return False, f"Transaction failed: {str(e)}"
    finally:
        conn.close()


def get_all_transactions(db_path=DEFAULT_DB_PATH):
    """Retrieves all stock transactions with product details as a DataFrame."""
    conn = get_connection(db_path)
    query = """
        SELECT t.id, t.date, t.product_id, p.name AS product_name, p.category,
               t.transaction_type, t.quantity, t.unit_price, t.total_amount
        FROM transactions t
        LEFT JOIN products p ON t.product_id = p.product_id
        ORDER BY t.date DESC, t.id DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_low_stock_products(db_path=DEFAULT_DB_PATH):
    """Retrieves products where current stock is less than or equal to reorder level."""
    conn = get_connection(db_path)
    query = """
        SELECT product_id, name, category, price, stock, reorder_level,
               (reorder_level - stock) AS stock_deficit, supplier
        FROM products
        WHERE stock <= reorder_level
        ORDER BY (reorder_level - stock) DESC, stock ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_sales_history_by_product(product_id, db_path=DEFAULT_DB_PATH):
    """Retrieves daily aggregated sales history for a specific product."""
    conn = get_connection(db_path)
    query = """
        SELECT date, SUM(quantity) as units_sold, SUM(total_amount) as total_revenue
        FROM transactions
        WHERE product_id = ? AND transaction_type = 'Sale'
        GROUP BY date
        ORDER BY date ASC
    """
    df = pd.read_sql_query(query, conn, params=(product_id,))
    conn.close()
    return df


def get_dashboard_metrics(db_path=DEFAULT_DB_PATH):
    """Computes key summary metrics for the executive dashboard."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Total products
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(stock * price), 0) FROM products")
    total_products, total_stock_value = cursor.fetchone()

    # 2. Low stock count
    cursor.execute("SELECT COUNT(*) FROM products WHERE stock <= reorder_level")
    low_stock_count = cursor.fetchone()[0]

    # 3. Today's sales
    today_str = date.today().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT COALESCE(SUM(total_amount), 0), COALESCE(SUM(quantity), 0) FROM transactions WHERE transaction_type = 'Sale' AND date = ?",
        (today_str,)
    )
    today_sales_value, today_sales_units = cursor.fetchone()

    # 4. Stock by category
    cursor.execute("SELECT category, SUM(stock) as total_stock, SUM(stock * price) as category_value FROM products GROUP BY category ORDER BY total_stock DESC")
    category_rows = cursor.fetchall()
    category_df = pd.DataFrame([dict(r) for r in category_rows])

    conn.close()

    return {
        "total_products": total_products or 0,
        "total_stock_value": round(float(total_stock_value or 0), 2),
        "low_stock_count": low_stock_count or 0,
        "today_sales_value": round(float(today_sales_value or 0), 2),
        "today_sales_units": int(today_sales_units or 0),
        "category_df": category_df
    }

