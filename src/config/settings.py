import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Get the project root directory
ROOT_DIR = Path(__file__).parent.parent.parent

# Load environment variables from .env file in project root
env_path = ROOT_DIR / '.env'
if not env_path.exists():
    print("Error: .env file not found in project root!")
    sys.exit(1)

load_dotenv(dotenv_path=env_path)

# Required settings with error checking
def get_env_var(var_name: str, required: bool = True):
    value = os.getenv(var_name)
    if value is None and required:
        print(f"Error: Missing required environment variable: {var_name}")
        print("Please make sure your .env file contains all required variables.")
        sys.exit(1)
    return value

# Bot settings
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SELLAUTH_API_KEY = os.getenv('SELLAUTH_API_KEY')
SELLAUTH_PASSWORD = os.getenv('SELLAUTH_PASSWORD')
SHOP_ID = os.getenv('SHOP_ID')

# Optional settings with defaults
try:
    GUILD_ID = int(get_env_var('GUILD_ID', required=False) or 0)
except ValueError:
    print("Warning: Invalid GUILD_ID in .env file. Using 0 as default.")
    GUILD_ID = 0

try:
    CUSTOMER_ROLE_ID = int(get_env_var('CUSTOMER_ROLE_ID', required=False) or 0)
except ValueError:
    print("Warning: Invalid CUSTOMER_ROLE_ID in .env file. Using 0 as default.")
    CUSTOMER_ROLE_ID = 0

# SellAuth API Configuration
SELLAUTH_API_BASE = "https://api.sellauth.com/v1"
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")

# File paths
# KEYS_FILE = "product_keys.json"
# BACKUP_DIR = "backups"
# LOG_FILE = "key_usage.log"

# Add database configuration
DATABASE_PATH = "database.db"

# Add this with your other environment variables
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET') 