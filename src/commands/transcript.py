import discord
from discord.ext import commands
import os
from ..config.transcript_config import createHeader


class Transcripts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.out_dir = os.path.join(os.path.dirname(__file__), 'out')
    
    def escape_html(self, text):
        """
        Escapes special characters in the given text to prevent Markdown and mentions from being interpreted in Discord.

        Parameters:
            - text (str): The text to be escaped.

        Returns:
            str: The escaped text.
        """
        return discord.utils.escape_markdown(discord.utils.escape_mentions(text))

    def escape_attachments(self, attachments):
        """
        Escapes the URLs of attachments for embedding in Discord messages.

        Parameters:
            - attachments (list): A list of attachments, where each attachment is an object with a 'url' attribute.

        Returns:
            str: A string containing HTML img tags for each attachment, with escaped URLs and styling.
                If no attachments are provided, an empty string is returned.
        """
        if not attachments:
            return ""

        attachment_list = [
            f'<img src="{discord.utils.escape_markdown(attachment.url)}" style="max-width: 800px; max-height: 600px; margin: 5px" alt="Attachment">'
            for attachment in attachments
        ]
        return " ".join(attachment_list)
    
    async def removeHTML(self, user: discord.User):
        # Get a list of HTML files in the 'out' directory
        html_files = [file for file in os.listdir(self.out_dir) if file.endswith('.html')]

        # Check if there are HTML files in the 'out' directory
        if not html_files:
            raise "Error: No HTML files found in 'out' directory." # type: ignore

        try:
            # Send each HTML file
            for html_file in html_files:
                html_file_path = os.path.join(self.out_dir, html_file)
                await user.send(file=discord.File(html_file_path))

            print(f"Transcripts sent to {user.name}")
        except discord.errors.Forbidden:
            print("Error: Unable to send files to the specified user. Make sure the user allows direct messages.")
            
        for file_name in html_files:
            try:
                os.remove(os.path.join(self.out_dir, file_name))
                print(f"File {file_name} removed successfully.")
            except FileNotFoundError:
                print(f"File {file_name} not found.")
            except Exception as e:
                print(f"Error removing file {file_name}: {e}")


    @commands.hybrid_command(
        name="transcriptchannel", 
        usage="/transcriptchannel <channel name>", 
        description="creates transcript for a channel",
    )
    async def transcriptchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        with open(os.path.join(self.out_dir, f"{channel.name}.html"), "w", encoding="utf-8") as file:
            file.write(
                await createHeader(channel.name)
            )
            messages = []
            async for message in channel.history(limit=None):
                
                content = self.escape_html(message.content)
                attachments = self.escape_attachments(message.attachments)
                
                pfp = message.author.display_avatar
                color = message.author.color
                messages.append((pfp, color, message.author.name, content, attachments))
                
                # Write messages to HTML file in reverse order
            for msg in reversed(messages):
                pfp, color, author_name, content, attachments = msg
                file.write(f'<div><img src="{pfp}" style="max-width: 40px; max-height: 40px; border-radius: 50%;"> <strong><a style="color: {color}">{author_name}</a>:</strong> {content}</div>')
                file.write(f'<div>{attachments}</div>')
                    
        await self.removeHTML(ctx.author) # type: ignore
    
    
    @commands.hybrid_command(
        name="transcriptthread", 
        usage="/transcriptthread <channel name>", 
        description="creates transcript for a channel",
    ) 
    async def transcriptthread(self, ctx: commands.Context, thread: discord.Thread):
        with open(os.path.join(self.out_dir, f"{thread.name}.html"), "w", encoding="utf-8") as file:
            # Creating head tag
            file.write(
                await createHeader(thread.name)
            )
            # Thread ID and Name
            file.write(f"Thread ID: {thread.id}, Name: {thread.name}")
            messages = []
            async for message in thread.history(limit=None):
                content = self.escape_html(message.content)
                attachments = self.escape_attachments(message.attachments)
                pfp = message.author.display_avatar
                color = message.author.color
                messages.append((pfp, color, message.author.name, content, attachments))

            # Write messages to HTML file in reverse order
            for msg in reversed(messages):
                pfp, color, author_name, content, attachments = msg
                file.write(f'<div><img src="{pfp}" style="max-width: 40px; max-height: 40px; border-radius: 50%;"> <strong><a style="color: {color}">{author_name}</a>:</strong> {content}</div>')
                file.write(f'<div>{attachments}</div>')

        await self.removeHTML(ctx.author) # type: ignore
        
        
    @commands.hybrid_command(
        name="transcriptthreads", 
        usage="/transcriptthreads <channel name>", 
        description="creates transcripts for all threads in a channel",
    )
    async def transcriptthreads(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Creates transcripts for a given channel.

        Args:
            ctx (commands.Context): The context of the command.
            channel (discord.TextChannel): The channel for which to create transcripts.

        Returns:
            None

        Examples:
            # Create transcripts for a channel
            /transcriptChannel #general
        """
        threads = channel.archived_threads()

        async for thread in threads:
            with open(os.path.join(self.out_dir, f"{thread.name}.html"), "w", encoding="utf-8") as file:
                # Creating head tag
                file.write(
                    await createHeader(thread.name)
                )
                messages = []
                # Thread ID and Name
                file.write(f"Thread ID: {thread.id}, Name: {thread.name}")
                async for message in thread.history(limit=None):
                    content = self.escape_html(message.content)
                    attachments = self.escape_attachments(message.attachments)
                    pfp = message.author.display_avatar
                    color = message.author.color
                    messages.append((pfp, color, message.author.name, content, attachments))

                # Write messages to HTML file in reverse order
                for msg in reversed(messages):
                    pfp, color, author_name, content, attachments = msg
                    file.write(f'<div><img src="{pfp}" style="max-width: 40px; max-height: 40px; border-radius: 50%;"> <strong><a style="color: {color}">{author_name}</a>:</strong> {content}</div>')
                    file.write(f'<div>{attachments}</div>')

        await self.removeHTML(ctx.author) # type: ignore
        
async def setup(bot: commands.Bot):
    await bot.add_cog(Transcripts(bot))