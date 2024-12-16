import logging
from enum import Enum
from typing import List

from .song import Fragment
from .song import Playlist as PlaylistLoader
from .song import Song

logger = logging.getLogger("strongest.playlist")


class LoopMode(Enum):
    OFF = 0
    CURRENT = 1
    ALL = 2


class Playlist:
    songs: List[Song]
    loopmode: LoopMode
    current_song: int
    current_fragment: int

    def __init__(self) -> None:
        logger.info("New playlist initialized")
        self.songs = []
        self.loopmode = LoopMode.OFF
        self.current_song = 0
        self.current_fragment = 0

    async def get(self) -> str | None:
        """Returns the path to the fragment or None if there is no song

        Returns:
            str: The path to the fragment to play
            None: There is no song to play
        """
        logger.debug("Retrieving current song")
        song_count: int = len(self.songs)
        if song_count == 0:
            logger.debug("No songs present, returning None")
            return None
        if self.current_song >= song_count:
            logger.debug("Current song is out of range, returning None")
            return None
        song: Song = self.songs[self.current_song]
        logger.debug("Waiting for current song to fetch metadata")
        await song.wait_until_ready()
        fragment: Fragment = song.fragments[self.current_fragment]
        logger.debug("Waiting for current song's fragment to cache")
        await fragment.wait_until_downloaded()  # Makes sure the current fragment is downloaded
        # Is the next fragment preloading? If not, preload it
        self._preload_next_fragment(
            song, self.current_fragment
        )  # This function figures out by it self whether to run another download or not
        logger.debug("Returning fragment path")
        return fragment.get_fragment_filepath()

    async def next(self) -> None:
        logger.debug("Next fragment or song has been requested")
        if len(self.songs) == 0:
            logger.debug("There are no songs, will not move anything")
            # There are no songs, don't do anything
            return
        song: Song = self.songs[self.current_song]
        logger.debug("Checking current song's progression")
        await song.wait_until_ready()  # Make sure the current song's fragments exist
        fragments_last_idx: int = len(song.fragments) - 1
        if self.current_fragment >= fragments_last_idx:
            # We were at the last fragment, next song
            logger.debug("This was the last fragment, moving to the next song")
            self._next_song()
        else:
            # We are not at the end of the song yet, move onto the next fragment
            logger.debug("More fragments are present, moving fragment")
            self._next_fragment()

    def skip(self) -> None:
        logger.debug("Skipping current song")
        if len(self.songs) == 0:
            logger.debug("There are no songs, will not skip anything")
            return
        if self.current_song + 1 >= len(self.songs):
            self.current_song = len(self.songs)
            logger.debug(
                "We already reached the end of the queue, setting skip ptr to queue end"
            )
            return
        self._next_song()

    def _next_fragment(self) -> None:
        song: Song = self.songs[self.current_song]
        self.current_fragment += 1
        logger.debug("Fragment pointer increased by 1")
        # We download the next fragment, if there is one
        self._preload_next_fragment(song, self.current_fragment)

    def _next_song(self) -> None:
        logger.debug("Fragment pointer reset to 0")
        self.current_fragment = 0
        if self.loopmode == LoopMode.CURRENT:
            logger.debug("Loop mode is current, will not move song pointer")
            return
        song_count = len(self.songs)
        if self.current_song >= song_count:
            # If we are already at the end of the queue (after last song), don't do anything
            logger.debug(
                "Song pointer is already at the end of the queue, will not move"
            )
            return
        self.current_song += 1
        logger.debug("Song pointer increased by 1")
        # if our current song index is AFTER the end of the playlist
        if self.current_song >= song_count and self.loopmode == LoopMode.ALL:
            logger.debug(
                "Song pointer is at the end of the queue, but loop mode is all, resetting back to 0"
            )
            self.current_song = 0
        # If loop mode is off, we just move onto the non-existent song.
        # Get current song will handle returning None if we are at the end of the playlist
        # Load the first fragment
        self._preload_next_song()  # Preload the next song if there is one

    def _preload_next_fragment(self, song: Song, current_fragment: int) -> None:
        logger.debug("Fragment preload requested in %s", song.meta.title)
        fragments_last_idx: int = len(song.fragments) - 1
        logger.debug("Last fragment index is %d", fragments_last_idx)
        if current_fragment >= fragments_last_idx:
            logger.debug(
                "Will not preload fragment %d, as the current fragment is the last one",
                current_fragment + 1,
            )
            logger.debug(
                "As fragment %d is the last one, we will preload the next song.",
                current_fragment,
            )
            self._preload_next_song()
            return
        logger.debug("Preloading fragment %d", current_fragment + 1)
        song.fragments[
            current_fragment + 1
        ].start_download_thread()  # This won't do anything if it's already downloaded or already in the process of downloading

    def _preload_next_song(self) -> None:
        logger.debug("Next song preload requested")
        song_count = len(self.songs)
        # If there is another song after this one, preload it's first fragment
        if self.current_song + 1 < song_count:
            logger.debug("Next song exists, will preload its first fragment")
            # If the next song exists
            song = self.songs[self.current_song + 1]
            self._preload_next_fragment(
                song, -1
            )  # We are not using the current_fragment to access the current fragment in this function, so this is fine
            return
        logger.debug("Next song does not exist, will not preload")

    async def add(self, url: str) -> None:
        logger.debug("Add job for %s requested", url)
        if "&list=" in url or "?list=" in url:
            logger.debug("%s appears to be a list, attempting to load", url)
            try:
                playlist: PlaylistLoader = PlaylistLoader(url)
                logger.debug("Waiting for PlaylistLoader to finish")
                await playlist.wait_until_ready()
                self.songs = self.songs + playlist.songs
                logger.debug("%s has been loaded into the queue as a list", url)
                logger.debug("Add for %s has been delegated to Song objects", url)
                return
            except ValueError:
                logger.debug("%s wasn't a list, adding as regular song", url)
        logger.debug("%s is being queued", url)
        self.songs.append(Song(url))
        logger.debug("Add for %s has been delegated to Song objects", url)

    async def remove(self, identifier: int | Song | str) -> None:
        if isinstance(identifier, int):
            if identifier < len(self.songs) and identifier >= 0:
                self.songs.pop(identifier)
        elif isinstance(identifier, Song):
            self.songs.remove(identifier)
        else:
            self.songs = [song for song in self.songs if song.meta.url != identifier]

    def clear(self) -> None:
        self.songs.clear()
        self.current_song = 0
        self.current_fragment = 0

    def get_loop_mode(self) -> str:
        return self.loopmode.name

    def set_loop_mode(self, loop_mode: LoopMode) -> None:
        self.loopmode = loop_mode

    def cycle_loop_mode(self) -> LoopMode:
        if self.loopmode == LoopMode.OFF:
            self.set_loop_mode(LoopMode.CURRENT)
        elif self.loopmode == LoopMode.CURRENT:
            self.set_loop_mode(LoopMode.ALL)
        else:
            self.set_loop_mode(LoopMode.OFF)
        return self.get_loop_mode()