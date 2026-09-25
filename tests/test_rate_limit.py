import pytest

import src.task10_generation as gen


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.slept = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(gen.time, "monotonic", fake.monotonic)
    monkeypatch.setattr(gen.time, "sleep", fake.sleep)
    monkeypatch.setattr(gen, "LLM_RPM", 3)
    monkeypatch.setattr(gen, "_call_times", gen.deque())
    return fake


def test_waits_only_when_window_is_full(clock, monkeypatch):
    monkeypatch.setattr(gen, "_send", lambda s, u: "ok")
    for _ in range(3):
        gen.call_llm("s", "u")
        clock.now += 5
    assert clock.slept == []  # 3 request trong 15s: chưa chạm giới hạn

    gen.call_llm("s", "u")  # request thứ 4 ở t=15 -> chờ tới t=60
    assert clock.slept == [45]


def test_retries_after_429_then_gives_up(clock, monkeypatch):
    class Limited(Exception):
        code = 429

    calls = []

    def always_limited(s, u):
        calls.append(clock.now)
        raise Limited()

    monkeypatch.setattr(gen, "_send", always_limited)
    with pytest.raises(Limited):
        gen.call_llm("s", "u")
    assert len(calls) == gen.LLM_MAX_RETRIES + 1
    assert gen.RATE_LIMIT_COOLDOWN in clock.slept


def test_other_errors_are_not_retried(clock, monkeypatch):
    calls = []

    def broken(s, u):
        calls.append(1)
        raise ValueError("bad request")

    monkeypatch.setattr(gen, "_send", broken)
    with pytest.raises(ValueError):
        gen.call_llm("s", "u")
    assert calls == [1]
