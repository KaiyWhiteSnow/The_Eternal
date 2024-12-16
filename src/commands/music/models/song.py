import asyncio
import json
import logging
import os
import urllib
from typing import Dict, List

import yt_dlp
from yt_dlp.utils import download_range_func

from ..threaded_executor import ThreadedExecutor, threaded

logger = logging.getLogger("strongest.song")

CACHE_DIR = "./cache"


def initialize_cache():
    meta_file = CACHE_DIR + '/meta.json'
    if not os.path.exists(CACHE_DIR):
        try:
            os.makedirs(CACHE_DIR)
        except OSError as e:
            return
    if not os.path.exists(meta_file):
        try:
            with open(meta_file, 'w') as f:
                json.dump({}, f)
        except OSError as e:
            return

initialize_cache()

class MetaCache:
    _cache: Dict

    def __init__(self) -> None:
        self._cache = dict()
        try:
            self.load()
        except FileNotFoundError:
            self.save()

    def _get_params(self, url: str) -> Dict:
        return urllib.parse.parse_qs(urllib.parse.urlparse(url).query)

    def get(self, url: str, default: Dict | None = None) -> Dict | None:
        params = self._get_params(url)
        id = params.get("list", params.get("v", [None]))[0]
        if id is None:
            return default
        return self._cache.get(id, default)

    def set(self, url: str, data: Dict) -> None:
        params = self._get_params(url)
        id = params.get("list", params.get("v", [None]))[0]
        if id is None:
            return None
        self._cache[id] = data
        self.save()

    def save(self) -> None:
        with open(f"{CACHE_DIR}/meta.json", "w") as f:
            json.dump(self._cache, f)

    def load(self) -> None:
        with open(f"{CACHE_DIR}/meta.json", "r") as f:
            self._cache = json.load(f)


meta_cache: MetaCache = MetaCache()


