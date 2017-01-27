"""bluepyopt.optimisations tests"""

import nose.tools as nt

import bluepyopt.optimisations
import bluepyopt.ephys.examples as examples

from nose.plugins.attrib import attr

import deap.tools


@attr('unit')
def test_DEAPOptimisation_constructor():
    "deapext.optimisation: Testing constructor DEAPOptimisation"

    optimisation = bluepyopt.optimisations.DEAPOptimisation(
        examples.simplecell.cell_evaluator)

    nt.assert_is_instance(
        optimisation,
        bluepyopt.optimisations.DEAPOptimisation)
    nt.assert_is_instance(
        optimisation.evaluator,
        bluepyopt.evaluators.Evaluator)


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
