"""bluepyopt.utils tests"""

import multiprocessing
import time

import bluepyopt.deapext.utils as utils
import nose.tools as nt

def flag(event):
    """Send a multiprocessing event."""
    time.sleep(1)
    event.set()

def catch_event(event):
    """Verify that run_next_gen changes when event is caught."""
    # None case
    nt.assert_true(utils.run_next_gen(True, None))

    # event is not set case
    nt.assert_true(utils.run_next_gen(True, event))

    # event is set by another process case
    time.sleep(2)
    nt.assert_equal(utils.run_next_gen(True, event), False)

def test_run_next_gen_condition():
    """deapext.utils: Testing run_next_gen."""
    event = multiprocessing.Event()
    p1 = multiprocessing.Process(target=catch_event, args=(event,))
    p2 = multiprocessing.Process(target=flag, args=(event,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()
