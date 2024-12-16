import logging

from decouple import config

CACHE_DIR: str = config("BOT_CACHE_DIR", None)
if CACHE_DIR is None:
    CACHE_DIR = "./cache"
