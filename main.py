import asyncio
from src.bot import ZwiftsBot
from src.config.settings import DISCORD_TOKEN

async def setup():
    bot = ZwiftsBot()
    async with bot:
        await bot.start(DISCORD_TOKEN)

def main():
    try:
        asyncio.run(setup())
    except KeyboardInterrupt:
        print("\nBot shutdown by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()