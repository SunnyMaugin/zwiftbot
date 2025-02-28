from aiohttp import web
import hmac
import hashlib
import json
from datetime import datetime
import discord
from src.config.settings import WEBHOOK_SECRET, GUILD_ID, CUSTOMER_ROLE_ID

class SellAuthWebhook:
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.app.router.add_post('/webhook/sellauth', self.handle_webhook)

    def verify_signature(self, signature: str, body: str) -> bool:
        """Verify the webhook signature from SellAuth"""
        try:
            print(f"Verifying signature: {signature}")
            print(f"Webhook secret: {WEBHOOK_SECRET[:5]}...") # Print first 5 chars for safety
            computed_sig = hmac.new(
                WEBHOOK_SECRET.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            print(f"Computed signature: {computed_sig}")
            return hmac.compare_digest(computed_sig, signature)
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False

    async def handle_dynamic_delivery(self, data: dict) -> str:
        """Handle dynamic delivery webhook event"""
        try:
            # Extract discord_id from customer data
            discord_id = data.get('customer', {}).get('discord_id')
            if discord_id:
                user_id = int(discord_id)
                user = await self.bot.fetch_user(user_id)
                
                if user:
                    # Create and send welcome embed
                    embed = discord.Embed(
                        title="🎉 Welcome to Generator Access!",
                        description="Your purchase has been confirmed and your access is now active.",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )

                    # Add purchase details
                    embed.add_field(
                        name="📦 Order Details",
                        value=(
                            f"**Product:** {data.get('item', {}).get('product', {}).get('name', 'Generator')}\n"
                            f"**Price Paid:** ${data.get('price', '0.00')} {data.get('currency', 'USD')}\n"
                            f"**Order ID:** `{data.get('id', 'N/A')}`"
                        ),
                        inline=False
                    )

                    # Add dates
                    purchase_date = datetime.utcnow()
                    if "MONTHLY" in data.get('item', {}).get('product', {}).get('name', ''):
                        renewal_date = purchase_date.timestamp() + (30 * 24 * 60 * 60)
                    else:
                        renewal_date = purchase_date.timestamp() + (7 * 24 * 60 * 60)

                    embed.add_field(
                        name="📅 Important Dates",
                        value=(
                            f"**Purchase Date:** <t:{int(purchase_date.timestamp())}:F>\n"
                            f"**Renewal Date:** <t:{int(renewal_date)}:F>"
                        ),
                        inline=False
                    )

                    # Add support info
                    embed.add_field(
                        name="❓ Need Help?",
                        value="If you need any assistance, please contact our support team.",
                        inline=False
                    )

                    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1237105773138542763/1338023352790683739/logox.png?ex=67beaada&is=67bd595a&hm=ad826a3a6f7feaa5ac53780b6cff9d7e02e3c33fd966f690da4065ce9bc89b48&=&format=webp&quality=lossless&width=1024&height=1024")

                    await user.send(embed=embed)

                    # Add role if configured
                    if GUILD_ID and CUSTOMER_ROLE_ID:
                        try:
                            guild = self.bot.get_guild(GUILD_ID)
                            if guild:
                                member = await guild.fetch_member(user_id)
                                if member:
                                    role = guild.get_role(CUSTOMER_ROLE_ID)
                                    if role:
                                        await member.add_roles(role)
                        except Exception as e:
                            print(f"Error adding role: {e}")

                    # Return success message
                    return "Welcome message sent and role assigned successfully"

            return "No Discord ID found or invalid"

        except Exception as e:
            print(f"Error in dynamic delivery: {e}")
            return f"Error processing delivery: {str(e)}"

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming webhook from SellAuth"""
        try:
            print("\n=== New Webhook Request ===")
            print(f"Headers: {dict(request.headers)}")
            
            # Get signature from headers - check multiple possible header names
            signature = (
                request.headers.get('X-Sellauth-Signature') or
                request.headers.get('x-sellauth-signature') or
                request.headers.get('X-Signature') or
                request.headers.get('x-signature')
            )
            
            if not signature:
                print("No signature found in headers. Available headers:", dict(request.headers))
                return web.Response(status=401, text="No signature provided")

            # Read body
            body = await request.text()
            print(f"Request body: {body}")

            # Verify signature
            if not self.verify_signature(signature, body):
                print("Signature verification failed")
                print(f"Received signature: {signature}")
                return web.Response(status=401, text="Invalid signature")

            # Parse webhook data
            data = json.loads(body)
            print(f"Parsed data: {json.dumps(data, indent=2)}")
            
            # Check for completed status
            if data.get('status') == 'completed':
                discord_id = (
                    data.get('discord_user_id') or 
                    data.get('customer', {}).get('discord_id') or
                    data.get('discord_id')
                )
                
                if discord_id:
                    print(f"Found Discord ID: {discord_id}")
                    success = await self.send_purchase_confirmation(discord_id, data)
                    if success:
                        return web.Response(text="Purchase confirmation sent successfully")
                    else:
                        return web.Response(text="Failed to send purchase confirmation")
                else:
                    print("No Discord ID found in webhook data")
            
            return web.Response(text="Webhook processed")

        except Exception as e:
            print(f"Webhook error: {e}")
            import traceback
            print(traceback.format_exc())
            return web.Response(status=500, text=f"Internal server error: {str(e)}")

    async def start(self):
        """Start the webhook server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        print(f"""
=== Webhook Server Started ===
URL: http://localhost:8080/webhook/sellauth
Webhook Secret: {WEBHOOK_SECRET[:5]}... (first 5 chars)
Listening for requests...
""")

    async def send_purchase_confirmation(self, user_id: str, data: dict) -> bool:
        """Send purchase confirmation DM to user"""
        try:
            print(f"Attempting to send DM to user {user_id}")
            user = await self.bot.fetch_user(int(user_id))
            
            if user:
                embed = discord.Embed(
                    title="🎉 Purchase Confirmed!",
                    description="Thank you for your purchase! Your order has been completed successfully.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )

                # Add purchase details
                product_name = data.get('item', {}).get('product', {}).get('name', 'Generator')
                embed.add_field(
                    name="📦 Order Details",
                    value=(
                        f"**Product:** {product_name}\n"
                        f"**Price:** ${data.get('price', '0.00')} {data.get('currency', 'USD')}\n"
                        f"**Order ID:** `{data.get('id', 'N/A')}`\n"
                        f"**Payment Method:** {data.get('gateway', 'N/A')}"
                    ),
                    inline=False
                )

                # Add dates
                purchase_date = datetime.utcnow()
                if "MONTHLY" in product_name.upper():
                    renewal_date = purchase_date.timestamp() + (30 * 24 * 60 * 60)  # 30 days
                else:
                    renewal_date = purchase_date.timestamp() + (7 * 24 * 60 * 60)  # 7 days

                embed.add_field(
                    name="📅 Important Dates",
                    value=(
                        f"**Purchase Date:** <t:{int(purchase_date.timestamp())}:F>\n"
                        f"**Renewal Date:** <t:{int(renewal_date)}:F>"
                    ),
                    inline=False
                )

                embed.add_field(
                    name="❓ Need Help?",
                    value="If you need any assistance, please contact our support team.",
                    inline=False
                )

                embed.set_thumbnail(url="https://media.discordapp.net/attachments/1253797403157331978/1326286397182840832/PFP.gif")

                await user.send(embed=embed)
                print(f"Successfully sent DM to user {user_id}")

                # Add role if configured
                if GUILD_ID and CUSTOMER_ROLE_ID:
                    try:
                        guild = self.bot.get_guild(GUILD_ID)
                        if guild:
                            member = await guild.fetch_member(int(user_id))
                            if member:
                                role = guild.get_role(CUSTOMER_ROLE_ID)
                                if role:
                                    await member.add_roles(role)
                                    print(f"Added role to user {user_id}")
                    except Exception as e:
                        print(f"Error adding role: {e}")

                return True
            else:
                print(f"Could not find user with ID {user_id}")
                return False

        except Exception as e:
            print(f"Error sending purchase confirmation: {e}")
            return False 