class Meta:
    url: str
    vid: str
    title: str
    channel_name: str
    channel_url: str
    _fetch_thread: ThreadedExecutor | None
    _meta_injection: Dict | None

    def __init__(self, url: str, info: Dict | None = None) -> None:
        logger.info("Created SongMeta object for %s", url)
        self._meta_injection = meta_cache.get(url, info)
        self._fetch_thread = self._fetch_meta(url)

    async def wait_until_fetched(self) -> None:
        """
        Asynchronously waits until the metadata fetch is completed.

        This function waits until the fetch thread has finished fetching the data.
        It uses the `wait()` method of the `fetch_thread` attribute to wait for the completion.

        Returns:
            None: This function does not return anything.
        """
        logger.debug("Someone is waiting for a song object to fetch meta data")
        await self._fetch_thread.wait()

    def get_fragment_dir(self) -> str:
        """
        Return the directory path for where the fragments of this song will be stored
        """
        return f"{CACHE_DIR}/{self.vid}"

    @threaded
    async def _fetch_meta(self, url) -> None:
        logger.info("Started fetching metadata for %s", url)
        if self._meta_injection is not None:
            logger.info("Metadata for %s appears to be injected", url)
            info = self._meta_injection
            try:
                self.vid = info["id"]
                self.url = info["webpage_url"]
                self.title = info["title"]
                self.channel_name = info.get("channel", "")
                self.channel_url = info.get("uploader_url") or info.get(
                    "channel_url", self.url
                )
                self.duration = info["duration"]
                logger.info("Finished injecting metadata for %s", url)
                return
            except KeyError:
                logger.error(
                    "Failed to inject metadata for %s, will retry using fetch", url
                )
        ydl_opts = {
            "format": "bestaudio/best",
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
            "no_playlist": True,
            "no_search": True,
            "verbose": False,
            "simulate": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            self._meta_injection = info

            self.vid = info["id"]
            self.url = info["webpage_url"]
            self.title = info["title"]
            self.channel_name = info.get("channel", "")
            self.channel_url = info.get("uploader_url") or info.get(
                "channel_url", self.url
            )
            self.duration = info["duration"]
        logger.info("Finished fetching metadata for %s", url)
        meta_cache.set(url, info)


class Fragment:
    fid: int
    start: int
    end: int
    meta: Meta
    _download_thread: ThreadedExecutor | None

    def __init__(self, meta: Meta, fid: int, start: int, end: int) -> None:
        logger.debug("Created fragment from %d to %d for %s", start, end, meta.url)
        self.meta = meta
        self.fid = fid
        self.start = start
        self.end = end
        self._download_thread = None

    def is_downloaded(self) -> bool:
        """Returns whether the fragment's file is downloaded or not

        Returns:
            bool: True if it is in cache, otherwise False
        """
        return os.path.exists(self.get_fragment_filepath())

    async def wait_until_downloaded(self) -> None:
        """Waits until the fragment's file is downloaded
        Downloads it if it no longer exists or wasn't present in the cache in the first place
        """
        logger.debug(
            "Someone is waiting for a fragment of %s to download", self.meta.url
        )
        self.start_download_thread()  # Doesn't do anything if the download thread is already running
        await self._download_thread.wait()

    def start_download_thread(self):
        """
        Starts a new download thread if one does not already exist.
        Does not re-download if the fragment is already in the cache

        This function checks if a download thread is already running. If a thread is not running,
        or if the current thread has been set but the download has not completed, a new download thread
        is started.

        Parameters:
            self (object): The instance of the class.

        Returns:
            None
        """
        if self._download_thread is not None:
            if not self._download_thread.is_set():
                return
            if self.is_downloaded():
                return
        logger.debug("Creating download job for a fragment of %s", self.meta.url)
        self._download_thread = self._download()

    def get_fragment_filepath(self) -> str:
        """
        Return the file path for the fragment file
        """
        return f"{self.meta.get_fragment_dir()}/{self.fid}"

    @threaded
    async def _download(self) -> None:
        if self.is_downloaded():
            logger.debug(
                "Fragment %d to %d of %s is cached! Will not re-download.",
                self.start,
                self.end,
                self.meta.url,
            )
            return
        logger.debug(
            "Starting download of fragment %d to %d of %s",
            self.start,
            self.end,
            self.meta.url,
        )
        yt_opts = {
            "format": "bestaudio/best",
            "outtmpl": self.get_fragment_filepath(),
            "extractaudio": True,
            "audioformat": "webm",
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
            "no_playlist": True,
            "no_search": True,
            "verbose": False,
            "download_ranges": download_range_func(None, [(self.start, self.end)]),
            "force_keyframes_at_cuts": True,
        }

        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            ydl.download(self.meta.url)
        logger.debug(
            "Finished download of fragment %d to %d of %s",
            self.start,
            self.end,
            self.meta.url,
        )


class Song:
    meta: Meta
    fragments: List[Fragment]
    _setup_task: asyncio.Task

    def __init__(self, url: str, meta: Meta | None = None) -> None:
        logger.info("Created new song: %s", url)
        self.meta = meta
        self._setup_task = asyncio.get_event_loop().create_task(self._download(url))

    async def wait_until_ready(self) -> None:
        """Waits until the file's meta data is fetched and fragments are prepared to be downloaded"""
        logger.debug("Someone is waiting for a song to finish initialization")
        await self._setup_task

    async def _download(self, url) -> None:
        if self.meta is None:
            logger.debug("Creating Metadata object")
            self.meta = Meta(url)
        else:
            logger.debug(
                "Metadata object has been injected, waiting for it to be fetched"
            )
        await self.meta.wait_until_fetched()
        logger.debug("Metadata object fetched, creating fragments")
        self._create_fragments()
        logger.debug("Fragments created")

    def _create_fragments(self) -> None:
        duration = int(self.meta.duration)
        start = 0
        fragments = []

        FRAGMENT_SIZE: int = 200 # 3 Minutes and 20 Seconds

        while start < duration:
            end = min(start + FRAGMENT_SIZE, duration)
            if len(fragments) > 0 and end - fragments[-1].end < FRAGMENT_SIZE:
                fragments[-1].end = end
            else:
                fragments.append(Fragment(self.meta, len(fragments), start, end))
            start = end

        self.fragments = fragments


class Playlist:
    url: str
    songs: List[Song]
    urls: List[str]
    videos: List[Dict]
    _fetch_thread: ThreadedExecutor | None
    _create_task: asyncio.Task

    def __init__(self, url: str) -> None:
        logger.info("Playlist loader initialized for %s", url)
        if not ("&list=" in url or "?list=" in url):
            logger.warn("%s is NOT a playlist", url)
            raise ValueError("Not a playlist URL")
        self.url = url
        self.songs = []
        self.urls = []
        self._create_task = asyncio.create_task(self._fetch_and_create_songs())

    async def _fetch_and_create_songs(self) -> None:
        logger.debug("Playlist initialization task started")
        self._fetch_thread = (
            self._fetch_playlist_urls()
        )  # Running this here should avoid a race condition when calling Playlist.wait_until_ready()
        logger.debug("Waiting for urls to download")
        await self._fetch_thread.wait()
        self.songs = self._urls_to_songs(self.urls, self.videos)
        logger.debug("Playlist initialization task finished")

    async def wait_until_ready(self) -> None:
        """Waits until all songs in the playlist have been fetched and created in Playlist.songs"""
        logger.debug("Someone is waiting for a playlist to finish initialization")
        await self._create_task

    @threaded
    async def _fetch_playlist_urls(self) -> None:
        logger.info("PlaylistLoader started fetching urls for %s", self.url)
        cached = meta_cache.get(self.url)
        if cached is None:
            ydl = yt_dlp.YoutubeDL(
                {
                    "nocheckcertificate": True,
                    "quiet": True,
                    "no_warnings": True,
                    "no_playlist": True,
                    "no_search": True,
                    "verbose": False,
                    "playlistend": 50,
                }
            )
            with ydl:
                info = ydl.extract_info(self.url, download=False)
            meta_cache.set(self.url, info)
        else:
            info = cached
        if info.get("entries", None) is None:
            videos = []
            urls = []
        else:
            videos = info["entries"]
            urls = [
                video.get("original_url", video.get("webpage_url"))
                for video in info["entries"]
            ]
        self.urls = urls
        self.videos = videos
        logger.info("PlaylistLoader finished fetching urls for %s", self.url)

    def _urls_to_songs(self, urls: List[str], videos: List[Dict]) -> List[Song]:
        # attempt Metadata injection
        return [
            Song(
                url,
                meta=Meta(
                    videos[i].get(
                        "original_url", videos[i].get("webpage_url", urls[i])
                    ),
                    info=self.videos[i],
                ),
            )
            for i, url in enumerate(urls)
        ]