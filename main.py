"""
Entrypoint for launching Dissound (MemeSound Bot).
"""
import sys
import asyncio
from config import DISCORD_TOKEN
from core.bot import DissoundBot
from core.logger import log

def main():
    """Main execution function."""
    if not DISCORD_TOKEN or DISCORD_TOKEN == "your_bot_token_here":
        log.error(
            "DISCORD_TOKEN is missing or not configured in your .env file.\n"
            "Please create a Discord application at https://discord.com/developers/applications\n"
            "and add your Bot Token to .env before starting Dissound."
        )
        sys.exit(1)

    bot = DissoundBot()
    try:
        log.info("Starting Dissound...")
        bot.run(DISCORD_TOKEN, log_handler=None)
    except KeyboardInterrupt:
        log.info("Shutdown requested. Closing Dissound...")
    except Exception as e:
        log.critical(f"Fatal error running Dissound: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
