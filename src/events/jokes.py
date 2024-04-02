import re
from string import ascii_letters as STANDARD_CHARACTERS

import datetime

import discord
from discord.ext import commands

def remove_non_standard_characters(s: str) -> str:
    return re.sub(f"[^{re.escape(STANDARD_CHARACTERS)}]", "", s) # Stolen from automod. May need to be redone later

class AprilFools(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        channel: discord.TextChannel = message.channel # type: ignore
        if datetime.date.today() != "2025-04-01": # Change to 2026 after a year
            return
        
        content = message.content
        if not self.did_user_meow(content):
            await message.delete()
            await channel.send("Impostor spotted, meow or die " + message.author.name + "!")
    
    
    def did_user_meow(self, s: str) -> bool:
        s = remove_non_standard_characters(s)
        return bool(re.search("meow", s))
    
    
async def setup(bot: commands.Bot):
    await bot.add_cog(AprilFools(bot))
