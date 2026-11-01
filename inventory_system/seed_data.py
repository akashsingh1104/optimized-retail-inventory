"""
seed_data.py - Populates the SQLite database with 20 realistic retail products
and 90 days of sales and restock transactions for immediate demonstration.
"""

import os
import random
from datetime import date, timedelta
from database import init_db, get_connection, DEFAULT_DB_PATH


# 20 realistic sample products across 4 popular retail categories
SAMPLE_PRODUCTS = [
    # Electronics
    ("P101", "Wireless Optical Mouse", "Electronics", 24.99, 12, 15, "LogiTech Dist."),    # Low stock
    ("P102", "Mechanical Gaming Keyboard", "Electronics", 79.99, 35, 10, "KeyForge Corp"),
    ("P103", "Braided USB-C Cable (2m)", "Electronics", 9.99, 8, 20, "AnkerSupply"),       # Low stock
    ("P104", "Portable Bluetooth Speaker", "Electronics", 49.99, 22, 10, "SoundWave Ltd"),
    ("P105", "1080p HD Webcam", "Electronics", 39.99, 18, 8, "VisionTech"),

    # Grocery & Pantry
    ("P106", "Organic Espresso Coffee Beans (1kg)", "Grocery", 18.50, 45, 15, "BeanRoasters Co"),
    ("P107", "Pure Green Tea Bags (100pk)", "Grocery", 12.00, 60, 20, "TeaGarden Export"),
    ("P108", "Unsweetened Almond Milk (1L)", "Grocery", 3.75, 5, 25, "DairyFree Farms"),   # Low stock
    ("P109", "Artisan Dark Chocolate (70%)", "Grocery", 4.50, 80, 25, "ChocoCraft"),
    ("P110", "Rolled Whole Oats Jar (1.5kg)", "Grocery", 6.25, 40, 15, "GoldenGrain Co"),

    # Apparel & Fashion
    ("P111", "Classic Cotton Crewneck T-Shirt", "Apparel", 19.99, 50, 20, "UrbanThreads"),
    ("P112", "Slim Fit Denim Jeans", "Apparel", 49.50, 28, 12, "DenimWorks Ltd"),
    ("P113", "Merino Wool Winter Socks (3-Pack)", "Apparel", 14.99, 6, 15, "CozyFeet Inc"), # Low stock
    ("P114", "Breathable Sports Running Cap", "Apparel", 16.50, 32, 10, "AthleticGear"),
    ("P115", "Fleece Zip-up Hoodie", "Apparel", 42.00, 24, 12, "WarmWear Co"),

    # Home & Kitchen
    ("P116", "Insulated Stainless Water Bottle (750ml)", "Home & Kitchen", 21.00, 38, 15, "HydroPure"),
    ("P117", "Matte Ceramic Coffee Mug Set (4pc)", "Home & Kitchen", 26.50, 19, 10, "ClayCraft Studios"),
    ("P118", "LED Dimmable Desk Lamp", "Home & Kitchen", 32.99, 14, 8, "LuminaHome"),
    ("P119", "Glass Airtight Food Container Set", "Home & Kitchen", 29.99, 7, 12, "KitchenSafe"), # Low stock
    ("P120", "Stainless Steel Chef Knife (8 inch)", "Home & Kitchen", 34.50, 25, 10, "EdgeCraft Cutlery")
]


def seed_database(db_path=DEFAULT_DB_PATH):
    """Initializes and seeds the database with products and 90 days of sales history."""
    print(f"Initializing database at: {db_path}")

    # Remove existing database file if present to guarantee a fresh demo state
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Removed existing database for a clean start.")
        except Exception as e:
            print(f"Note: Could not remove old DB file: {e}")

    # Re-initialize tables
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Insert 20 sample products
    print("Seeding 20 sample products...")
    cursor.executemany(
        """
        INSERT INTO products (product_id, name, category, price, stock, reorder_level, supplier)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        SAMPLE_PRODUCTS
    )

    # 2. Generate 90 days of realistic sales transactions
    print("Generating 90 days of realistic sales and restock records...")
    today = date.today()
    random.seed(42)  # Fixed seed for repeatable, realistic sample trends

    # Product popularity weights so some products sell more (generating realistic A, B, C curves)
    product_dict = {p[0]: {"price": p[3], "name": p[1], "category": p[2]} for p in SAMPLE_PRODUCTS}
    
    # Weight factors: some products are bestsellers, others moderate, some niche
    high_sellers = ["P101", "P106", "P111", "P102", "P116"]
    medium_sellers = ["P103", "P107", "P112", "P114", "P118", "P120", "P104"]
    low_sellers = ["P105", "P108", "P109", "P110", "P113", "P115", "P117", "P119"]

    transactions = []

    # Generate records for each of the last 90 days
    for day_offset in range(89, -1, -1):
        current_day = today - timedelta(days=day_offset)
        date_str = current_day.strftime("%Y-%m-%d")

        # Slight weekend lift (Friday/Saturday/Sunday have more sales)
        day_of_week = current_day.weekday()
        weekend_boost = 2 if day_of_week in (4, 5, 6) else 0

        # Number of sales transactions occurring today
        num_sales_today = random.randint(4 + weekend_boost, 8 + weekend_boost)

        # High sellers get picked more frequently
        pool = (high_sellers * 5) + (medium_sellers * 3) + (low_sellers * 1)
        sampled_products = random.sample(pool, min(num_sales_today, len(pool)))

        for pid in sampled_products:
            # Sales quantity between 1 and 5 units
            qty = random.randint(1, 5)
            # Add an upward trend for coffee and mouse over time to show forecasting trend
            if pid in ("P101", "P106") and day_offset < 30:
                qty += random.randint(1, 2)

            price = product_dict[pid]["price"]
            total = round(qty * price, 2)
            transactions.append((pid, "Sale", qty, price, total, date_str))

        # Occasionally add restock / purchase transactions (every 7-10 days for some items)
        if day_offset % 8 == 0:
            restock_pid = random.choice(SAMPLE_PRODUCTS)[0]
            restock_qty = random.randint(15, 30)
            restock_cost = round(product_dict[restock_pid]["price"] * 0.6, 2)  # Wholesale cost
            restock_total = round(restock_qty * restock_cost, 2)
            transactions.append((restock_pid, "Purchase", restock_qty, restock_cost, restock_total, date_str))

    cursor.executemany(
        """
        INSERT INTO transactions (product_id, transaction_type, quantity, unit_price, total_amount, date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        transactions
    )

    conn.commit()
    conn.close()

    print(f"Successfully seeded {len(SAMPLE_PRODUCTS)} products and {len(transactions)} transactions.")
    print("Database is ready for immediate live demo!")


if __name__ == "__main__":
    seed_database()

