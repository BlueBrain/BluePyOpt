"""bluepyopt.stoppingCriteria tests"""

import nose.tools as nt

import bluepyopt.stoppingCriteria

from nose.plugins.attrib import attr

import deap.tools


@attr('unit')
def test_MaxNGen():
    """deapext.stoppingCriteria: Testing MaxNGen"""

    max_gen = 3
    criteria = bluepyopt.deapext.stoppingCriteria.MaxNGen(max_gen)

    nt.assert_equal(criteria.criteria_met, False)
    criteria.check({"gen": max_gen + 1})
    nt.assert_equal(criteria.criteria_met, True)
    criteria.reset()
    criteria.check({"gen": max_gen})
    nt.assert_equal(criteria.criteria_met, False)
