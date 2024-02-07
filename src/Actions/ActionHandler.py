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
            if Functions.is_message_banned(message, Functions.load_banned_phrases("/home/kaiy/Dokumenty/GitHub/file/The_Eternal/src/Config/banned.txt")):
                await message.delete()

                # Assuming message.author.id is the user's unique identifier
                user_id = message.author.id
                from Main import session_instance

                from Database.Models.UserModel import User
                from Database.Models.WarningModel import CustomWarning
                # Query the user from the database
                user = session_instance.query(User).filter_by(UID=user_id).first()

                # Create a warning for the user
                warning = CustomWarning(UID=user_id, Reason=f"Warned for usage of banned word; {message.content}")

                # Add the warning to the user's warnings
                user.Warnings.append(warning)

                # Commit the changes to the database
                session_instance.commit()

                await message.channel.send(f"Get automoded idiot {message.author.mention}")
