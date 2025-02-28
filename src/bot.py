import discord
from discord.ext import commands, tasks
from collections import defaultdict
from src.models.key_manager import KeyManagement
from src.models.product import ProductDelivery
import requests
from src.config.settings import SELLAUTH_API_KEY, SELLAUTH_PASSWORD, SHOP_ID, GUILD_ID, CUSTOMER_ROLE_ID, SELLAUTH_API_BASE
import logging
import datetime
import aiohttp
from src.models.database import Database
import json
from datetime import datetime, timedelta
from src.webhooks.sellauth_webhook import SellAuthWebhook

class ZwiftsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Add message content intent
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix="!",
            intents=intents
        )
        self.key_manager = KeyManagement()
        self.product_delivery = ProductDelivery(self, self.key_manager)
        self.active_invoices = {}
        self.last_status_check = defaultdict(float)
        self.STATUS_CHECK_COOLDOWN = 60  # 60 seconds cooldown
        self._extensions_loaded = False  # Track if extensions are loaded
        self.db = Database()  # Initialize the database
        self.webhook_handler = None
        
    async def setup_hook(self):
        """Initial setup when bot is starting"""
        print("Setting up bot...")
        
        try:
            print("Loading commands cog...")
            await self.load_extension("src.cogs.commands")
            print("Commands cog loaded successfully")
            
            print("Registering commands...")
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            commands = await self.tree.sync(guild=guild)
            print(f"Successfully synced {len(commands)} commands to guild")
            for cmd in commands:
                print(f"Registered command: {cmd.name}")
        except Exception as e:
            print(f"Error during setup: {e}")
            import traceback
            traceback.print_exc()

        print("Starting tasks...")
        self.check_invoices.start()
        self.check_expiring_subs.start()
        self.check_invoice_status.start()  # Start the background task

        # Start webhook server
        self.webhook_handler = SellAuthWebhook(self)
        await self.webhook_handler.start()

        print("Bot setup complete!")

    @commands.Cog.listener()
    async def on_ready(self):
        """Handler for bot ready event"""
        print(f"Logged in as {self.user.name}")
        print(f"Bot ID: {self.user.id}")
        print(f"Guild ID: {GUILD_ID}")
        print("------")
        
        # Try to sync commands again on ready
        try:
            guild = self.get_guild(GUILD_ID)
            if guild:
                print(f"Attempting to sync commands to {guild.name}...")
                synced = await self.tree.sync(guild=guild)
                print(f"Synced {len(synced)} commands")
                for cmd in synced:
                    print(f"- Command available: {cmd.name}")
            else:
                print(f"Could not find guild with ID {GUILD_ID}")
        except Exception as e:
            print(f"Error syncing commands on ready: {e}")

    async def create_sellauth_invoice(self, user_id: str, product_id: str, checkout_data: dict) -> dict:
        """Create a SELLAUTH invoice"""
        url = f"{SELLAUTH_API_BASE}/shops/{SHOP_ID}/checkout"
        headers = {
            "Authorization": f"Bearer {SELLAUTH_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Format the request payload
        payload = {
            "cart": [{
                "productId": int(checkout_data["cart"][0]["productId"]),
                "variantId": int(checkout_data["cart"][0]["variantId"]),
                "quantity": 1
            }],
            "email": checkout_data["email"],
            "discord_user_id": str(user_id)
        }

        # Set the correct gateway based on docs
        if checkout_data.get("gateway") == "CRYPTO":
            payload["gateway"] = "LTC"  # Using LTC as default crypto gateway
        else:
            payload["gateway"] = checkout_data["gateway"]

        # Add coupon if provided
        if checkout_data.get("coupon"):
            payload["coupon"] = checkout_data["coupon"]
        
        try:
            print(f"Sending request to SELLAUTH with data: {json.dumps(payload, indent=2)}")
            response = requests.post(url, json=payload, headers=headers)
            print(f"SELLAUTH Response Status: {response.status_code}")
            print(f"SELLAUTH Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    invoice_id = data.get('invoice_id')
                    if invoice_id:
                        self.active_invoices[invoice_id] = user_id
                        
                        # If it's a crypto payment, get the invoice details
                        if checkout_data.get("gateway") == "CRYPTO":
                            invoice_response = requests.get(
                                f"{SELLAUTH_API_BASE}/shops/{SHOP_ID}/invoices/{invoice_id}",
                                headers=headers
                            )
                            if invoice_response.status_code == 200:
                                invoice_data = invoice_response.json()
                                return {
                                    "url": data.get("invoice_url") or data.get("url"),
                                    "gateway": "LTC",  # Using LTC as specified in docs
                                    "crypto_address": invoice_data.get("crypto_address"),
                                    "crypto_amount": invoice_data.get("crypto_amount"),
                                    "currency": "LTC",  # Explicitly set currency
                                    "price_usd": invoice_data.get("price_usd")
                                }
                        
                    return {
                        "url": data.get("invoice_url") or data.get("url"),
                        "gateway": checkout_data.get("gateway")
                    }
            return None
        except Exception as e:
            print(f"SELLAUTH Request Error: {e}")
            print(f"Full error details: {e.__class__.__name__}: {str(e)}")
            return None

    @tasks.loop(seconds=30)
    async def check_invoices(self):
        """Check SELLAUTH for completed invoices"""
        async with aiohttp.ClientSession() as session:
            url = "https://api.sellauth.app/v1/fetchInvoices"
            headers = {
                "Authorization": f"Bearer {SELLAUTH_API_KEY}"
            }
            payload = {
                "password": SELLAUTH_PASSWORD,
                "status": "completed"
            }
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    invoices = await response.json()
                    
                    for invoice in invoices:
                        invoice_id = invoice['id']
                        
                        # Skip if we've already processed this invoice
                        if invoice_id in self.active_invoices:
                            continue
                            
                        user_id = invoice['userId']
                        try:
                            user = await self.fetch_user(int(user_id))
                            if user:
                                # Record subscription in database
                                self.db.add_subscription(
                                    discord_id=user_id,
                                    discord_name=user.name,
                                    invoice_id=invoice_id
                                )
                                
                                # Send thank you message
                                await self.send_thank_you(user, invoice_id)
                                
                                # Mark as processed
                                self.active_invoices[invoice_id] = True
                                
                        except Exception as e:
                            print(f"Error processing invoice {invoice_id}: {e}")

    @tasks.loop(hours=12)
    async def check_expiring_subs(self):
        """Check for subscriptions expiring in 2 days"""
        expiring = self.db.get_expiring_subscriptions()
        for discord_id, discord_name, expiry_date in expiring:
            try:
                user = await self.fetch_user(int(discord_id))
                if user:
                    await self.send_expiry_notice(user, expiry_date)
                    self.db.mark_notification_sent(discord_id)
            except Exception as e:
                print(f"Error sending expiry notice to {discord_id}: {e}")

    async def send_thank_you(self, user: discord.User, invoice_id: str):
        """Send thank you message to user"""
        embed = discord.Embed(
            title="🎉 Thank You For Your Purchase!",
            description=(
                "Your purchase has been completed successfully!\n\n"
                "We would greatly appreciate if you could leave a review - "
                "it helps us grow and provide better service to our community! 🙏"
            ),
            color=discord.Color.green()
        )
        await user.send(embed=embed)

    async def send_expiry_notice(self, user: discord.User, expiry_date: datetime):
        """Send expiry notice to user"""
        embed = discord.Embed(
            title="⚠️ Subscription Expiring Soon",
            description=(
                "Your AUTOPLAY subscription is expiring in 2 days!\n\n"
                "To keep your benefits, please renew using `/buy`."
            ),
            color=discord.Color.yellow()
        )
        embed.add_field(
            name="Expiry Date",
            value=f"<t:{int(expiry_date.timestamp())}:F>"
        )
        await user.send(embed=embed)

    @tasks.loop(minutes=5)
    async def cleanup_old_invoices(self):
        """Clean up old invoices that haven't been completed"""
        # Implementation if needed
        pass 

    @tasks.loop(minutes=30)
    async def check_expiring_subscriptions(self):
        """Check for subscriptions expiring in 2 days"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                
                # Get subscriptions expiring in ~2 days that haven't been notified
                cursor.execute("""
                    SELECT discord_id, discord_name, expiry_date 
                    FROM subscriptions 
                    WHERE notified = FALSE 
                    AND expiry_date BETWEEN datetime('now', '+1 day', '+23 hours') 
                    AND datetime('now', '+2 days', '+1 hour')
                """)
                
                expiring_subs = cursor.fetchall()
                
                for discord_id, discord_name, expiry_date in expiring_subs:
                    try:
                        user = await self.fetch_user(int(discord_id))
                        if user:
                            embed = discord.Embed(
                                title="⚠️ Subscription Expiring Soon",
                                description=(
                                    "Your GENERATOR subscription is expiring in 2 days!\n\n"
                                    "To keep your benefits and continue using our GENERATOR, "
                                    "please renew your subscription using `/buy`.\n\n"
                                    "Thank you for being a valued customer! 🙏"
                                ),
                                color=discord.Color.yellow()
                            )
                            embed.add_field(
                                name="Expiry Date",
                                value=f"<t:{int(datetime.datetime.fromisoformat(expiry_date).timestamp())}:F>"
                            )
                            
                            await user.send(embed=embed)
                            
                            # Mark as notified
                            cursor.execute(
                                "UPDATE subscriptions SET notified = TRUE WHERE discord_id = ?",
                                (discord_id,)
                            )
                            conn.commit()
                            
                    except Exception as e:
                        print(f"Error notifying user {discord_id}: {e}")
                        
        except Exception as e:
            print(f"Error checking expiring subscriptions: {e}") 

    @tasks.loop(seconds=30)
    async def check_invoice_status(self):
        """Check status of active invoices every 30 seconds"""
        for invoice_id, user_id in list(self.active_invoices.items()):
            try:
                headers = {
                    "Authorization": f"Bearer {SELLAUTH_API_KEY}",
                    "Accept": "application/json"
                }
                
                response = requests.get(
                    f"{SELLAUTH_API_BASE}/shops/{SHOP_ID}/invoices/{invoice_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    invoice_data = response.json()
                    
                    if invoice_data.get('status') == 'completed':
                        # Get the user
                        user = self.get_user(int(user_id))
                        if user:
                            # Create success embed
                            embed = discord.Embed(
                                title="🎉 Thank You For Your Purchase!",
                                description="Your order has been completed successfully!",
                                color=discord.Color.green(),
                                timestamp=discord.utils.utcnow()
                            )
                            
                            # Get purchase date and calculate renewal date
                            purchase_date = datetime.utcnow()
                            # Check if it's monthly or weekly subscription
                            if "MONTHLY" in invoice_data.get('product', {}).get('name', ''):
                                renewal_date = purchase_date + timedelta(days=30)
                            else:
                                renewal_date = purchase_date + timedelta(days=7)
                            
                            embed.add_field(
                                name="📅 Important Dates",
                                value=(
                                    f"**Purchase Date:** <t:{int(purchase_date.timestamp())}:F>\n"
                                    f"**Renewal Date:** <t:{int(renewal_date.timestamp())}:F>"
                                ),
                                inline=False
                            )
                            
                            embed.add_field(
                                name="📦 Order Details",
                                value=(
                                    f"**Product:** {invoice_data.get('product', {}).get('name', 'Generator')}\n"
                                    f"**Invoice ID:** `{invoice_id}`\n"
                                    f"**Amount Paid:** ${invoice_data.get('price_usd', '0.00')} USD"
                                ),
                                inline=False
                            )
                            
                            embed.add_field(
                                name="❓ Need Help?",
                                value="If you need any assistance, please contact our support team.",
                                inline=False
                            )
                            
                            # Set thumbnail
                            embed.set_thumbnail(url="https://media.discordapp.net/attachments/1237105773138542763/1338023352790683739/logox.png?ex=67aed8da&is=67ad875a&hm=18cd0b58b8ef8b572f1acabb0bfc89674f7d5bfd1a9526af4c0e9248f140bf25&=&format=webp&quality=lossless&width=1024&height=1024")
                            
                            try:
                                await user.send(embed=embed)
                                print(f"Sent success message to user {user.name} ({user.id})")
                                
                                # Add customer role if configured
                                if CUSTOMER_ROLE_ID:
                                    guild = self.get_guild(GUILD_ID)
                                    if guild:
                                        member = guild.get_member(int(user_id))
                                        if member:
                                            role = guild.get_role(CUSTOMER_ROLE_ID)
                                            if role:
                                                await member.add_roles(role)
                                                print(f"Added customer role to {member.name}")
                            except discord.Forbidden:
                                print(f"Could not DM user {user_id}")
                            except Exception as e:
                                print(f"Error sending success message: {e}")
                            
                            # Remove from active invoices
                            del self.active_invoices[invoice_id]
                            
                    elif invoice_data.get('status') == 'cancelled':
                        # Remove cancelled invoices
                        del self.active_invoices[invoice_id]
                
            except Exception as e:
                print(f"Error checking invoice {invoice_id}: {e}")

    @check_invoice_status.before_loop
    async def before_check_invoice_status(self):
        await self.wait_until_ready() 