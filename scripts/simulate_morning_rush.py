import psycopg2
import psycopg2.extras
import time
import random
from datetime import datetime

DB_PARAMS = {
    "host": "localhost",
    "port": 7432,
    "user": "postgres",
    "password": "secret",
    "database": "demo"
}

def simulate_morning_rush(conn):
    print("Starting Morning Rush Firehose! Press Ctrl+C to stop.")
    store_ids = ['MV-01', 'SF-01', 'NY-01'] 
    
    try:
        with conn.cursor() as cur:
            while True:
                live_orders = []
                
                # Generate a burst of 10-30 orders every second
                for _ in range(random.randint(10, 30)):
                    store = random.choice(store_ids)
                    
                    # 30% chance an order is driven by the campaign (anonymous users)
                    is_campaign = random.random() < 0.3 
                    
                    if is_campaign:
                        item = 1 
                        campaign_id = 'SPRING_LATTE_PROMO'
                    else:
                        item = random.choice([2, 3])
                        campaign_id = None
                        
                    qty = random.randint(1, 3)
                    
                    # Insert random anonymous customers (IDs 456, 789) but explicitly EXCLUDE Alex (123)
                    customer = random.choice([456, 789, None, None]) 
                    
                    live_orders.append((store, customer, item, campaign_id, qty))
                
                psycopg2.extras.execute_values(
                    cur,
                    "INSERT INTO demo.live_orders (store_id, customer_id, item_id, campaign_id, quantity) VALUES %s",
                    live_orders
                )
                conn.commit()
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Inserted {len(live_orders)} background orders...", end="\r")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nMorning rush ended.")

if __name__ == "__main__":
    with psycopg2.connect(**DB_PARAMS) as conn:
        simulate_morning_rush(conn)