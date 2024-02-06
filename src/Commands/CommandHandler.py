from discord.ext import commands
from discord import app_commands
import discord

from Config.config import DiscordConfig

class CommandHandler:
    def __init__(self, client: commands.Bot, tree: app_commands.CommandTree):
        self.client = client
        self.tree = tree
        self.register_commands()

    def register_commands(self):
        
        print(DiscordConfig.getPrefix(), "Initialized commands")
        
        @self.tree.command(name="example", description="example")
        @commands.has_role("The Kaiy")
        async def example(interaction: discord.Interaction):
            await interaction.response.send_message(f"Hello {interaction.user.display_name}")