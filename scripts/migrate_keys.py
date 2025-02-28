import json
from pathlib import Path
from src.models.database import Database
from src.config.settings import DATABASE_PATH

def migrate_keys():
    """Migrate keys from JSON file to SQLite database"""
    try:
        # Initialize database
        db = Database(DATABASE_PATH)
        
        # Read existing JSON file
        json_path = Path("product_keys.json")
        if not json_path.exists():
            print("No existing keys file found")
            return
        
        with open(json_path, 'r') as f:
            keys_data = json.load(f)
        
        # Migrate each key
        for variant_key, keys in keys_data.items():
            db.add_keys(variant_key, keys)
        
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_keys() 