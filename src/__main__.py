"""The Eternal Runner
This script is only executed when the application is ran directly
When it's imported as a package, this script will not run.
"""
if __name__ == "__main__":
    from . import bot
    from .Config.discord_config import BOT_TOKEN
    bot.run(BOT_TOKEN, log_handler=None)
