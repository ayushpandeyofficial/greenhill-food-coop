import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).parent
DATABASE_FILE = DATABASE_DIR / "greenhill.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_FILE)

    connection.row_factory = sqlite3.Row

    return connection


def initialise_database():

    connection = get_connection()

    cursor = connection.cursor()

    # =========================
    # MEMBERS TABLE
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member'
        )
    """)

    # =========================
    # PRODUCTS TABLE
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_type TEXT NOT NULL,
            price REAL NOT NULL,
            available INTEGER NOT NULL DEFAULT 1
        )
    """)

    try:
        cursor.execute(
            "ALTER TABLE products ADD COLUMN category TEXT NOT NULL DEFAULT 'Other'"
        )
    except sqlite3.OperationalError:
        pass

    # =========================
    # ROUNDS TABLE
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cutoff_datetime TEXT NOT NULL,
            pickup_datetime TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open'
        )
    """)

    # =========================
    # ORDERS TABLE
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            round_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',

            FOREIGN KEY (member_id)
                REFERENCES members(id),

            FOREIGN KEY (round_id)
                REFERENCES rounds(id)
        )
    """)

    # =========================
    # ORDER ITEMS TABLE
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity REAL NOT NULL,

            FOREIGN KEY (order_id)
                REFERENCES orders(id),

            FOREIGN KEY (product_id)
                REFERENCES products(id)
        )
    """)

    # =========================
    # WHOLESALE ORDER SUMMARY
    # =========================

    cursor.execute("""
        CREATE VIEW IF NOT EXISTS WholesaleOrderSummary AS
        SELECT
            products.name AS product_name,
            products.unit_type,
            SUM(order_items.quantity) AS total_quantity
        FROM order_items
        JOIN products
            ON order_items.product_id = products.id
        JOIN orders
            ON order_items.order_id = orders.id
        WHERE orders.status = 'submitted'
        GROUP BY
            products.id,
            products.name,
            products.unit_type
    """)

    connection.commit()

    connection.close()