"""bluepyopt.optimisations tests"""


import bluepyopt.optimisations
import bluepyopt.ephys.examples.simplecell

import pytest
import numpy

import deap.tools


@pytest.mark.unit
def test_DEAPOptimisation_constructor():
    "deapext.optimisation: Testing constructor DEAPOptimisation"

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()
    optimisation = bluepyopt.deapext.optimisations.DEAPOptimisation(
        simplecell.cell_evaluator, map_function=map)

    assert isinstance(optimisation,
                      bluepyopt.deapext.optimisations.DEAPOptimisation)
    assert isinstance(optimisation.evaluator,
                      bluepyopt.evaluators.Evaluator)

    pytest.raises(
        ValueError,
        bluepyopt.deapext.optimisations.DEAPOptimisation,
        simplecell.cell_evaluator,
        selector_name='wrong')


@pytest.mark.unit
def test_IBEADEAPOptimisation_constructor():
    "deapext.optimisation: Testing constructor IBEADEAPOptimisation"

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()
    optimisation = bluepyopt.deapext.optimisations.IBEADEAPOptimisation(
        simplecell.cell_evaluator, map_function=map)

    assert isinstance(optimisation,
                      bluepyopt.deapext.optimisations.IBEADEAPOptimisation)


@pytest.mark.unit
def test_DEAPOptimisation_run():
    "deapext.optimisation: Testing DEAPOptimisation run"

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()
    optimisation = bluepyopt.optimisations.DEAPOptimisation(
        simplecell.cell_evaluator, offspring_size=1)

    pop, hof, log, hist = optimisation.run(max_ngen=1)

    ind = [0.06007731830843009, 0.06508319290092013]
    assert len(pop) == 1
    numpy.testing.assert_almost_equal(pop[0], ind)
    numpy.testing.assert_almost_equal(hof[0], ind)
    assert log[0]['nevals'] == 1
    numpy.testing.assert_almost_equal(hist.genealogy_history[1], ind)


@pytest.mark.unit
def test_DEAPOptimisation_run_from_parents():
    "deapext.optimisation: Testing DEAPOptimisation run using prior parents"

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()
    optimisation = bluepyopt.optimisations.DEAPOptimisation(
        simplecell.cell_evaluator, offspring_size=1)

    parent_population = [[0.060, 0.065]]
    pop, hof, log, hist = optimisation.run(max_ngen=0,
                                           parent_population=parent_population)

    assert len(pop) == 1
    numpy.testing.assert_almost_equal(pop[0], parent_population[0])


@pytest.mark.unit
def test_selectorname():
    "deapext.optimisation: Testing selector_name argument"

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()

    # Test default value
    ibea_optimisation = bluepyopt.optimisations.DEAPOptimisation(
        simplecell.cell_evaluator)
    assert ibea_optimisation.selector_name == 'IBEA'

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()

    # Test NSGA2 selector
    nsga2_optimisation = bluepyopt.optimisations.DEAPOptimisation(
        simplecell.cell_evaluator, selector_name='NSGA2')

    assert (
        nsga2_optimisation.toolbox.select.func
        == deap.tools.emo.selNSGA2)

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()

    # Test IBEA selector
    ibea_optimisation = bluepyopt.optimisations.DEAPOptimisation(
        simplecell.cell_evaluator, selector_name='IBEA')

    assert (
        ibea_optimisation.toolbox.select.func
        == bluepyopt.deapext.tools.selIBEA)
