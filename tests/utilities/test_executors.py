import multiprocessing
import sys
import threading
import time
from datetime import timedelta
from unittest.mock import MagicMock

import pytest

import prefect
from prefect.utilities.configuration import set_temporary_config
from prefect.utilities.executors import Heartbeat, timeout_handler, run_with_heartbeat


@pytest.mark.parametrize("interval", [0.2, 1])
@pytest.mark.parametrize("sleeptime", [1, 2])
def test_heartbeat_calls_function_on_interval(interval, sleeptime):
    class A:
        def __init__(self):
            self.called = 0

        def __call__(self):
            self.called += 1
            return True

    a = A()
    timer = Heartbeat(interval, a, None)
    timer.start()
    time.sleep(sleeptime)
    timer.cancel()
    assert a.called >= sleeptime / interval
    assert a.called <= sleeptime / interval + 1


def test_heartbeat_logs_if_first_call_fails(caplog):
    class A:
        def __init__(self):
            self.logger = prefect.utilities.logging.get_logger("A")

        def _heartbeat(self):
            raise SyntaxError("oops")

        @run_with_heartbeat
        def run(self):
            pass

    a = A()
    a.run()

    assert caplog.records

    log = caplog.records[0]
    assert log.name == "prefect.A"
    assert "Heartbeat" in log.message
    assert "zombie" in log.message


def test_heartbeat_logs_if_thread_dies(caplog):
    class A:
        def __init__(self):
            self.calls = 0
            self.logger = prefect.utilities.logging.get_logger("A")

        def _heartbeat(self):
            if self.calls == 1:
                raise SyntaxError("oops")
            return True

        @run_with_heartbeat
        def run(self):
            self.calls = 1
            time.sleep(1)

    a = A()
    with set_temporary_config({"cloud.heartbeat_interval": 0.25}):
        a.run()

    assert caplog.records

    log = caplog.records[0]
    assert log.name == "prefect.A"
    assert "Heartbeat thread appears to have died" in log.message
    assert "zombie" in log.message


def test_timeout_handler_times_out():
    slow_fn = lambda: time.sleep(2)
    with pytest.raises(TimeoutError):
        timeout_handler(slow_fn, timeout=1)


def test_timeout_handler_passes_args_and_kwargs_and_returns():
    def do_nothing(x, y=None):
        return x, y

    assert timeout_handler(do_nothing, 5, timeout=1, y="yellow") == (5, "yellow")


def test_timeout_handler_doesnt_swallow_bad_args():
    def do_nothing(x, y=None):
        return x, y

    with pytest.raises(TypeError):
        timeout_handler(do_nothing, timeout=1)

    with pytest.raises(TypeError):
        timeout_handler(do_nothing, 5, timeout=1, z=10)

    with pytest.raises(TypeError):
        timeout_handler(do_nothing, 5, timeout=1, y="s", z=10)


def test_timeout_handler_reraises():
    def do_something():
        raise ValueError("test")

    with pytest.raises(ValueError, match="test"):
        timeout_handler(do_something, timeout=1)


@pytest.mark.skipif(sys.platform == "win32", reason="Test fails on Windows")
def test_timeout_handler_allows_function_to_spawn_new_process():
    def my_process():
        p = multiprocessing.Process(target=lambda: 5)
        p.start()
        p.join()
        p.terminate()

    assert timeout_handler(my_process, timeout=1) is None


@pytest.mark.skipif(sys.platform == "win32", reason="Test fails on Windows")
def test_timeout_handler_allows_function_to_spawn_new_thread():
    def my_thread():
        t = threading.Thread(target=lambda: 5)
        t.start()
        t.join()

    assert timeout_handler(my_thread, timeout=1) is None


def test_timeout_handler_doesnt_do_anything_if_no_timeout(monkeypatch):
    monkeypatch.delattr(prefect.utilities.executors, "ThreadPoolExecutor")
    with pytest.raises(NameError):  # to test the test's usefulness...
        timeout_handler(lambda: 4, timeout=1)
    assert timeout_handler(lambda: 4) == 4


def test_timeout_handler_preserves_context():
    def my_fun(x, **kwargs):
        return prefect.context.get("test_key")

    with prefect.context(test_key=42):
        res = timeout_handler(my_fun, 2, timeout=1)

    assert res == 42


def test_timeout_handler_preserves_logging(caplog):
    timeout_handler(prefect.Flow("logs").run, timeout=2)
    assert len(caplog.records) >= 2  # 1 INFO to start, 1 INFO to end
