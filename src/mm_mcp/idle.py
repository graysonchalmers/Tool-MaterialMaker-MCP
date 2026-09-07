"""Idle-exit watchdog for the stdio server: exit the process after a quiet
period with no tool activity. Opt-in via MM_IDLE_EXIT_MINUTES (0 = off).
Claude Code does not restart an exited stdio server, so a long-idle session's
next tool call fails until the session reconnects; that is the intended
trade-off for cleaning up abandoned sessions."""
import os
import sys
import threading
import time


class IdleWatchdog:
    def __init__(self, timeout_s: float, *, clock=time.monotonic, on_expire=None,
                 poll_s: float | None = None):
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        self._timeout = float(timeout_s)
        self._clock = clock
        self._on_expire = on_expire or self._default_exit
        self._poll = poll_s if poll_s is not None else max(1.0, min(30.0, self._timeout / 4))
        self._last = clock()
        self._lock = threading.Lock()
        self._thread = None

    def touch(self) -> None:
        with self._lock:
            self._last = self._clock()

    def idle_seconds(self) -> float:
        with self._lock:
            return self._clock() - self._last

    def expired(self) -> bool:
        return self.idle_seconds() >= self._timeout

    def check(self) -> bool:
        """One poll: fire on_expire and return True if the quiet period elapsed."""
        if self.expired():
            self._on_expire(self.idle_seconds())
            return True
        return False

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, name="mm-mcp-idle", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while not self.check():
            time.sleep(self._poll)

    def _default_exit(self, idle_s: float) -> None:
        print(f"mm-mcp: no tool activity for {idle_s / 60:.0f} min "
              f"(MM_IDLE_EXIT_MINUTES={self._timeout / 60:.0f}); exiting.", file=sys.stderr, flush=True)
        os._exit(0)
