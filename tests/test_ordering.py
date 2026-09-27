import importlib
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from database import database


_database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_database_file.close()
database.DATABASE_FILE = Path(_database_file.name)

application = importlib.import_module("app")


class OrderingStoriesTestCase(unittest.TestCase):
    def setUp(self):
        self.client = application.app.test_client()
        connection = database.get_connection()
        for table in ("order_items", "orders", "rounds", "products", "members"):
            connection.execute(f"DELETE FROM {table}")
        connection.execute(
            "INSERT INTO members (id, name, email, password) VALUES (1, 'Shuai', 'shuai@example.com', 'test')"
        )
        connection.execute(
            "INSERT INTO members (id, name, email, password) VALUES (2, 'Other', 'other@example.com', 'test')"
        )
        connection.execute(
            """
            INSERT INTO products (id, name, category, unit_type, price, available)
            VALUES (1, 'Apples', 'Fruit', 'kg', 4.5, 1)
            """
        )
        connection.commit()
        connection.close()

        with self.client.session_transaction() as session:
            session["member_id"] = 1
            session["member_name"] = "Shuai"
            session["member_role"] = "member"

    def add_round(self, status="open", cutoff_delta=timedelta(days=1)):
        connection = database.get_connection()
        connection.execute(
            """
            INSERT INTO rounds (id, name, cutoff_datetime, pickup_datetime, status)
            VALUES (1, 'Weekly Round', ?, ?, ?)
            """,
            (
                (datetime.now() + cutoff_delta).isoformat(),
                (datetime.now() + timedelta(days=3)).isoformat(),
                status,
            ),
        )
        connection.commit()
        connection.close()

    def add_order(self, member_id=1, status="submitted"):
        connection = database.get_connection()
        connection.execute(
            "INSERT INTO orders (id, member_id, round_id, status) VALUES (1, ?, 1, ?)",
            (member_id, status),
        )
        connection.execute(
            "INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (1, 1, 1, 1)")
        connection.commit()
        connection.close()

    def test_products_explain_when_no_round_is_open(self):
        response = self.client.get("/products")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No open grocery round", response.data)
        self.assertNotIn(b"Add to Order", response.data)

    def test_products_show_name_price_and_sale_type_in_open_round(self):
        self.add_round()
        response = self.client.get("/products")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Apples", response.data)
        self.assertIn(b"$4.50", response.data)
        self.assertIn(b"/ kg", response.data)
        self.assertIn(b'step="0.1"', response.data)

    def test_member_can_modify_submitted_order_before_cutoff(self):
        self.add_round()
        self.add_order()
        page = self.client.get("/current-order")
        self.assertIn(b"Cancel Entire Order", page.data)
        self.assertIn(b'step="0.1"', page.data)
        response = self.client.post("/update-order-item/1", data={"quantity": "2.5"})
        self.assertEqual(response.status_code, 302)
        connection = database.get_connection()
        quantity = connection.execute(
            "SELECT quantity FROM order_items WHERE id = 1"
        ).fetchone()["quantity"]
        connection.close()
        self.assertEqual(quantity, 2.5)

    def test_member_cannot_modify_order_after_cutoff(self):
        self.add_round(cutoff_delta=timedelta(minutes=-1))
        self.add_order()
        response = self.client.post("/update-order-item/1", data={"quantity": "2"})
        self.assertEqual(response.status_code, 409)

    def test_member_can_cancel_own_submitted_order_before_cutoff(self):
        self.add_round()
        self.add_order()
        details = self.client.get("/view-order/1")
        self.assertIn(b"Cancel Entire Order", details.data)
        response = self.client.post("/cancel-order/1")
        self.assertEqual(response.status_code, 302)
        connection = database.get_connection()
        status = connection.execute(
            "SELECT status FROM orders WHERE id = 1"
        ).fetchone()["status"]
        connection.close()
        self.assertEqual(status, "cancelled")

    def test_member_cannot_change_another_members_order(self):
        self.add_round()
        self.add_order(member_id=2)
        response = self.client.post("/remove-order-item/1")
        self.assertEqual(response.status_code, 302)
        connection = database.get_connection()
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM order_items WHERE id = 1"
        ).fetchone()["count"]
        connection.close()
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
