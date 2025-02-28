import discord
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys and Secrets
SELLAPP_API_KEY = os.getenv('SELLAPP_API_KEY')
SELLAPP_WEBHOOK_SECRET = os.getenv('SELLAPP_WEBHOOK_SECRET')

# Product Mapping with detailed information
PRODUCTS = {
    "GENERATOR": {
        "id": "215075",
        "emoji": "💎",
        "description": "Generator Access",
        "color": discord.Color.gold(),
        "variants": {
            "MONTHLY": {
                "id": "269485",
                "name": "Generator [30 Days]",
                "description": "1 Month Generator Access",
                "emoji": "💎",
                "amount": "9.99",
                "perks": [
                    "Feature 1",
                    "Feature 2",
                    "Feature 3"
                ]
            },
            "WEEKLY": {
                "id": "271247",
                "name": "Generator [7 Days]",
                "description": "1 Week Generator Access",
                "emoji": "💎",
                "amount": "19.99",
                "perks": [
                    "Feature 1",
                    "Feature 2",
                    "Feature 3"
                ]
            }
        }
    }
}

# Payment Methods
PAYMENT_METHODS = {
    "STRIPE": {"name": "💳 Card", "gateway": "STRIPE"},
    "LTC": {"name": "₿ LTC", "gateway": "LTC"},
    "CASHAPP": {"name": "💵 CashApp", "gateway": "CASHAPP"},
    "PAYPAL": {"name": "💰 PayPal", "gateway": "PAYPAL"}
}

# Emojis
EMOJIS = {
    # Status Emojis
    "success": "✅",
    "error": "❌",
    "pending": "⏳",
    "completed": "🎉",
    
    # Product Category Emojis
    "cart": "🛒",
    "status": "📋",
    "money": "💵",
    "time": "⏰",
    
    # Communication Emojis
    "email": "📧",
    "coupon": "🎟️",
    
    # Payment Method Emojis
    "stripe": "💳",
    "paypal": "💰",
    "crypto": "₿",
    
    # Misc Emojis
    "info": "ℹ️",
    "warning": "⚠️",
    "star": "⭐",
    "sparkles": "✨",
    "gem": "💎",
    "crown": "👑",
    "clock": "🕒",
    "link": "🔗",
    "search": "🔍",
    "chart": "📊",
    "receipt": "📄",
    "wallet": "👛"
}