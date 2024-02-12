from typing import List
from random import randint

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
        leader_role = await ctx.guild.create_role(name=f"{clan}_leader_role")  # New line for leader role
        await category.set_permissions(role, read_messages=True, connect=True)
        await category.set_permissions(leader_role, read_messages=True, connect=True)  # Give leader role access

        coleader_role = await ctx.guild.create_role(name=f"{clan}_coleader_role")
        await category.set_permissions(coleader_role, read_messages=True, connect=True)  # Give co-leader role access       

        # Assign the leader role to the person who initiated the command
        await ctx.author.add_roles(leader_role)

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

            # Delete roles associated with the clan
            for role in ctx.guild.roles:
                if role.name.startswith(clan):
                    await role.delete()

            # Delete the category
            await category.delete()
            
            await ctx.send(f"Clan {clan} removed, including roles.")
        else:
            await ctx.send(f"Clan {clan} not found.")


    @commands.hybrid_command(
        name="dice",
        usage="dice <Number of sides>",
        description="Rolls a dice with specified number of sides",
    )
    async def dice(self, ctx: commands.Context, numofsides: int = 6):
        roll: int = randint(0, numofsides)
        await ctx.send(f"The magical dice rolled {roll} for {ctx.author.display_name}")
    
    @commands.hybrid_command(
        name="addcoleader",
        usage="/addcoleader <member object>",
        description="Adds a coleader to your clan"
    )
    async def add_coleader(self, ctx: commands.Context, member: discord.Member):
        # Check if the command invoker has the required role
        clan_leader_role = next((role for role in ctx.author.roles if role.name.endswith("_leader_role")), None)
        
        if clan_leader_role is None:
            await ctx.send("You do not have the required leader role.")
            return
        
        # Extract clan name from the leader's role name
        clan_name = clan_leader_role.name.split("_")[0]
        
        coleader_role_name = f"{clan_name}_coleader_role"
        coleader_role = discord.utils.get(ctx.guild.roles, name=coleader_role_name)
        
        if coleader_role is None:
            await ctx.send(f"Error: Co-leader role ({coleader_role_name}) not found.")
            return

        # Assign the co-leader role to the specified member
        await member.add_roles(coleader_role)
        
        await ctx.send(f"{member.mention} has been added as a co-leader to the {clan_name} clan.")
                
    
    @commands.hybrid_command(
        name="addmember", 
        usage="/addmember <member name>", 
        description="Adds member to your clan",
    )
    async def addmember(self, ctx: commands.Context, member: discord.Member):
        
        clan_leader_role = next((role for role in ctx.author.roles if role.name.endswith("_leader_role") or role.name.endswith("_coleader_role")), None)

        if clan_leader_role is None:
            await ctx.send("You do not have the required leader role.")
            return
        # Extract clan name from the leader's role name
        clan_name = clan_leader_role.name.split("_")[0]
        
        role_name = f"{clan_name}_role"
        clan_role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        await member.add_roles(clan_role)
        
async def setup(bot: commands.Bot):
    await bot.add_cog(All(bot))
