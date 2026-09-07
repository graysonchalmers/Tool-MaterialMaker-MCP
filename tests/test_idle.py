import pytest
from mm_mcp.idle import IdleWatchdog


class FakeClock:
    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, idle_s: float) -> None:
        self.calls.append(idle_s)


def test_check_is_false_before_timeout():
    clock = FakeClock()
    on_expire = Recorder()
    watchdog = IdleWatchdog(100.0, clock=clock, on_expire=on_expire)
    clock.advance(99.0)
    assert watchdog.check() is False
    assert on_expire.calls == []


def test_check_is_true_at_timeout_and_calls_on_expire_once():
    clock = FakeClock()
    on_expire = Recorder()
    watchdog = IdleWatchdog(100.0, clock=clock, on_expire=on_expire)
    clock.advance(100.0)
    assert watchdog.check() is True
    assert on_expire.calls == [100.0]


def test_check_is_true_after_timeout():
    clock = FakeClock()
    on_expire = Recorder()
    watchdog = IdleWatchdog(100.0, clock=clock, on_expire=on_expire)
    clock.advance(150.0)
    assert watchdog.check() is True
    assert on_expire.calls == [150.0]


def test_touch_resets_the_idle_clock():
    clock = FakeClock()
    on_expire = Recorder()
    watchdog = IdleWatchdog(100.0, clock=clock, on_expire=on_expire)
    clock.advance(90.0)
    watchdog.touch()
    clock.advance(50.0)
    assert watchdog.check() is False
    assert on_expire.calls == []


def test_nonpositive_timeout_raises_value_error():
    with pytest.raises(ValueError):
        IdleWatchdog(0.0)
    with pytest.raises(ValueError):
        IdleWatchdog(-5.0)


def test_start_twice_keeps_one_thread():
    clock = FakeClock()
    watchdog = IdleWatchdog(10_000.0, clock=clock, poll_s=0.01)
    watchdog.start()
    thread_after_first_start = watchdog._thread
    watchdog.start()
    assert watchdog._thread is thread_after_first_start
