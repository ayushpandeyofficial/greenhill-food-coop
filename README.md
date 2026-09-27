# Greenhill Food Co-op — Ordering System

A web application replacing Greenhill Food Co-op's paper order forms and 
coordinator spreadsheet with member self-service ordering.

## Prerequisites
- Python 3.10 or later
- pip

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Set up the database
```bash
python add_products.py
python add_round.py
```
These scripts seed the database with sample products and an open ordering 
round so the app isn't empty on first run.

## Run
```bash
python app.py
```
Visit **[http://localhost:5000](http://127.0.0.1:5000)**.

- Go to `register.html` / `login.html` to create an account or sign in as a member.
- View `products.html` to browse available products in the open round.
- Place an order via `current_order.html`, review it on `order_details.html`, 
  and see confirmation on `order_confirmation.html`.
- Members can review past orders on `my_orders.html`.
- Coordinator views: `dashboard.html` (overview), `staff_orders.html` 
  (all member orders), `wholesale_summary.html` (product totals for the 
  wholesale order).

## Project structure
- `app.py` — main Flask application and routes
- `add_products.py` — seed script for demo products
- `add_round.py` — seed script for an open ordering round
- `database/` — database setup and connection
- `templates/` — HTML pages (see above)
- `static/` — CSS/JS/images

## Known limitations
- [Update honestly: e.g. no automated tests yet / payments out of scope / 
  authentication simplified — whatever is actually true right now]

## Team
Ayush Pandey · Shuai Li · Sidharth Dhull · Supriya Adhikari
