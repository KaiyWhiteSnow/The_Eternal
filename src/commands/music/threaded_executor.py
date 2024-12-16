import threading
import asyncio
from typing import Any, Coroutine, Callable

# ? This might be needless-ly complicated. If this still sucks, there is an alternative solution in my chatgpt history
class ThreadedExecutor:
    _thread: threading.Thread
    _event: asyncio.Event
    _coro: Coroutine
    _loop: asyncio.AbstractEventLoop
    _result: Any | None

    def __init__(self, coro: Coroutine) -> None:
        self._event = asyncio.Event()
        self._coro = coro
        self._loop = asyncio.get_event_loop()
        self._thread = threading.Thread(target=lambda: asyncio.run(self._run()))
        self._thread.start()

    async def wait(self) -> None:
        """
        Wait for the event to be set.

        This function is used to wait for the thread to finish. Execution will resume once the thread has finished.

        Returns:
            None: This function does not return any value.
        """

        await self._event.wait()

    def is_set(self) -> bool:
        """
        Check if the thread has finished.

        Returns:
            bool: True if the event is set, False otherwise.
        """
        return self._event.is_set()

    async def get(self) -> Any:
        """
        Asynchronously gets the result once it is avabiable.
        Returns:
            Any: The result.
        """
        await self.wait()
        return self._result

    async def _complete(self):
        self._event.set()

    async def _run(self) -> None:
        try:
            self._result = await self._coro
        finally:
            asyncio.run_coroutine_threadsafe(self._complete(), self._loop)


def threaded(func: Coroutine) -> Callable[[Any, Any], ThreadedExecutor]:
    """
    Decorator that wraps a coroutine function in a ThreadedExecutor.

    ! NOTE: The function runs in a seperate event loop, awaits and event sets might not behave as expected

    Args:
        func (Coroutine): The coroutine function to be wrapped.

    Returns:
        Callable[[Any, Any], ThreadedExecutor]: A wrapper function that takes any number of positional and keyword arguments and returns a ThreadedExecutor object.

    Example:
        @threaded
        async def my_coroutine():
            # Coroutine code here

        executor = my_coroutine()
        # Use the executor to run the coroutine in a separate thread
    """

    def wrapper(*args, **kwargs) -> ThreadedExecutor:
        return ThreadedExecutor(func(*args, **kwargs))

    return wrapper