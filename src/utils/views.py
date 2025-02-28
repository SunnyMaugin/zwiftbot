import discord
from discord.ui import Select, View, Button
from src.config.constants import EMOJIS, SELLAPP_API_KEY
import aiohttp

class VariantSelect(discord.ui.Select):
    def __init__(self, variants: dict):
        options = []
        for variant_id, variant_data in variants.items():
            option = discord.SelectOption(
                label=f"{variant_data['name']} (${variant_data['amount']})",
                description=variant_data['description'][:100],
                emoji=variant_data['emoji'],
                value=variant_data['id']
            )
            options.append(option)
        
        super().__init__(
            placeholder="Choose your subscription plan",
            min_values=1,
            max_values=1,
            options=options
        )
        self.variants = variants

    async def callback(self, interaction: discord.Interaction):
        variant_id = self.values[0]
        selected_variant = next(v for v in self.variants.values() if v['id'] == variant_id)
        
        # Create an enhanced embed for variant details
        embed = discord.Embed(
            title=f"{selected_variant['emoji']} {selected_variant['name']}",
            description=(
                "**AUTOPLAY - The Ultimate AFK Experience**\n\n"
                "Transform your gaming experience with AUTOPLAY, the most advanced "
                "and reliable AFK solution available. Designed for maximum efficiency "
                "and safety.\n\n"
                f"🎮 **Selected Plan:** {selected_variant['name']}\n"
                f"💰 **Price:** ${selected_variant['amount']} USD"
            ),
            color=discord.Color.brand_green()
        )
        
        # Add key features
        embed.add_field(
            name="🌟 Key Features",
            value=(
                "• Advanced Anti-Detection System\n"
                "• 24/7 Automated Operation\n"
                "• Customizable AFK Settings\n"
                "• Real-time Status Monitoring\n"
                "• Performance Optimization"
            ),
            inline=True
        )
        
        # Add included benefits
        embed.add_field(
            name="✨ Included Benefits",
            value="\n".join(f"• {perk}" for perk in selected_variant['perks']),
            inline=True
        )
        
        # Add technical specifications
        embed.add_field(
            name="⚙️ Technical Specs",
            value=(
                "• Instant Activation\n"
                "• HWID Protection\n"
                "• Auto-Updates\n"
                "• Priority Support Access\n"
                "• Performance Analytics"
            ),
            inline=False
        )
        
        # Add subscription details
        embed.add_field(
            name="📋 Subscription Details",
            value=(
                f"• Duration: {selected_variant['name'].split('[')[1].split(']')[0]}\n"
                f"• Billing: One-time payment\n"
                f"• Activation: Instant upon payment\n"
                "• Renewal: Manual"
            ),
            inline=True
        )
        
        # Add support information
        embed.add_field(
            name="🛟 Support",
            value=(
                "• 24/7 Discord Support\n"
                "• Installation Guide\n"
                "• Video Tutorials\n"
                "• FAQ Access"
            ),
            inline=True
        )
        
        
        # Set footer
        embed.set_footer(
            text="Select your plan and click 'Confirm Selection' to proceed with purchase",
            icon_url="https://media.discordapp.net/attachments/1253797403157331978/1326286397182840832/PFP.gif"
        )
        
        # Set thumbnail
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1253797403157331978/1326286397182840832/PFP.gif")
        
        # Update the message with the variant details
        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=self.view
        )
        self.view.selected_variant = variant_id

class VariantButton(Button):
    def __init__(self, variant_id: str, name: str, price: float):
        super().__init__(
            label=f"{name} - ${price:.2f}",
            style=discord.ButtonStyle.primary,
            custom_id=f"variant_{variant_id}"
        )
        self.variant_id = variant_id
        self.price = price

    async def callback(self, interaction: discord.Interaction):
        # Create payment link through SellApp API
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {SELLAPP_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "title": "AUTOPLAY Subscription",
                "price": self.price,
                "currency": "USD",
                "custom_fields": {
                    "discord_id": str(interaction.user.id),
                    "discord_name": interaction.user.name,
                    "variant_id": self.variant_id
                }
            }
            
            async with session.post("https://sell.app/api/v1/payments/create", 
                                  headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    payment_url = data['url']
                    
                    # Create payment button
                    payment_view = View()
                    payment_view.add_item(
                        Button(
                            label="Complete Payment",
                            url=payment_url,
                            style=discord.ButtonStyle.link
                        )
                    )
                    
                    await interaction.response.edit_message(
                        content="Click below to complete your purchase:",
                        view=payment_view
                    )
                else:
                    await interaction.response.edit_message(
                        content="Sorry, there was an error creating your payment link. Please try again later.",
                        view=None
                    )

class VariantView(View):
    def __init__(self, variants: dict):
        super().__init__()
        for variant_id, variant_data in variants.items():
            self.add_item(
                VariantButton(
                    variant_id=variant_id,
                    name=variant_data["name"],
                    price=variant_data["price"]
                )
            ) 