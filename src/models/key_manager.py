import logging
from typing import Dict, List
from src.models.database import Database

class KeyManagement:
    """Handles all key-related operations"""
    
    def __init__(self):
        self.db = Database()
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def load_keys(self) -> Dict[str, List[str]]:
        """Load available product keys from database"""
        print("Loading keys from database...")  # Debug
        keys = self.db.get_available_keys()
        print(f"Loaded keys for variants: {list(keys.keys())}")  # Debug
        return keys
    
    def get_and_use_key(self, variant_key: str, user_id: str, user_name: str = None) -> str:
        """Get a key and mark it as used"""
        print(f"Attempting to get key for variant {variant_key} and user {user_id}")  # Debug
        key = self.db.get_and_use_key(variant_key, user_id, user_name)
        print(f"Retrieved key: {'Found' if key else 'None'}")  # Debug
        return key

    @property
    def button_keys(self):
        """Property to maintain compatibility with existing code"""
        class ButtonKeyProxy:
            def __init__(self, db):
                self.db = db
            
            def __setitem__(self, invoice_id, product_key):
                self.db.store_button_key(invoice_id, product_key)
            
            def __getitem__(self, invoice_id):
                return self.db.get_button_key(invoice_id)
        
        return ButtonKeyProxy(self.db) 