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
                .order_by(desc(WarningModel.time)) # type: ignore
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


async def setup(bot: commands.Bot):
    await bot.add_cog(All(bot))
