import sqlite3
from pathlib import Path
import logging
from typing import List, Dict
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initialize the database with required tables"""
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id TEXT NOT NULL,
                    discord_name TEXT NOT NULL,
                    invoice_id TEXT NOT NULL,
                    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expiry_date TIMESTAMP NOT NULL,
                    notification_sent BOOLEAN DEFAULT FALSE
                )
            """)
            conn.commit()

    def add_subscription(self, discord_id: str, discord_name: str, invoice_id: str, duration_days: int = 30):
        """Add a new subscription"""
        try:
            with self.connect() as conn:
                expiry_date = datetime.now() + timedelta(days=duration_days)
                conn.execute("""
                    INSERT INTO subscriptions 
                    (discord_id, discord_name, invoice_id, expiry_date)
                    VALUES (?, ?, ?, ?)
                """, (discord_id, discord_name, invoice_id, expiry_date))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Failed to add subscription: {e}")
            return False

    def get_expiring_subscriptions(self):
        """Get subscriptions expiring in ~2 days that haven't been notified"""
        try:
            with self.connect() as conn:
                cursor = conn.execute("""
                    SELECT discord_id, discord_name, expiry_date 
                    FROM subscriptions 
                    WHERE notification_sent = FALSE 
                    AND expiry_date BETWEEN datetime('now', '+1 day', '+23 hours') 
                    AND datetime('now', '+2 days', '+1 hour')
                """)
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Failed to get expiring subscriptions: {e}")
            return []

    def mark_notification_sent(self, discord_id: str):
        """Mark that expiry notification has been sent"""
        try:
            with self.connect() as conn:
                conn.execute("""
                    UPDATE subscriptions 
                    SET notification_sent = TRUE 
                    WHERE discord_id = ?
                """, (discord_id,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Failed to mark notification sent: {e}")
            return False

    def add_keys(self, variant_key: str, keys: List[str]) -> bool:
        """Add new keys to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT INTO keys (variant_key, product_key) VALUES (?, ?)",
                    [(variant_key, key) for key in keys]
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Failed to add keys: {e}")
            return False

    def get_available_keys(self) -> Dict[str, List[str]]:
        """Get all unused keys grouped by variant"""
        try:
            print("DB: Fetching available keys...")  # Debug
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT variant_key, product_key FROM keys WHERE used = FALSE"
                )
                results = cursor.fetchall()
                print(f"DB: Found {len(results)} unused keys")  # Debug
                
                keys_dict = {}
                for variant_key, product_key in results:
                    if variant_key not in keys_dict:
                        keys_dict[variant_key] = []
                    keys_dict[variant_key].append(product_key)
                
                print(f"DB: Keys by variant: {[(k, len(v)) for k, v in keys_dict.items()]}")  # Debug
                return keys_dict
        except Exception as e:
            print(f"DB Error in get_available_keys: {str(e)}")  # Debug
            logging.error(f"Failed to get available keys: {e}")
            return {}

    def get_and_use_key(self, variant_key: str, user_id: str, user_name: str = None) -> str:
        """Get an available key and mark it as used"""
        try:
            print(f"DB: Getting key for variant {variant_key}")  # Debug
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First, add discord_name column if it doesn't exist
                try:
                    cursor.execute("""
                        ALTER TABLE keys ADD COLUMN discord_name TEXT;
                    """)
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                cursor.execute(
                    """
                    SELECT id, product_key 
                    FROM keys 
                    WHERE variant_key = ? AND used = FALSE 
                    LIMIT 1
                    """,
                    (variant_key,)
                )
                result = cursor.fetchone()
                
                print(f"DB: Query result: {result}")  # Debug
                
                if not result:
                    print(f"DB: No available keys found for variant {variant_key}")  # Debug
                    return None
                
                key_id, product_key = result
                print(f"DB: Found key {key_id}")  # Debug
                
                # Mark the key as used
                cursor.execute(
                    """
                    UPDATE keys 
                    SET used = TRUE, 
                        used_by = ?, 
                        used_at = CURRENT_TIMESTAMP,
                        discord_name = ?
                    WHERE id = ?
                    """,
                    (user_id, user_name, key_id)
                )
                
                conn.commit()
                print(f"DB: Marked key {key_id} as used by {user_id} ({user_name})")  # Debug
                return product_key
        except Exception as e:
            print(f"DB Error in get_and_use_key: {str(e)}")  # Debug
            logging.error(f"Failed to get and use key: {e}")
            return None

    def store_button_key(self, invoice_id: str, product_key: str):
        """Store a key for button interaction"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO button_keys (invoice_id, product_key) VALUES (?, ?)",
                    (invoice_id, product_key)
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Failed to store button key: {e}")

    def get_button_key(self, invoice_id: str) -> str:
        """Get a key stored for button interaction"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT product_key FROM button_keys WHERE invoice_id = ?",
                    (invoice_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logging.error(f"Failed to get button key: {e}")
            return None

    def record_purchase(self, discord_id: str, discord_name: str, invoice_id: str, product_key: str, variant_key: str, duration_days: int = 30):
        """Record a purchase in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate expiry date
                cursor.execute("""
                    INSERT INTO purchases (
                        discord_id, 
                        discord_name, 
                        invoice_id, 
                        product_key, 
                        variant_key,
                        expiry_date
                    ) VALUES (?, ?, ?, ?, ?, datetime('now', '+' || ? || ' days'))
                """, (discord_id, discord_name, invoice_id, product_key, variant_key, duration_days))
                
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Failed to record purchase: {e}")
            return False

    def get_user_purchases(self, discord_id: str) -> list:
        """Get all purchases for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        variant_key,
                        product_key,
                        purchase_date,
                        expiry_date,
                        status
                    FROM purchases 
                    WHERE discord_id = ?
                    ORDER BY purchase_date DESC
                """, (discord_id,))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Failed to get user purchases: {e}")
            return [] 