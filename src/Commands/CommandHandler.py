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

        @self.tree.command(name="syncdatabase", description="Manually synchronizes database with all users")
        @commands.has_role("The Kaiy")
        async def syncDatabaseManually(interaction: discord.Interaction):
            from Main import session_instance, client
            from Database.Database import Database
            guild = interaction.guild

            members = [m async for m in guild.fetch_members()]
            
            await Database.syncDatabase(session_instance, members)
            await interaction.response.send_message("Database synchronized successfully.")
    