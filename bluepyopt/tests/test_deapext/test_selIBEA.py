"""selIBEA tests"""


import deap
import numpy

import bluepyopt.deapext
from bluepyopt.deapext.tools.selIBEA \
    import (_calc_fitness_components, _mating_selection,)
from .deapext_test_utils import make_mock_population

import pytest


@pytest.mark.unit
def test_calc_fitness_components():
    """deapext.selIBEA: test calc_fitness_components"""
    KAPPA = 0.05
    population = make_mock_population()

    components = _calc_fitness_components(population, kappa=KAPPA)

    expected = numpy.array(
        [
            [1.00000000e+00, 4.30002298e-05, 4.26748513e-09, 2.06115362e-09,
             9.71587289e-03],
            [5.11484499e-09, 1.00000000e+00, 2.02317572e-07, 4.79335491e-05,
             3.52720088e-08],
            [6.75130710e-07, 1.23735078e+00, 1.00000000e+00, 2.77149617e-01,
             8.37712763e-06],
            [2.06115362e-09, 3.04444453e-04, 8.15288827e-08, 1.00000000e+00,
             2.06115362e-09],
            [2.06115362e-09, 6.75565231e-04, 4.39228177e-07, 2.12142918e-07,
             1.00000000e+00]
        ])

    assert numpy.allclose(expected, components)


@pytest.mark.unit
def test_mating_selection():
    """deapext.selIBEA: test mating selection"""

    PARENT_COUNT = 10
    population = make_mock_population()
    parents = _mating_selection(population, PARENT_COUNT, 5)
    assert len(parents) == PARENT_COUNT
    expected = [1, 1, 1, 1, 1, 0, 1, 0, 0, 0]
    assert expected == [ind.ibea_fitness for ind in parents]


@pytest.mark.unit
def test_selibea_init():
    """deapext.selIBEA: test selIBEA init"""

    deap.creator.create('fit', deap.base.Fitness, weights=(-1.0,))
    deap.creator.create(
        'ind',
        numpy.ndarray,
        fitness=deap.creator.__dict__['fit'])

    numpy.random.seed(1)

    population = [deap.creator.__dict__['ind'](x)
                  for x in numpy.random.uniform(0, 1,
                                                (10, 2))]

    for ind in population:
        ind.fitness.values = (numpy.random.uniform(0, 1), )

    mu = 5
    parents = bluepyopt.deapext.tools.selIBEA(population, mu)

    assert len(parents) == mu
