import discord
from discord.ext import commands
import os


class Clans(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.hybrid_command(
        name="createclan",
        usage="createclan <clan Name>",
        description="Creates roles and channels for specified clan",
    )
    async def createclan(self, ctx: commands.Context, clan: str):
        # Create category
        category = await ctx.guild.create_category(f"==={clan}===") # type: ignore

        # Deny all roles access to the category
        await category.set_permissions(ctx.guild.default_role, read_messages=False, connect=False) # type: ignore

        # Create roles and give access to the category
        role = await ctx.guild.create_role(name=f"{clan}_role") # type: ignore
        leader_role = await ctx.guild.create_role(name=f"{clan}_leader_role")  # type: ignore
        await category.set_permissions(role, read_messages=True, connect=True)
        await category.set_permissions(leader_role, read_messages=True, connect=True)  # Give leader role access

        coleader_role = await ctx.guild.create_role(name=f"{clan}_coleader_role") # type: ignore
        await category.set_permissions(coleader_role, read_messages=True, connect=True)  # Give co-leader role access       

        # Assign the leader role to the person who initiated the command
        await ctx.author.add_roles(leader_role) # type: ignore

        await ctx.channel.send(f"Creating channels for: {clan}")

        # Create text and voice channels within the category
        await ctx.guild.create_text_channel(f"{clan}-general", category=category) # type: ignore
        await ctx.guild.create_text_channel(f"{clan}-config", category=category) # type: ignore
        await ctx.guild.create_text_channel(f"{clan}-bases", category=category) # type: ignore
        await ctx.guild.create_voice_channel(f"{clan} voice", category=category) # type: ignore

        await ctx.channel.send(f"Channels created for: {clan}")


    @commands.hybrid_command(
        name="removeclan",
        usage="removeclan <Team Name>",
        description="Removes roles, channels, and category for the specified team",
    )
    async def removeclan(self, ctx: commands.Context, clan: str):
        if category := discord.utils.get(
            ctx.guild.categories, name=f"==={clan}===" # type: ignore
        ):
            # Delete channels within the category
            for channel in category.channels:
                await channel.delete()

            # Delete roles associated with the clan
            for role in ctx.guild.roles: # type: ignore
                if role.name.startswith(clan):
                    await role.delete()

            # Delete the category
            await category.delete()

            await ctx.send(f"Clan {clan} removed, including roles.")
        else:
            await ctx.send(f"Clan {clan} not found.")

        "--------------------------------------"    
        """ Clans related commands end here! """
        "--------------------------------------"

    @commands.hybrid_command(
        name="addcoleader",
        usage="/addcoleader <member object>",
        description="Adds a coleader to your clan"
    )
    async def add_coleader(self, ctx: commands.Context, member: discord.Member):
        # Check if the command invoker has the required role
        clan_leader_role = next((role for role in ctx.author.roles if role.name.endswith("_leader_role")), None) # type: ignore
        
        if clan_leader_role is None:
            await ctx.send("You do not have the required leader role.")
            return
        
        # Extract clan name from the leader's role name
        clan_name = clan_leader_role.name.split("_")[0]
        
        coleader_role_name = f"{clan_name}_coleader_role"
        coleader_role = discord.utils.get(ctx.guild.roles, name=coleader_role_name) # type: ignore
        
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
        
        clan_leader_role = next((role for role in ctx.author.roles if role.name.endswith("_leader_role") or role.name.endswith("_coleader_role")), None) # type: ignore

        if clan_leader_role is None:
            await ctx.send("You do not have the required leader role.")
            return
        # Extract clan name from the leader's role name
        clan_name = clan_leader_role.name.split("_")[0]
        
        role_name = f"{clan_name}_role"
        clan_role = discord.utils.get(ctx.guild.roles, name=role_name) # type: ignore
        
        await member.add_roles(clan_role) # type: ignore


async def setup(bot: commands.Bot):
    await bot.add_cog(Clans(bot))
    