from database.database import get_connection


products = [

    # =========================
    # GRAINS & PANTRY
    # =========================

    ("Organic Oats", "Grains & Pantry", "kg", 3.40),
    ("Brown Rice", "Grains & Pantry", "kg", 4.20),
    ("White Rice", "Grains & Pantry", "kg", 3.80),
    ("Basmati Rice", "Grains & Pantry", "kg", 5.20),
    ("Red Lentils", "Grains & Pantry", "kg", 5.50),
    ("Green Lentils", "Grains & Pantry", "kg", 5.20),
    ("Chickpeas", "Grains & Pantry", "kg", 4.80),
    ("All-Purpose Flour", "Grains & Pantry", "kg", 2.80),
    ("Wholemeal Flour", "Grains & Pantry", "kg", 3.20),
    ("White Sugar", "Grains & Pantry", "kg", 2.50),
    ("Brown Sugar", "Grains & Pantry", "kg", 3.20),
    ("Salt", "Grains & Pantry", "kg", 1.80),
    ("Ground Coffee", "Grains & Pantry", "kg", 18.00),
    ("Tea Bags", "Grains & Pantry", "box", 5.50),

    # =========================
    # DAIRY & REFRIGERATED
    # =========================

    ("Milk", "Dairy", "unit", 3.20),
    ("Free Range Eggs", "Dairy", "dozen", 7.50),
    ("Butter", "Dairy", "unit", 6.00),
    ("Cheddar Cheese", "Dairy", "unit", 8.50),
    ("Mozzarella Cheese", "Dairy", "unit", 9.00),
    ("Yoghurt", "Dairy", "unit", 5.00),
    ("Greek Yoghurt", "Dairy", "unit", 6.50),

    # =========================
    # BAKERY
    # =========================

    ("White Bread", "Bakery", "loaf", 4.00),
    ("Wholemeal Bread", "Bakery", "loaf", 4.50),
    ("Sourdough Bread", "Bakery", "loaf", 6.50),
    ("Bread Rolls", "Bakery", "pack", 5.00),
    ("English Muffins", "Bakery", "pack", 4.50),

    # =========================
    # PASTA & SAUCES
    # =========================

    ("Pasta", "Pasta & Sauces", "kg", 3.50),
    ("Spaghetti", "Pasta & Sauces", "kg", 3.80),
    ("Tomato Sauce", "Pasta & Sauces", "unit", 4.20),
    ("Pasta Sauce", "Pasta & Sauces", "unit", 5.00),
    ("Canned Tomatoes", "Pasta & Sauces", "unit", 2.50),

    # =========================
    # CANNED & PACKAGED
    # =========================

    ("Baked Beans", "Canned & Packaged", "unit", 2.20),
    ("Canned Corn", "Canned & Packaged", "unit", 2.40),
    ("Canned Chickpeas", "Canned & Packaged", "unit", 2.30),
    ("Peanut Butter", "Canned & Packaged", "unit", 5.50),
    ("Breakfast Cereal", "Canned & Packaged", "box", 6.50),
    ("Muesli", "Canned & Packaged", "box", 7.50),
    ("Biscuits", "Canned & Packaged", "pack", 4.00),
    ("Crackers", "Canned & Packaged", "pack", 4.50),

    # =========================
    # COOKING
    # =========================

    ("Cooking Oil", "Cooking", "unit", 7.50),
    ("Extra Virgin Olive Oil", "Cooking", "unit", 12.00),
    ("Apple Cider Vinegar", "Cooking", "unit", 5.50),
    ("Honey", "Cooking", "unit", 8.00),
    ("Tahini", "Cooking", "unit", 8.50),

    # =========================
    # FRUIT
    # =========================

    ("Apples", "Fruit", "kg", 4.50),
    ("Bananas", "Fruit", "kg", 3.50),
    ("Oranges", "Fruit", "kg", 4.20),
    ("Pears", "Fruit", "kg", 5.00),
    ("Grapes", "Fruit", "kg", 6.50),
    ("Lemons", "Fruit", "kg", 5.50),

    # =========================
    # VEGETABLES
    # =========================

    ("Potatoes", "Vegetables", "kg", 3.00),
    ("Onions", "Vegetables", "kg", 2.80),
    ("Carrots", "Vegetables", "kg", 3.20),
    ("Tomatoes", "Vegetables", "kg", 5.00),
    ("Broccoli", "Vegetables", "kg", 6.50),
    ("Spinach", "Vegetables", "kg", 7.00),
    ("Capsicum", "Vegetables", "kg", 6.00),
    ("Garlic", "Vegetables", "kg", 8.00),

    # =========================
    # HOUSEHOLD
    # =========================

    ("Laundry Detergent", "Household", "unit", 9.00),
    ("Dishwashing Liquid", "Household", "unit", 4.50),
    ("Toilet Paper", "Household", "pack", 8.00),
    ("Paper Towels", "Household", "pack", 6.50),
    ("Bin Bags", "Household", "pack", 7.00),
    ("Cleaning Sponges", "Household", "pack", 4.00)
]


connection = get_connection()


for name, category, unit_type, price in products:

    existing_product = connection.execute(
        """
        SELECT id
        FROM products
        WHERE name = ?
        """,
        (name,)
    ).fetchone()


    if existing_product is None:

        connection.execute(
            """
            INSERT INTO products
            (name, category, unit_type, price, available)
            VALUES (?, ?, ?, ?, 1)
            """,
            (name, category, unit_type, price)
        )


connection.commit()
connection.close()


print("Products added successfully!")
print(f"Total products in catalogue: {len(products)}")