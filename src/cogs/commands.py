import discord
from discord import app_commands
from discord.ext import commands
from src.config.constants import PRODUCTS, PAYMENT_METHODS, EMOJIS
from src.bot import ZwiftsBot
import json
import re

class InitialPurchaseModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Purchase Details")
        
        self.email = discord.ui.TextInput(
            label="Email Address",
            placeholder="your@email.com",
            required=True,
            min_length=5,
            max_length=100
        )
        self.add_item(self.email)
        
        self.coupon = discord.ui.TextInput(
            label="Coupon Code (Optional)",
            placeholder="Leave empty if none",
            required=False,
            max_length=50
        )
        self.add_item(self.coupon)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validate email
            if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email.value):
                await interaction.response.send_message(
                    "❌ Please enter a valid email address.",
                    ephemeral=True
                )
                return

            # Create embed
            embed = discord.Embed(
                title="🛒 Purchase Generator Access",
                description="Please select your payment method below.",
                color=discord.Color.blue()
            )

            # Add order details
            embed.add_field(
                name="Order Details",
                value=(
                    f"**Email:** {self.email.value}\n"
                    f"**Coupon:** {self.coupon.value if self.coupon.value else 'None'}"
                ),
                inline=False
            )

            # Create view with payment options
            view = PurchaseView(
                product_name="GENERATOR",
                email=self.email.value,
                coupon=self.coupon.value if self.coupon.value else None
            )

            # Send response
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in modal submission: {str(e)}")
            # If we haven't sent a response yet, send an error message
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred. Please try again.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ An error occurred. Please try again.",
                    ephemeral=True
                )

class PaymentLinkView(discord.ui.View):
    def __init__(self, url: str):
        super().__init__()
        self.add_item(discord.ui.Button(
            label="Click Here to Pay", 
            url=url, 
            style=discord.ButtonStyle.link
        ))

class PurchaseView(discord.ui.View):
    def __init__(self, product_name: str, email: str, coupon: str = None):
        super().__init__()
        self.product_name = product_name
        self.email = email
        self.coupon = coupon

    @discord.ui.select(
        placeholder="Choose your payment method",
        options=[
            discord.SelectOption(
                label="Credit/Debit Card",
                value="STRIPE",
                emoji="💳"
            ),
            discord.SelectOption(
                label="Cryptocurrency",
                value="LTC",
                emoji="🪙"
            ),
            discord.SelectOption(
                label="CashApp",
                value="CASHAPP",
                emoji="💵"
            ),
            discord.SelectOption(
                label="PayPal",
                value="PAYPAL",
                emoji="💰"
            )
        ]
    )
    async def payment_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Handle payment method selection"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            payment_method = PAYMENT_METHODS[select.values[0]]
            variant_data = PRODUCTS[self.product_name]["variants"]["MONTHLY"]
            
            checkout_data = {
                "cart": [{
                    "productId": PRODUCTS[self.product_name]["id"],
                    "variantId": variant_data["id"],
                    "quantity": 1
                }],
                "gateway": payment_method["gateway"],
                "email": self.email
            }

            if self.coupon:
                checkout_data["coupon"] = self.coupon

            invoice = await interaction.client.create_sellauth_invoice(
                user_id=str(interaction.user.id),
                product_id=PRODUCTS[self.product_name]["id"],
                checkout_data=checkout_data
            )

            if invoice:
                if payment_method["gateway"] == "LTC":
                    embed = discord.Embed(
                        title="🪙 Crypto Payment Details",
                        description="Please complete your payment using the button below.",
                        color=discord.Color.gold()
                    )
                elif payment_method["gateway"] == "PAYPAL":
                    embed = discord.Embed(
                        title="💰 PayPal Payment Instructions",
                        description=(
                            "Please follow these steps to complete your PayPal payment:\n\n"
                            "1️⃣ Open PayPal and click 'Send'\n"
                            "2️⃣ Enter our PayPal email: `zwiftservices@outlook.com`\n"
                            "3️⃣ Send the exact amount: `$" + str(variant_data['amount']) + "`\n"
                            "4️⃣ Add your Discord ID in the note: `" + str(interaction.user.id) + "`\n"
                            "5️⃣ Take a screenshot of the completed payment\n"
                            "6️⃣ Send the screenshot in this DM\n\n"
                            "⚠️ **Important Notes:**\n"
                            "• Send as 'Friends & Family'\n"
                            "• Include your Discord ID in the payment note\n"
                            "• Send the exact amount shown\n"
                            "• Payment will be verified manually"
                        ),
                        color=discord.Color.blue()
                    )

                    embed.add_field(
                        name="Order Details",
                        value=(
                            f"**Product:** {variant_data['name']}\n"
                            f"**Price:** ${variant_data['amount']}\n"
                            f"**Payment Method:** {payment_method['name']}\n"
                            f"**Email:** {self.email}\n"
                            f"**Discord ID:** {interaction.user.id}"
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="Need Help?",
                        value="If you need assistance, please contact our support team.",
                        inline=False
                    )

                    embed.set_footer(text="Please send the payment screenshot in this DM after completing the payment")
                    
                    # No payment button for PayPal manual payments
                    await interaction.edit_original_response(
                        embed=embed,
                        view=None
                    )
                else:
                    embed = discord.Embed(
                        title="🛒 Complete Your Purchase",
                        description="Please complete your payment using the button below.",
                        color=discord.Color.blue()
                    )

                # Create payment button view
                payment_view = PaymentLinkView(invoice['url'])

                await interaction.edit_original_response(
                    embed=embed,
                    view=payment_view
                )
            else:
                await interaction.edit_original_response(
                    content="❌ Error creating payment link. Please try again.",
                    view=None
                )

        except Exception as e:
            print(f"Error in payment_select: {str(e)}")
            try:
                await interaction.edit_original_response(
                    content="❌ An error occurred. Please try again.",
                    view=None
                )
            except:
                await interaction.followup.send(
                    "❌ An error occurred. Please try again.",
                    ephemeral=True
                )

class Commands(commands.Cog):
    def __init__(self, bot: ZwiftsBot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="buy", description="Purchase Generator Access")
    async def buy(self, interaction: discord.Interaction):
        """Start the purchase process"""
        modal = InitialPurchaseModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="sync", description="Sync all slash commands")
    @app_commands.default_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        """Sync all slash commands"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            print("Manually syncing commands...")
            guild = discord.Object(id=interaction.guild_id)
            commands = await self.bot.tree.sync(guild=guild)
            await interaction.followup.send(f"✅ Successfully synced {len(commands)} commands!", ephemeral=True)
            print(f"Manual sync complete! Synced {len(commands)} commands")
        except Exception as e:
            print(f"Sync error: {e}")
            await interaction.followup.send(f"❌ Error syncing commands: {str(e)}", ephemeral=True)

async def setup(bot: ZwiftsBot):
    await bot.add_cog(Commands(bot))
    print("Commands cog loaded")