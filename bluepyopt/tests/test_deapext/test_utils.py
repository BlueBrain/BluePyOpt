"""bluepyopt.utils tests"""

import multiprocessing
import time

import bluepyopt.deapext.utils as utils
import pytest


def flag(event):
    """Send a multiprocessing event."""
    time.sleep(1)
    event.set()


def catch_event(event):
    """Verify that run_next_gen changes when event is caught."""
    # None case
    assert utils.run_next_gen(True, None)

    # event is not set case
    assert utils.run_next_gen(True, event)

    # event is set by another process case
    time.sleep(2)
    assert not(utils.run_next_gen(True, event))


@pytest.mark.unit
def test_run_next_gen_condition():
    """deapext.utils: Testing run_next_gen."""
    event = multiprocessing.Event()
    p1 = multiprocessing.Process(target=catch_event, args=(event,))
    p2 = multiprocessing.Process(target=flag, args=(event,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()
