from typing import List

import discord
from discord.ext import commands
from sqlalchemy import desc, func

from ..database import get_session
from ..database.models.warning import WarningModel


class All(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="warnings",
        usage="warnings <member>",
        description="Shows all warnings for the specified user",
    )
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        warnings: List[WarningModel] = []
        warnings_text: List[str] = ["none :)"]
        with get_session() as session:
            warnings = (
                session.query(WarningModel)
                .filter_by(memberId=member.id)
                .order_by(desc(WarningModel.time))
                .limit(50)
                .all()
            )
            warning_count = (
                session.query(func.count(WarningModel.warningId))
                .filter_by(memberId=member.id)
                .scalar()
            )
            if len(warnings) > 0:
                warnings_text: List[str] = [
                    f"<t:{round(warning.time.timestamp())}> {warning.reason}"
                    for warning in warnings
                ]
        # TODO: If a member has way too many warnings, we might need to handle messages longer than 2000 chars by sending multiple messages.
        # The terrible ternary will add "(showing at most 50 latest)" to the message if the user has more than 50 warnings
        await ctx.send(
            f"{member.mention} has {warning_count} total warnings{' (showing at most 50 latest)' if warning_count > 50 else ''}: \n- "
            + "\n- ".join(warnings_text),
            ephemeral=True,
        )
    @commands.hybrid_command(
        name="createclan",
        usage="createclan <clan Name>",
        description="Creates roles and channels for specified clan",
    )
    async def createclan(self, ctx: commands.Context, clan: str):
        # Create category
        category = await ctx.guild.create_category("==="+clan+"===")

        # Deny all roles access to the category
        await category.set_permissions(ctx.guild.default_role, read_messages=False, connect=False)

        # Create roles and give access to the category
        role = await ctx.guild.create_role(name=f"{clan}_role")
        await category.set_permissions(role, read_messages=True, connect=True)

        await ctx.channel.send(f"Creating channels for: {clan}")

        # Create text and voice channels within the category
        await ctx.guild.create_text_channel(clan+"-general", category=category)
        await ctx.guild.create_text_channel(clan+"-config", category=category)
        await ctx.guild.create_text_channel(clan+"-bases", category=category)
        await ctx.guild.create_voice_channel(clan+" voice", category=category)

        await ctx.channel.send(f"Channels created for: {clan}")
        
    @commands.hybrid_command(
        name="removeclan",
        usage="removeclan <Team Name>",
        description="Removes roles, channels, and category for the specified team",
    )
    async def removeclan(self, ctx: commands.Context, clan: str):
        # Find the category associated with the clan
        category = discord.utils.get(ctx.guild.categories, name="==="+clan+"===")

        if category:
            # Delete channels within the category
            for channel in category.channels:
                await channel.delete()

            # Delete the category
            await category.delete()
            
            await ctx.send(f"Clan {clan} removed.")
        else:
            await ctx.send(f"Clan {clan} not found.")



async def setup(bot: commands.Bot):
    await bot.add_cog(All(bot))
