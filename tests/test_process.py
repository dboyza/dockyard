import sys
import threading

from dockyard.process import run


def test_large_bidirectional_io_does_not_deadlock():
    source = "import sys; sys.stderr.write('e'*200000); data=sys.stdin.read(); print(len(data))"
    result = run([sys.executable, "-c", source], input_text="x" * 300000, output_limit=1024)
    assert result.ok
    assert result.stdout.strip() == "300000"
    assert len(result.stderr) == 1024
    assert result.truncated


def test_timeout_kills_descendants_that_hold_output_pipes():
    source = "import os,time; child=os.fork(); time.sleep(30) if child == 0 else None"
    result = run([sys.executable, "-c", source], timeout=0.25)
    assert result.timed_out
    assert result.duration < 4


def test_cancellation_is_distinct_from_timeout():
    cancel = threading.Event()
    cancel.set()
    result = run([sys.executable, "-c", "import time; time.sleep(10)"], cancel=cancel)
    assert result.canceled
    assert not result.timed_out
    assert not result.ok


def test_arguments_are_literal_and_environment_is_explicit(tmp_path):
    payload = "$(touch should-not-exist); `echo bad`"
    source = "import os,sys; print(sys.argv[1]); print(os.environ['DOCKYARD_LAB'])"
    result = run([sys.executable, "-c", source, payload], cwd=tmp_path, env={"DOCKYARD_LAB": "one"})
    assert result.stdout.splitlines() == [payload, "one"]
    assert list(tmp_path.iterdir()) == []
