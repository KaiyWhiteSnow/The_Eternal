import re
from string import ascii_letters as STANDARD_CHARACTERS
from typing import List

import discord
from discord.ext import commands

from ..config.automod_config import BANNED_WORDS
from ..database import get_session
from ..database.models.warning import WarningModel


def remove_non_standard_characters(s: str) -> str:
    return re.sub(f"[^{re.escape(STANDARD_CHARACTERS)}]", "", s)


class AutoModeration(commands.Cog):
    banned_words: List[str]

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.banned_words = [remove_non_standard_characters(i) for i in BANNED_WORDS]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author: discord.Member = message.author
        content: str = message.content
        channel: discord.TextChannel = message.channel
        if self.is_string_blacklisted(content.lower()):
            await message.delete()
            # Warn the sender
            warning = WarningModel(
                author, self.bot.user, "Sending inappropriate messages (Automod)"
            )
            with get_session() as session:
                session.add(warning)
                session.commit()
            await channel.send(
                f"Get automodded idiot {author.mention}", delete_after=5.0
            )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.moderate_nickname(member)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.nick == after.nick:
            return
        await self.moderate_nickname(after)

    async def moderate_nickname(self, member: discord.Member):
        """Checks whether the member's nickname contains a banned word. If it does, renames the user.

        Args:
            member (discord.Member): The member to check
        """
        if member.display_name.lower() in self.banned_words:
            await member.edit(nick="Moderated Nickname")
            # Warn the member
            warning = WarningModel(
                member, self.bot.user, "Inappropriate nickname or username (Automod)"
            )
            with get_session() as session:
                session.add(warning)
                session.commit()

    def is_string_blacklisted(self, s: str) -> bool:
        s = remove_non_standard_characters(s)
        pattern = "|".join(self.banned_words)
        if re.search(pattern, s):
            return True
        return False


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoModeration(bot))
