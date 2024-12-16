from typing import Dict, List

import discord
from discord.ext import commands

from ..services.audiocontroller import AudioController
from ..models.playlist import LoopMode, Playlist
from ..embed_factory import create_embed


class Default(commands.Cog):
    bot: commands.Bot
    controllers: Dict[int, AudioController]

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.controllers = dict()

    def _get_controller(self, guild: discord.Guild):
        c = self.controllers.get(guild.id, None)
        if c is None:
            self.controllers[guild.id] = AudioController(self.bot, guild)
        return self.controllers[guild.id]

    @commands.hybrid_command(
        name="debug",
        usage="&debug",
        description="Dumbs a ton of info into an embed",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _debug(self, ctx: commands.Context):
        if ctx.author.id not in [
            380987045008506880,
            936226256159125525,
            722480803896098876,
        ]:
            await ctx.reply(
                embed=create_embed(
                    "Error", "This command can only be used by the bot's developers!"
                )
            )
            return
        controller: AudioController = self._get_controller(ctx.guild)
        """
        current_fragment = lambda: (
            f"{controller._playlist.current_fragment+1}/{len(controller._playlist.songs[controller._playlist.current_song].fragments)}"
            if controller._playlist.current_song < len(controller._playlist.songs)
            else f"Song out of range (Internal Fragment IDX Buffer: {controller._playlist.current_fragment+1} [Lit.: {controller._playlist.current_fragment}])"
        ) + (
            f"Fragment File Name: `{controller._playlist.songs[controller._playlist.current_song].fragments[controller._playlist.current_fragment].get_fragment_filepath()}`"
            if controller._playlist.current_song < len(controller._playlist.songs)
            else ""
        )
        current_song = lambda: (
            f"{controller._playlist.current_song+1}/{len(controller._playlist.songs)}"
            if len(controller._playlist.songs)
            else f"Song out of range (Internal Song IDX Buffer: {controller._playlist.current_song+1} [Lit.: {controller._playlist.current_song}])"
        )
        await ctx.reply(
            embed=create_embed(
                f"Audio Controller for {controller.guild.id}",
                "# Audio Player\n"
                + f"Loop Mode: {controller._playlist.loopmode.name.title()}\n"
                + f"Current Fragment: {current_fragment()}\n"
                + f"Current Song: {current_song()}\n"
                + f"Voice Client: {('Playing' if controller._vc.is_playing else 'Not Playing') if controller._vc else 'Disconnected'}\n"
                + f"Finished playing? {('Yes' if controller._finished_playing.is_set() else 'No') if controller._finished_playing else 'null'}\n"
                + f"Paused? {('Yes' if controller._vc.is_paused() else 'No') if controller._vc else 'null'}",
            )
        )
        await ctx.reply(
            embed=create_embed(
                f"Audio Controller for {controller.guild.id}",
                "# Download Queue\n"
                + f"Song Fetch Queue: {len([song for song in controller._playlist.songs if not song._setup_task.done()])}\n"
                + "I... just use the debugger to see which fragments are downloading.",
            )
        )
        """
        playlist: Playlist = controller._playlist
        data: List[str] = []
        # VC Connected?
        if controller._vc is not None:
            data.append(
                "Voice Client Connected: "
                + (
                    "`Yes`"
                    if controller._vc.is_connected()
                    else "`Idle` **Something is wrong here**"
                )
            )
        else:
            data.append("Voice Client Connected: `No`")
            data.append("- Playing: `No`")
            data.append("- Paused: `No`")
        if controller._vc is not None:
            # Playing?
            data.append(
                "- Playing: " + ("`Yes`" if controller._vc.is_playing() else "`No`")
            )
            # Paused?
            data.append(
                "- Paused: " + ("`Yes`" if controller._vc.is_paused() else "`No`")
            )
        # -- Internals --
        # Song status
        if playlist.current_song < len(playlist.songs):
            # Song exists
            data.append(
                "Current Song: "
                + f"[idx: `{playlist.current_song}`/`{len(playlist.songs)}`] "
                + f"[dec: `{playlist.current_song+1}`/`{len(playlist.songs)}`]"
            )
            # Fragment
            try:
                if (
                    playlist.current_fragment
                    < len(playlist.songs[playlist.current_song].fragments)
                    and playlist.current_fragment > -1
                ):
                    # Fragment within bounds
                    data.append(
                        "Current Fragment: "
                        + f"[idx: `{playlist.current_fragment}`/{len(playlist.songs[playlist.current_song].fragments)}] "
                        + f"[dec: `{playlist.current_fragment+1}`/{len(playlist.songs[playlist.current_song].fragments)}] "
                    )
                else:
                    # Fragment out of bounds
                    data.append(
                        "Current Fragment: "
                        + f"[idx: `{playlist.current_fragment}`/{len(playlist.songs[playlist.current_song].fragments)}] "
                        + f"[dec: `{playlist.current_fragment+1}`/{len(playlist.songs[playlist.current_song].fragments)}] **Out of range**"
                    )
            except AttributeError:
                data.append(
                    "Current Fragment: *Waiting for song to finish initialization...* "
                    + f"[idx: `{playlist.current_fragment}`] "
                    + f"[dec: `{playlist.current_fragment+1}`] "
                    if playlist.current_fragment == 0
                    else "**Unexpected value, should be `0`**"
                )
        else:
            # Song does NOT exist
            data.append(
                "Current Song: "
                + f"[idx: `{playlist.current_song}`/`{len(playlist.songs)}`] "
                + f"[dec: `{playlist.current_song+1}`/`{len(playlist.songs)}`] **Out of queue**"
            )
            if playlist.current_fragment != 0:
                data.append(
                    "Current Fragment: "
                    + f"[idx: `{playlist.current_fragment}`] "
                    + f"[dec: `{playlist.current_fragment+1}`] **Unexpected value, should be `0`** "
                    + "*No song is present*"
                )
            else:
                data.append(
                    "Current Fragment: "
                    + f"[idx: `{playlist.current_fragment}`] "
                    + f"[dec: `{playlist.current_fragment+1}`] *No song is present*"
                )
        # Loop mode
        data.append("Loop: " + f"`{playlist.loopmode.name.title()}`")

        # Send response
        await ctx.reply(
            embed=create_embed(
                f"Audio Controller for {controller.guild.id}", "\n".join(data)
            )
        )

    @commands.hybrid_command(
        name="restart",
        usage="&restart",
        description="Reloads the bot in case it stops accepting new requests",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def _reload(self, ctx: commands.Context, force: bool = False):
        controller: AudioController = self._get_controller(ctx.guild)
        if (not force) and not controller.is_connected():
            await ctx.reply(
                'Will not reload, as we are connected. If this is incorrect, set the force flag to "True"'
            )
            return
        channel: discord.VoiceChannel = controller._vc.channel
        await ctx.invoke(self._leave)
        await ctx.invoke(self._join, channel)
        await ctx.reply("Reloaded!")

    @commands.hybrid_command(
        name="join",
        usage="&join [channel]",
        description="Makes the bot join a channel, by default your current channel",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _join(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        controller: AudioController = self._get_controller(ctx.guild)
        if (channel or ctx.author.voice.channel) is None:
            await ctx.reply(
                embed=create_embed(
                    "Error",
                    "You must either run this command in a voice channel or specify one",
                )
            )
            return
        if not controller.is_connected():
            await controller.join(channel or ctx.author.voice.channel, ctx.channel)
            await ctx.reply(
                embed=create_embed(
                    "Bot Connected",
                    f"Joined <#{(channel or ctx.author.voice.channel).id}>",
                )
            )
        else:
            if controller._vc.channel == (channel or ctx.author.voice.channel):
                await ctx.reply(
                    embed=create_embed(
                        "Bot Already Connected",
                        f"Already connected to <#{(channel or ctx.author.voice.channel).id}>",
                    )
                )
                return
            await controller.leave()
            await controller.join(channel or ctx.author.voice.channel, ctx.channel)
            await ctx.reply(
                embed=create_embed(
                    "Bot Re-Connected",
                    f"Left the previous channel and joined <#{(channel or ctx.author.voice.channel).id}>",
                )
            )

    @commands.hybrid_command(
        name="leave",
        usage="&leave",
        aliases=["stop"],
        description="Makes the bot leave it's current channel",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _leave(self, ctx: commands.Context):
        controller: AudioController = self._get_controller(ctx.guild)
        if controller.is_connected():
            await controller.stop()
            await ctx.reply(
                embed=create_embed(
                    "Bot Disconnected", "Stopped playing & left the voice channel"
                )
            )
        else:
            await ctx.reply(
                embed=create_embed("Error", "The bot is not currently in a channel!")
            )

    @commands.hybrid_command(
        name="play",
        usage="&play <url>",
        description="Adds the song or playlist to the queue",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _play(self, ctx: commands.Context, url: str):
        await ctx.defer()
        controller: AudioController = self._get_controller(ctx.guild)
        if not controller.is_connected():
            await controller.join(ctx.author.voice.channel, ctx.channel)
        status: discord.Message = None
        if "list=" in url:
            status = await ctx.reply(
                embed=create_embed(
                    "Queuing Playlist",
                    "It appears you are queuing a playlist\nThe bot may take a while to load it, please be patient",
                )
            )
        else:
            status = await ctx.reply(
                embed=create_embed(
                    "Queuing Song",
                    f"The bot is now queuing {url}\nThe bot may take a while to fetch it, please be patient",
                )
            )
        await controller.queue(url)
        if status is not None:
            await status.edit(
                embed=create_embed(
                    "Queued",
                    f"Added {url} to the queue!\nTo view the current queue, use `/queue`",
                )
            )
        else:
            await ctx.reply(
                embed=create_embed(
                    "Queued",
                    f"Added {url} to the queue!\nTo view the current queue, use `/queue`",
                )
            )
        await controller.play()

    @commands.hybrid_command(
        name="pause",
        usage="&pause",
        description="Pauses the audio player",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _pause(self, ctx: commands.Context):
        controller: AudioController = self._get_controller(ctx.guild)
        if not controller.is_connected() or controller._vc.is_paused():
            await ctx.reply(
                embed=create_embed("Error", "The bot is not playing right now!")
            )
        controller._vc.pause()
        await ctx.reply(
            embed=create_embed(
                "Paused",
                "The audio player has been paused.\nUse `/resume` to continue playing.",
            )
        )

    @commands.hybrid_command(
        name="resume",
        usage="&resume",
        aliases=["unpause"],
        description="Pauses the audio player",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _resume(self, ctx: commands.Context):
        controller: AudioController = self._get_controller(ctx.guild)
        if not controller.is_connected():
            await ctx.reply(
                embed=create_embed(
                    "Error", "The bot is currently not in a voice channel!"
                )
            )
            return
        if controller._vc.is_paused():
            controller._vc.resume()
            await ctx.reply(
                embed=create_embed("Resumed", "The audio player has been unpaused.")
            )
        else:
            await ctx.reply(
                embed=create_embed("Error", "The audio player is not paused.")
            )

    @commands.hybrid_command(
        name="skip",
        usage="&skip [number]",
        description="Skips any number of songs (by default 1)",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _skip(self, ctx: commands.Context, num: int = 1):
        await ctx.defer()
        controller: AudioController = self._get_controller(ctx.guild)
        if not controller.is_connected():
            await ctx.reply(
                embed=create_embed(
                    "Error", "The bot is currently not in a voice channel!"
                )
            )
            return
        if not controller._vc.is_playing():
            await ctx.reply(
                embed=create_embed("Error", "The audio player is not playing.")
            )
            return
        if num <= 0 or num > 100:
            await ctx.reply(
                embed=create_embed(
                    "Error",
                    "The number of songs to skip must be between 1 and 100 (inclusive)",
                )
            )
            return
        if num == 1:
            await controller.skip(quiet=True)
        else:
            for _ in range(num - 1):
                controller._playlist.skip()
            await controller.skip(quiet=True)
        await ctx.reply(
            embed=create_embed(
                "Fast-forward", f"Skipped {num} song{'s' if num > 1 else ''}"
            )
        )

    @commands.hybrid_command(
        name="queue",
        usage="&queue [page]",
        description="Shows a specific page of the current queue",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _queue(self, ctx: commands.Context, page: int = 1):
        controller: AudioController = self._get_controller(ctx.guild)
        queue, remaining = controller.get_queue(
            template_remaining="{}", character_limit_per_page=1700
        )  # Leaves us with 300 characters to work with per page
        if len(queue) == 0:
            await ctx.reply(
                embed=create_embed("Error", "There are no songs in the queue")
            )
            return
        if page < 1 or page > len(queue):
            await ctx.reply(
                embed=create_embed(
                    "Error",
                    f"Page out of range\nThere {'are' if len(queue) > 1 else 'is'} only {len(queue)} page{'s' if len(queue) > 1 else ''} in the queue!\nThe first page is always `1`.",
                )
            )
            return
        body = "{}\nand {} songs, which are still fetching".format(
            queue[page - 1], remaining
        )
        e = create_embed("Queue", body)
        e.set_footer(text=f"Page {page}/{len(queue)}")
        await ctx.reply(embed=e)

    @commands.hybrid_command(
        name="loop",
        usage="&loop [all/current/(off/none)]",
        description="Toggles loop mode",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _loop(self, ctx: commands.Context, mode: str = None):
        controller: AudioController = self._get_controller(ctx.guild)
        if mode is None:
            loop_mode = controller._playlist.cycle_loop_mode()
        else:
            mode = mode.lower()
            if mode.startswith("a"):
                controller._playlist.set_loop_mode(LoopMode.ALL)
            elif mode.startswith("c") or mode.startswith("s"):
                controller._playlist.set_loop_mode(LoopMode.CURRENT)
            else:
                controller._playlist.set_loop_mode(LoopMode.OFF)
            loop_mode = controller._playlist.get_loop_mode()
        await ctx.reply(
            embed=create_embed("Loop", f"Loop mode has been set to `{loop_mode}`")
        )

    @commands.hybrid_command(
        name="clear",
        usage="&clear",
        description="Clears the queue",
    )
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _clear(self, ctx: commands.Context):
        controller: AudioController = self._get_controller(ctx.guild)
        controller._playlist.clear()
        await controller.skip()
        await ctx.reply(embed=create_embed("Queue", "The queue has been cleared!"))


async def setup(bot: commands.Bot):
    await bot.add_cog(Default(bot))