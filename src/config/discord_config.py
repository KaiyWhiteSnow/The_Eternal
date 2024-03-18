from decouple import config

BOT_TOKEN: str = config("eternal_token", None) # type: ignore
if BOT_TOKEN is None:
    raise RuntimeError("No token specified!")
if BOT_TOKEN == "bot.token.here" or BOT_TOKEN.count(".") != 2:
    raise RuntimeError("Invalid token specified!")

BOT_PREFIX: str = config("eternal_prefix", "!") # type: ignore
