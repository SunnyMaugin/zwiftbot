import discord
from discord.ui import Button, View
import time

class ProductDelivery:
    """Handles product delivery and messaging"""
    
    def __init__(self, bot: discord.Client, key_manager):
        self.bot = bot
        self.key_manager = key_manager
        self.ICON_URL = "https://media.discordapp.net/attachments/1237105773138542763/1338023352790683739/logox.png?ex=67ad875a&is=67ac35da&hm=54647bdf1b78af6b677a6b0b214fd49e3d4f80918d5e3e132c3e5f2f76c6ee37&=&format=webp&quality=lossless&width=1024&height=1024"

    async def create_delivery_embed(self, product_key: str, invoice_id: str) -> discord.Embed:
        """Create a beautifully formatted delivery embed"""
        
        embed = discord.Embed(
            title="🌟 Thank You For Your Purchase!",
            description=(
                "Your GENERATOR license has been activated successfully.\n"
                "Below you'll find your product key and important information."
            ),
            color=0x2b2d31  # Discord dark theme color
        )

        # Add product key section
        embed.add_field(
            name="🔑 License Key",
            value=(
                "```yaml\n"
                f"{product_key}\n"
                "```"
                "*Click 'Copy Key' below to copy your license key*"
            ),
            inline=False
        )

        # Add product details section
        embed.add_field(
            name="📦 Product Details",
            value=(
                "**Product:** AUTOPLAY\n"
                "**Duration:** 30 Days\n"
                "**Status:** ✅ Active\n"
                "**Activation:** Instant"
            ),
            inline=True
        )

        # Add important information
        embed.add_field(
            name="📋 Important Information",
            value=(
                "• Important Information\n"
                "• Important Information\n"
                "• Important Information\n"
                "• 24/7 Support available"
            ),
            inline=False
        )

        # Add quick links
        embed.add_field(
            name="🔗 Quick Links",
            value=(
                "[Installation Guide](https://autoplay-guide.gitbook.io/full-autoplay-guide)\n"
                "[Support Server](https://discord.gg/zwiftresells)\n"
                "[Terms of Service](https://cheapcodservices.com/terms)"
            ),
            inline=False
        )

        # Add purchase details footer
        embed.add_field(
            name="🧾 Purchase Details",
            value=(
                f"**Invoice ID:** `{invoice_id}`\n"
                f"**Purchase Date:** <t:{int(time.time())}:F>\n"
                f"**Next Renewal:** <t:{int(time.time()) + (30 * 24 * 60 * 60)}:F>"
            ),
            inline=False
        )

        # Set footer with animated icon
        embed.set_footer(
            text="Zwift Support • Thank you for your purchase!",
            icon_url=self.ICON_URL
        )

        # Set animated thumbnail
        embed.set_thumbnail(url=self.ICON_URL)

        # Set timestamp
        embed.timestamp = discord.utils.utcnow()

        return embed

    def create_delivery_view(self, invoice_id: str, product_key: str) -> View:
        """Create the delivery view with enhanced buttons"""
        view = discord.ui.View(timeout=None)  # Buttons never expire
        
        # Support Guide Button
        view.add_item(Button(
            style=discord.ButtonStyle.link,
            label="Installation Guide",
            emoji="📚",
            url="https://autoplay-guide.gitbook.io/full-autoplay-guide"
        ))

        # Support Server Button
        view.add_item(Button(
            style=discord.ButtonStyle.link,
            label="Support Server",
            emoji="🛟",
            url="https://discord.gg/zwiftresells"
        ))
        
        self.key_manager.button_keys[f"copy_{invoice_id}"] = product_key
        return view 

    async def send_success_message(self, user: discord.User, invoice_id: str):
        embed = discord.Embed(
            title="�� Thank You For Your Purchase!",
            description=(
                "Your purchase has been completed successfully!\n\n"
                "We would greatly appreciate if you could leave a review - "
                "it helps us grow and provide better service to our community! 🙏\n\n"
                "You can leave a review in our server: discord.gg/zwiftresells"
            ),
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📋 Order Details",
            value=f"Invoice ID: `{invoice_id}`",
            inline=False
        )
        
        await user.send(embed=embed) 