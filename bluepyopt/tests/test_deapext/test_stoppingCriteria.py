"""bluepyopt.stoppingCriteria tests"""


import bluepyopt.stoppingCriteria

import pytest


@pytest.mark.unit
def test_MaxNGen():
    """deapext.stoppingCriteria: Testing MaxNGen"""

    max_gen = 3
    criteria = bluepyopt.deapext.stoppingCriteria.MaxNGen(max_gen)

    assert criteria.criteria_met is False
    criteria.check({"gen": max_gen + 1})
    assert criteria.criteria_met is True
    criteria.reset()
    criteria.check({"gen": max_gen})
    assert criteria.criteria_met is False
