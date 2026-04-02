import psycopg2
import psycopg2.extras
import random
from datetime import datetime, timedelta

DB_PARAMS = {
    "host": "localhost",
    "port": 7432,
    "user": "postgres",
    "password": "secret",
    "database": "demo"
}

SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS demo;

DROP TABLE IF EXISTS demo.live_orders CASCADE;
DROP TABLE IF EXISTS demo.historical_sales CASCADE;
DROP TABLE IF EXISTS demo.campaigns CASCADE;
DROP TABLE IF EXISTS demo.items CASCADE;
DROP TABLE IF EXISTS demo.customers CASCADE;
DROP TABLE IF EXISTS demo.stores CASCADE;

CREATE TABLE demo.stores (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),
    lat DECIMAL(9,6),
    lng DECIMAL(9,6),
    city VARCHAR(50)
) WITH (pgd.replicate_to_analytics = true);

CREATE TABLE demo.customers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    loyalty_tier VARCHAR(20),
    propensity_score DECIMAL(5,4) DEFAULT 0.0000
) WITH (pgd.replicate_to_analytics = true);

CREATE TABLE demo.items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(5,2)
) WITH (pgd.replicate_to_analytics = true);

CREATE TABLE demo.campaigns (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    target_item_id INTEGER REFERENCES demo.items(id),
    discount_pct DECIMAL(3,2) DEFAULT 0.00
) WITH (pgd.replicate_to_analytics = true);

CREATE TABLE demo.historical_sales (
    id BIGSERIAL PRIMARY KEY,
    store_id VARCHAR(10) REFERENCES demo.stores(id),
    customer_id INTEGER REFERENCES demo.customers(id),
    item_id INTEGER REFERENCES demo.items(id),
    campaign_id VARCHAR(20) REFERENCES demo.campaigns(id),
    quantity INTEGER,
    sale_timestamp TIMESTAMP
) WITH (pgd.replicate_to_analytics = true);

CREATE TABLE demo.live_orders (
    id BIGSERIAL PRIMARY KEY,
    store_id VARCHAR(10) REFERENCES demo.stores(id),
    customer_id INTEGER REFERENCES demo.customers(id),
    item_id INTEGER REFERENCES demo.items(id),
    campaign_id VARCHAR(20) REFERENCES demo.campaigns(id),
    quantity INTEGER,
    order_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) WITH (pgd.replicate_to_analytics = true);
"""

def create_schema():
    print("Connecting to PGD...")
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                print("Creating the 6 core HTAP tables...")
                cur.execute(SCHEMA_SQL)
                conn.commit()
        print("Schema creation successful.")
        seed_data()
    except Exception as e:
        print(f"Database error: {e}")

def seed_data():
    print("Seeding base data after schema creation...")
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                seed_base_data(cur)
                seed_historical_sales(cur)
                conn.commit()
        print("Data seeding successful.")
    except Exception as e:
        print(f"Database error during seeding: {e}")

def seed_base_data(cur):
    print("Seeding stores, items, customers, and campaigns...")
    
    # Stores (Mountain View Cafe theme)
    stores = [
        ('MV-01', 'Mountain View HQ Flagship', 37.3861, -122.0839, 'Mountain View'),
        ('SF-01', 'Market St. Hub', 37.7946, -122.3999, 'San Francisco'),
        ('NY-01', 'Times Square', 40.7580, -73.9855, 'New York')
    ]
    psycopg2.extras.execute_values(cur, "INSERT INTO demo.stores (id, name, lat, lng, city) VALUES %s", stores)

    # Customers (Including our Target Customer 123 for Use Case 2/3)
    customers = [
        (123, 'Alex', 'Chen', 'alex.chen@example.com', 'Gold', 0.6500),
        (456, 'Jordan', 'Smith', 'jsmith@example.com', 'Silver', 0.3200),
        (789, 'Taylor', 'Swift', 'taylor@example.com', 'Platinum', 0.9800)
    ]
    # Reset sequence so we can explicitly insert these IDs
    psycopg2.extras.execute_values(cur, "INSERT INTO demo.customers (id, first_name, last_name, email, loyalty_tier, propensity_score) VALUES %s", customers)

    # Items (With prices for revenue calculations)
    items = [
        (1, 'Spring Oat Milk Latte', 'Seasonal', 6.50),
        (2, 'Classic Cold Brew', 'Coffee', 4.50),
        (3, 'Double Espresso', 'Coffee', 3.00)
    ]
    psycopg2.extras.execute_values(cur, "INSERT INTO demo.items (id, name, category, price) VALUES %s", items)

    # Campaigns
    campaigns = [
        ('SPRING_LATTE_PROMO', 'Spring Kickoff Push', 1, 0.15)
    ]
    psycopg2.extras.execute_values(cur, "INSERT INTO demo.campaigns (id, name, target_item_id, discount_pct) VALUES %s", campaigns)

def seed_historical_sales(cur):
    print("Generating 50,000 historical sales rows (dense 90-day history for the GPU)...")
    historical_data = []
    now = datetime.now()
    store_ids = ['MV-01', 'SF-01', 'NY-01']
    customer_ids = [123, 456, 789, None, None, None, None] # Mostly anonymous
    
    for _ in range(50000):
        store = random.choice(store_ids)
        item = random.choice([1, 2, 3])
        qty = random.randint(1, 3)
        cust = random.choice(customer_ids)
        
        # Randomly attribute some past sales to campaigns if it's item 1
        campaign = 'SPRING_LATTE_PROMO' if item == 1 and random.random() > 0.8 else None
        
        # Focus dates heavily in the last 90 days to feed the dashboard baseline query
        random_days = random.uniform(0, 90)
        sale_time = now - timedelta(days=random_days)
        historical_data.append((store, cust, item, campaign, qty, sale_time))
        
    psycopg2.extras.execute_values(
        cur, 
        "INSERT INTO demo.historical_sales (store_id, customer_id, item_id, campaign_id, quantity, sale_timestamp) VALUES %s", 
        historical_data,
        page_size=10000
    )

if __name__ == "__main__":
    create_schema()