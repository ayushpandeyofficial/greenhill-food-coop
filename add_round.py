from database.database import get_connection
from datetime import datetime, timedelta


# Get today's date
today = datetime.now()

# Find the next Sunday
days_until_sunday = (6 - today.weekday()) % 7

# If today is Sunday, use today's Sunday
cutoff_date = today + timedelta(days=days_until_sunday)

# Set cutoff time to Sunday 8:00 PM
cutoff_datetime = cutoff_date.replace(
    hour=20,
    minute=0,
    second=0,
    microsecond=0
)

# Pickup is the following Wednesday at 5:00 PM
days_until_wednesday = (2 - cutoff_date.weekday()) % 7

# If calculated Wednesday is not after Sunday, add 7 days
if days_until_wednesday == 0:
    days_until_wednesday = 7

pickup_date = cutoff_date + timedelta(days=days_until_wednesday)

pickup_datetime = pickup_date.replace(
    hour=17,
    minute=0,
    second=0,
    microsecond=0
)


connection = get_connection()

# Check whether an open round already exists
existing_round = connection.execute(
    """
    SELECT id
    FROM rounds
    WHERE status = 'open'
    """
).fetchone()

if existing_round:
    print("An open grocery round already exists.")
    print(f"Round ID: {existing_round['id']}")
else:
    connection.execute(
        """
        INSERT INTO rounds
        (name, cutoff_datetime, pickup_datetime, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            "Weekly Grocery Round",
            cutoff_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            pickup_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "open"
        )
    )

    connection.commit()

    print("Weekly grocery round created successfully!")
    print("Cutoff:", cutoff_datetime.strftime("%A, %d %B %Y at %I:%M %p"))
    print("Pickup:", pickup_datetime.strftime("%A, %d %B %Y at %I:%M %p"))

connection.close()