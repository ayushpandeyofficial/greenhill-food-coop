from flask import Flask, render_template, request, redirect, url_for, session
from database.database import initialise_database, get_connection

app = Flask(__name__)

app.secret_key = "greenhill-development-key"

# Initialise database
initialise_database()


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_connection()

        member = connection.execute(
            """
            SELECT *
            FROM members
            WHERE email = ? AND password = ?
            """,
            (email, password)
        ).fetchone()

        connection.close()

        if member:

            session["member_id"] = member["id"]
            session["member_name"] = member["name"]
            session["member_role"] = member["role"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        connection = get_connection()

        try:

            connection.execute(
                """
                INSERT INTO members
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, password)
            )

            connection.commit()

        except Exception:

            connection.close()

            return render_template(
                "register.html",
                error="An account with this email already exists."
            )

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "member_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["member_name"],
        role=session["member_role"]
    )


# =========================
# PRODUCTS
# =========================

@app.route("/products")
def products():

    if "member_id" not in session:
        return redirect(url_for("login"))

    selected_category = request.args.get("category")

    connection = get_connection()

    categories = connection.execute(
        """
        SELECT DISTINCT category
        FROM products
        WHERE available = 1
        ORDER BY category
        """
    ).fetchall()

    if selected_category:

        product_list = connection.execute(
            """
            SELECT *
            FROM products
            WHERE available = 1
            AND category = ?
            ORDER BY name
            """,
            (selected_category,)
        ).fetchall()

    else:

        product_list = connection.execute(
            """
            SELECT *
            FROM products
            WHERE available = 1
            ORDER BY category, name
            """
        ).fetchall()

    connection.close()

    category_list = [
        row["category"]
        for row in categories
    ]

    return render_template(
        "products.html",
        products=product_list,
        categories=category_list,
        selected_category=selected_category
    )


# =========================
# ADD PRODUCT TO ORDER
# =========================

@app.route("/add-to-order/<int:product_id>", methods=["POST"])
def add_to_order(product_id):

    # Make sure member is logged in
    if "member_id" not in session:
        return redirect(url_for("login"))

    # Get quantity
    quantity = request.form.get("quantity", type=int)

    # Validate quantity
    if quantity is None or quantity < 1:
        return redirect(url_for("products"))

    connection = get_connection()

    # Find current open grocery round
    current_round = connection.execute(
        """
        SELECT *
        FROM rounds
        WHERE status = 'open'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    if current_round is None:

        connection.close()

        return "No open grocery round is currently available."

    # Check product exists and is available
    product = connection.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        AND available = 1
        """,
        (product_id,)
    ).fetchone()

    if product is None:

        connection.close()

        return "Product not found or unavailable."

    # Check if member already has a draft order
    order = connection.execute(
        """
        SELECT *
        FROM orders
        WHERE member_id = ?
        AND round_id = ?
        AND status = 'draft'
        """,
        (
            session["member_id"],
            current_round["id"]
        )
    ).fetchone()

    # Create new draft order if needed
    if order is None:

        cursor = connection.execute(
            """
            INSERT INTO orders
            (member_id, round_id, status)
            VALUES (?, ?, ?)
            """,
            (
                session["member_id"],
                current_round["id"],
                "draft"
            )
        )

        order_id = cursor.lastrowid

    else:

        order_id = order["id"]

    # Check if product already exists in order
    existing_item = connection.execute(
        """
        SELECT *
        FROM order_items
        WHERE order_id = ?
        AND product_id = ?
        """,
        (
            order_id,
            product_id
        )
    ).fetchone()

    if existing_item:

        # Increase quantity
        connection.execute(
            """
            UPDATE order_items
            SET quantity = quantity + ?
            WHERE order_id = ?
            AND product_id = ?
            """,
            (
                quantity,
                order_id,
                product_id
            )
        )

    else:

        # Add new product
        connection.execute(
            """
            INSERT INTO order_items
            (order_id, product_id, quantity)
            VALUES (?, ?, ?)
            """,
            (
                order_id,
                product_id,
                quantity
            )
        )

    connection.commit()
    connection.close()

    return redirect(url_for("current_order"))
# =========================
# CURRENT ORDER
# =========================

@app.route("/current-order")
def current_order():

    # Make sure member is logged in
    if "member_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()

    # Find the member's current draft order
    order = connection.execute(
        """
        SELECT *
        FROM orders
        WHERE member_id = ?
        AND status = 'draft'
        ORDER BY id DESC
        LIMIT 1
        """,
        (session["member_id"],)
    ).fetchone()

    # If there is no order yet
    if order is None:

        connection.close()

        return render_template(
            "current_order.html",
            order_items=[],
            total=0
        )

    # Get products in the order
    order_items = connection.execute(
        """
        SELECT
            order_items.id,
            order_items.quantity,
            products.name,
            products.price,
            products.unit_type,
            products.category
        FROM order_items
        JOIN products
            ON order_items.product_id = products.id
        WHERE order_items.order_id = ?
        ORDER BY products.name
        """,
        (order["id"],)
    ).fetchall()

    connection.close()

    # Calculate total
    total = sum(
        item["price"] * item["quantity"]
        for item in order_items
    )

    return render_template(
        "current_order.html",
        order_items=order_items,
        total=total
    )
# =========================
# UPDATE ORDER ITEM
# =========================

@app.route("/update-order-item/<int:item_id>", methods=["POST"])
def update_order_item(item_id):

    if "member_id" not in session:
        return redirect(url_for("login"))

    quantity = request.form.get("quantity", type=int)

    connection = get_connection()

    # Make sure this order item belongs to the logged-in member
    item = connection.execute(
        """
        SELECT order_items.id
        FROM order_items
        JOIN orders
            ON order_items.order_id = orders.id
        WHERE order_items.id = ?
        AND orders.member_id = ?
        AND orders.status = 'draft'
        """,
        (
            item_id,
            session["member_id"]
        )
    ).fetchone()

    if item is None:
        connection.close()
        return "Order item not found."

    if quantity is None or quantity < 1:
        connection.close()
        return redirect(url_for("current_order"))

    connection.execute(
        """
        UPDATE order_items
        SET quantity = ?
        WHERE id = ?
        """,
        (
            quantity,
            item_id
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("current_order"))
# =========================
# REMOVE ORDER ITEM
# =========================

@app.route("/remove-order-item/<int:item_id>", methods=["POST"])
def remove_order_item(item_id):

    if "member_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()

    # Make sure this order item belongs to the logged-in member
    item = connection.execute(
        """
        SELECT order_items.id
        FROM order_items
        JOIN orders
            ON order_items.order_id = orders.id
        WHERE order_items.id = ?
        AND orders.member_id = ?
        AND orders.status = 'draft'
        """,
        (
            item_id,
            session["member_id"]
        )
    ).fetchone()

    if item is not None:

        connection.execute(
            """
            DELETE FROM order_items
            WHERE id = ?
            """,
            (item_id,)
        )

        connection.commit()

    connection.close()

    return redirect(url_for("current_order"))

# =========================
# SUBMIT ORDER
# =========================

@app.route("/submit-order", methods=["POST"])
def submit_order():

    # Make sure member is logged in
    if "member_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()

    # Find the member's current draft order
    order = connection.execute(
        """
        SELECT
            orders.id,
            orders.round_id,
            rounds.cutoff_datetime,
            rounds.status AS round_status
        FROM orders
        JOIN rounds
            ON orders.round_id = rounds.id
        WHERE orders.member_id = ?
        AND orders.status = 'draft'
        ORDER BY orders.id DESC
        LIMIT 1
        """,
        (session["member_id"],)
    ).fetchone()

    if order is None:

        connection.close()

        return redirect(url_for("current_order"))

    # Check that the grocery round is still open
    if order["round_status"] != "open":

        connection.close()

        return "This grocery round is closed. The order cannot be submitted."

    # Check the Sunday 8 PM cutoff
    from datetime import datetime

    cutoff_datetime = datetime.fromisoformat(
        order["cutoff_datetime"]
    )

    if datetime.now() > cutoff_datetime:

        connection.close()

        return "The ordering deadline has passed. Orders can no longer be submitted."

    # Make sure the order contains at least one item
    item_count = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM order_items
        WHERE order_id = ?
        """,
        (order["id"],)
    ).fetchone()["count"]

    if item_count == 0:

        connection.close()

        return redirect(url_for("current_order"))

    # Submit the order
    connection.execute(
        """
        UPDATE orders
        SET status = 'submitted'
        WHERE id = ?
        """,
        (order["id"],)
    )

    connection.commit()

    connection.close()

    return redirect(
        url_for(
            "order_confirmation",
            order_id=order["id"]
        )
    )
# =========================
# ORDER CONFIRMATION
# =========================

@app.route("/order-confirmation/<int:order_id>")
def order_confirmation(order_id):

    if "member_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()

    order = connection.execute(
        """
        SELECT
            orders.id,
            orders.status,
            rounds.name AS round_name
        FROM orders
        JOIN rounds
            ON orders.round_id = rounds.id
        WHERE orders.id = ?
        AND orders.member_id = ?
        """,
        (
            order_id,
            session["member_id"]
        )
    ).fetchone()

    connection.close()

    if order is None:
        return "Order not found."

    return render_template(
        "order_confirmation.html",
        order=order
    )
    
@app.route("/my-orders")
def my_orders():
    if "member_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()

    orders = connection.execute(
        """
        SELECT
            orders.id,
            orders.status,
            rounds.name AS round_name,
            rounds.pickup_datetime,
            SUM(order_items.quantity * products.price) AS total
        FROM orders
        JOIN rounds
            ON orders.round_id = rounds.id
        JOIN order_items
            ON orders.id = order_items.order_id
        JOIN products
            ON order_items.product_id = products.id
        WHERE orders.member_id = ?
        AND orders.status = 'submitted'
        GROUP BY orders.id
        ORDER BY orders.id DESC
        """,
        (session["member_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "my_orders.html",
        orders=orders
    )
    
@app.route("/view-order/<int:order_id>")
def view_order(order_id):
    if "member_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()

    order = connection.execute(
        """
        SELECT
            orders.id,
            orders.status,
            rounds.name AS round_name,
            rounds.pickup_datetime
        FROM orders
        JOIN rounds
            ON orders.round_id = rounds.id
        WHERE orders.id = ?
        AND orders.member_id = ?
        """,
        (order_id, session["member_id"])
    ).fetchone()

    if order is None:
        connection.close()
        return "Order not found."

    order_items = connection.execute(
        """
        SELECT
            order_items.quantity,
            products.name,
            products.price,
            products.unit_type,
            products.category
        FROM order_items
        JOIN products
            ON order_items.product_id = products.id
        WHERE order_items.order_id = ?
        ORDER BY products.name
        """,
        (order_id,)
    ).fetchall()

    connection.close()

    total = sum(
        item["price"] * item["quantity"]
        for item in order_items
    )

    return render_template(
        "order_details.html",
        order=order,
        order_items=order_items,
        total=total
    )

@app.route("/staff/orders")
def staff_orders():
    if "member_id" not in session:
        return redirect(url_for("login"))

    if session.get("member_role") != "staff":
        return "Access denied. Staff only."

    connection = get_connection()

    orders = connection.execute(
        """
        SELECT
            orders.id,
            members.name AS member_name,
            members.email AS member_email,
            rounds.name AS round_name,
            orders.status,
            rounds.pickup_datetime,
            SUM(order_items.quantity * products.price) AS total
        FROM orders
        JOIN members
            ON orders.member_id = members.id
        JOIN rounds
            ON orders.round_id = rounds.id
        JOIN order_items
            ON orders.id = order_items.order_id
        JOIN products
            ON order_items.product_id = products.id
        WHERE orders.status = 'submitted'
        GROUP BY orders.id
        ORDER BY orders.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "staff_orders.html",
        orders=orders
    )
    
@app.route("/staff/wholesale-summary")
def wholesale_summary():
    if "member_id" not in session:
        return redirect(url_for("login"))

    if session.get("member_role") != "staff":
        return "Access denied. Staff only."

    connection = get_connection()

    summary = connection.execute(
        """
        SELECT
            product_name,
            unit_type,
            total_quantity
        FROM WholesaleOrderSummary
        ORDER BY product_name
        """
    ).fetchall()

    connection.close()

    return render_template(
        "wholesale_summary.html",
        summary=summary
    )

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    app.run(debug=True)