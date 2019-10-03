"""bluepyopt.optimisations tests"""

import nose.tools as nt

import bluepyopt.optimisations
import bluepyopt.ephys.examples as examples

from nose.plugins.attrib import attr

import deap.tools


@attr('unit')
def test_DEAPOptimisation_constructor():
    "deapext.optimisation: Testing constructor DEAPOptimisation"

    optimisation = bluepyopt.deapext.optimisations.DEAPOptimisation(
        examples.simplecell.cell_evaluator, map_function=map)

    nt.assert_is_instance(
        optimisation,
        bluepyopt.deapext.optimisations.DEAPOptimisation)
    nt.assert_is_instance(
        optimisation.evaluator,
        bluepyopt.evaluators.Evaluator)

    nt.assert_raises(
        ValueError,
        bluepyopt.deapext.optimisations.DEAPOptimisation,
        examples.simplecell.cell_evaluator,
        selector_name='wrong')


@attr('unit')
def test_IBEADEAPOptimisation_constructor():
    "deapext.optimisation: Testing constructor IBEADEAPOptimisation"

    optimisation = bluepyopt.deapext.optimisations.IBEADEAPOptimisation(
        examples.simplecell.cell_evaluator, map_function=map)

    nt.assert_is_instance(
        optimisation,
        bluepyopt.deapext.optimisations.IBEADEAPOptimisation)


@attr('unit')
def test_DEAPOptimisation_run():
    "deapext.optimisation: Testing DEAPOptimisation run"

    optimisation = bluepyopt.optimisations.DEAPOptimisation(
        examples.simplecell.cell_evaluator, offspring_size=1)

    pop, hof, log, hist = optimisation.run(max_ngen=1)

    ind = [0.06007731830843009, 0.06508319290092013]
    nt.assert_equal(len(pop), 1)
    nt.assert_almost_equal(pop[0], ind)
    nt.assert_almost_equal(hof[0], ind)
    nt.assert_equal(log[0]['nevals'], 1)
    nt.assert_almost_equal(hist.genealogy_history[1], ind)


@attr('unit')
def test_selectorname():
    "deapext.optimisation: Testing selector_name argument"

    # Test default value
    ibea_optimisation = bluepyopt.optimisations.DEAPOptimisation(
        examples.simplecell.cell_evaluator)
    nt.assert_equal(ibea_optimisation.selector_name, 'IBEA')

    # Test NSGA2 selector
    nsga2_optimisation = bluepyopt.optimisations.DEAPOptimisation(
        examples.simplecell.cell_evaluator, selector_name='NSGA2')

    nt.assert_equal(
        nsga2_optimisation.toolbox.select.func,
        deap.tools.emo.selNSGA2)

    # Test IBEA selector
    ibea_optimisation = bluepyopt.optimisations.DEAPOptimisation(
        examples.simplecell.cell_evaluator, selector_name='IBEA')

    nt.assert_equal(
        ibea_optimisation.toolbox.select.func,
        bluepyopt.deapext.tools.selIBEA)
