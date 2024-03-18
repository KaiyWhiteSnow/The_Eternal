from random import randint
from discord.ext import commands


class Minigames(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.hybrid_command(
        name="dice",
        usage="dice <Number of sides>",
        description="Rolls a dice with specified number of sides",
    )
    async def dice(self, ctx: commands.Context, numofsides: int = 6):
        roll: int = randint(0, numofsides)
        await ctx.send(f"The magical dice rolled {roll} for {ctx.author.display_name}")
            

async def setup(bot: commands.Bot):
    await bot.add_cog(Minigames(bot))