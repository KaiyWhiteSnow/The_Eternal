import discord
from discord import app_commands

from Database.Database import Session
from Commands.CommandHandler import CommandHandler 
from Actions.ActionHandler import ActionHandler
        
session_instance = Session()
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Initiaize handlers
Command_Handler = CommandHandler(client, tree)
Action_Handler = ActionHandler(client, tree)

@client.event
async def on_ready():
    await client.wait_until_ready()
    await tree.sync()

    prefix = DiscordConfig.getPrefix()
    print(f"{prefix} Initialized all modules")

    
if __name__ == "__main__":
    from Config.config import DiscordConfig
    client.run(DiscordConfig.client_token)
