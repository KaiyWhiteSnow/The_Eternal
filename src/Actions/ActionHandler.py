from discord.ext import commands
from discord import app_commands
import discord

from Config.config import DiscordConfig
from Config.Functions import Functions

class ActionHandler:
    def __init__(self, client: commands.Bot, tree: app_commands.CommandTree):
        self.client = client
        self.tree = tree
        self.register_Actions()

    def register_Actions(self):
        
        print(DiscordConfig.getPrefix(), "Initialized Actions")
        
        @self.client.event
        async def on_message(message: discord.Message):
            if message.author == message.author.bot:
                return
            if Functions.is_message_banned(message, Functions.load_banned_words("C:/Users/Kaiy/Documents/GitHub/The_Eternal/src/Config/banned.txt")) == True:
                await message.delete()
                await message.channel.send(f"Get automoded idiot {message.author.mention}")
