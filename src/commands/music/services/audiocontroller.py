import asyncio
import logging
from typing import List, Tuple

import discord
from discord.ext import commands

from ..models.playlist import Playlist
from ..models.song import Fragment

logger = logging.getLogger("strongest.audiocontroller")


class AudioController:
    bot: commands.Bot
    guild: discord.Guild
    _vc: discord.VoiceClient | None
    _callback_channel: discord.TextChannel
    _playlist: Playlist
    _finished_playing: asyncio.Event | None
    _play_task: asyncio.Task | None
    __loop: asyncio.AbstractEventLoop

    def __init__(self, bot: commands.Bot, guild: discord.Guild) -> None:
        logger.info("Initialized AudioController for %s (%d)", guild.name, guild.id)
        self.bot = bot
        self.guild = guild
        self._playlist = Playlist()
        self._finished_playing = None
        self._play_task = None
        self.__loop = asyncio.get_running_loop()

        self._callback_channel = None

        # TODO: This can be removed when we replace all usages of this in default.py with getters
        self._vc = None

    def is_connected(self) -> bool:
        return self._vc is not None

    async def join(
        self, channel: discord.VoiceChannel, callback_channel: discord.TextChannel
    ) -> None:
        logger.info(
            "Joining channel %s with callback in %s",
            channel.name,
            callback_channel.name,
        )
        if self._vc is not None:
            logger.warn("Already in a voice channel! Will not overwrite.")
            return
        self._vc = await channel.connect()
        self._callback_channel = callback_channel

    async def leave(self) -> None:
        logger.info("Leaving current channel")
        await self._vc.disconnect()
        self._vc = None
        self._callback_channel = None
        self._playlist.clear()

    async def queue(self, url: str) -> None:
        logger.info("Queuing %s", url)
        try:
            await self._playlist.add(url)
            logger.info("Queued %s successfully", url)
        except Exception as e:
            logger.error("Something went wrong queuing %s", url, exc_info=e)

    def get_queue(
        self,
        template: str = "[{}](<{}>) uploaded by [{}](<{}>)",
        template_remaining: str = "{} more songs, which are still being fetched.",
        character_limit_per_page: int = 2000,
    ) -> Tuple[List[str], str]:
        """Returns a partitioned list of messages describing the current queue

        Returns:
            List[str]: A partitioned list of strings
        """
        queued = [
            template.format(
                song.meta.title,
                song.meta.url,
                song.meta.channel_name,
                song.meta.channel_url,
            )
            for song in self._playlist.songs
            if song._setup_task.done()
        ]
        remaining = template_remaining.format(len(self._playlist.songs) - len(queued))
        partitioned = []
        partition = ""
        for i in queued:
            line = f"{partition}\n{i}"
            if len(line) > character_limit_per_page - (len(remaining) + 2):
                partitioned.append(partition)
                partition = i
            else:
                partition = line
        partitioned.append(partition)
        return partitioned, remaining

    async def skip(self, quiet: bool = False) -> None:
        """Skips the current song
        Returns:
            None
        """
        logger.debug("Skipping the current song")
        try:
            self._playlist.current_fragment = len(
                self._playlist.songs[self._playlist.current_song].fragments
            )
        except IndexError as e:
            logger.error("bruh", exc_info=e)  # TODO: Actually debug what's wrong
            self._playlist.current_fragment = 2**64
        self._vc.stop()

    async def play(self) -> None:
        """
        Initialities the audio player task

        This method checks if a play task is already running.
        If not, it creates a new event object to track when the audio playback has finished.
        It then sets the event to indicate that the audio has finished playing.
        Finally, it creates a new play task using the `_play` method and assigns it to the `_play_task` attribute.

        Returns:
            None
        """
        logger.info("Controller play command issued")
        if self._play_task is None:
            logger.info("Starting new play task")
            self._finished_playing = asyncio.Event()
            self._finished_playing.set()
            # TODO? Perhaps use a seperate thread for the play loop it self (asyncio "executor" param)
            self._play_task = asyncio.create_task(self._play())
        else:
            logger.warn("Already playing! Nothing will be done.")

    async def stop(self) -> None:
        """Stops the audio player
        Returns:
            None
        """
        logger.info("Controller stop command issued")
        if self._play_task is None:
            logger.warn("We are already stopped")
            if self._vc is not None:
                logger.warn("Leaving the voice channel, as it is connected anyway")
                await self.leave()
            return
        logger.debug("Running cleanup and leave")
        await self._cleanup()
        await self.leave()
        logger.info("Stopped!")

    async def _play(self) -> None:
        """Asynchronously plays audio from the playlist.
        It continuously retrieves fragments from the playlist and plays them using the voice client.
        It sets up an event to signal when the audio playback is finished.
        If there are no more songs in the playlist, it sends a message to the callback channel and then performs cleanup before returning.
        """
        logger.debug("New play task started")
        if self._finished_playing is None:
            self._finished_playing = asyncio.Event()
        while 1:
            self._finished_playing.clear()
            logger.debug("Retrieving fragment")
            frag_path: str | None = await self._playlist.get()
            if frag_path is None:
                try:
                    logger.debug("Fragment is none, returning")
                    return
                finally:
                    logger.debug("Fragment was none, calling cleanup")
                    await self._cleanup()
            # await self._announce_current_song() #! Broken asf, announcing by fragment instead of song
            # TODO: Maybe we can use PCMAudio to read from a buffer instead of a file?
            logger.debug("Starting audio playback")
            self._vc.play(
                discord.FFmpegPCMAudio(frag_path),
                after=lambda _: asyncio.run_coroutine_threadsafe(
                    self._next(), self.__loop
                ).result(),
            )
            logger.debug("Waiting until fragment playback finishes")
            await self._finished_playing.wait()
            logger.debug("Fragment playback finished!")

    async def _next(self) -> None:
        """Asynchronously moves the current song to the next item in the playlist and unblocks the audio playback process. (Blocked event-wise)

        This method checks if the current play task has been cancelled. If it has, the method returns immediately as to not interfiere with cleanup.
        Otherwise, it proceeds to the next item in the playlist and starts playing it.
        After that, it sets an event to indicate that the playback has finished.

        Returns:
            None
        """
        try:
            logger.debug("Moving queue position using _next")
            if self._play_task.cancelled():
                return
            await self._playlist.next()
            # await self._play() #! This would do recursion, whereas we already have a loop for playing the audio
            self._finished_playing.set()
        except Exception as e:
            logger.error(
                "An exception occoured while executing _next, we will do a cleanup!",
                exc_info=e,
            )
            await self._cleanup()

    async def _cleanup(self) -> None:
        """
        Asynchronous function to perform cleanup tasks. No parameters. Returns None.
        Makes sure the audio player is stopped and then resets to default state.
        """
        logger.debug("Cleanup issued")
        self._play_task.cancel()
        if self._vc.is_playing():
            logger.debug("Cleanup found we are playing, stopping")
            self._vc.stop()
        self._finished_playing.set()
        self._play_task = None
        logger.debug("Finished cleanup")