import numpy as np
from nose.tools import ok_

from bluepyopt.deapext.tools.selIBEA import _calc_fitness_components


def make_population():
    #TODO: Use mock instead
    class Individual(object):
        class Fitness(object):
            def __init__(self, wvalues):
                self.wvalues = wvalues
        def __init__(self, wvalues):
            self.fitness = Individual.Fitness(wvalues)

    FEATURES_COUNT = 5
    POPULATION_COUNT = 5
    MU, SIGMA = 0, 1
    np.random.seed(0)

    return [Individual(np.random.normal(MU, SIGMA, FEATURES_COUNT))
            for _ in range(POPULATION_COUNT)]


def test_calc_fitness_components():
    KAPPA = 0.05

    population = make_population()

    components = _calc_fitness_components(population, kappa=KAPPA)

    expected = np.array(
        [[1.00000000e+00, 4.30002298e-05, 4.26748513e-09, 2.06115362e-09, 9.71587289e-03],
         [5.11484499e-09, 1.00000000e+00, 2.02317572e-07, 4.79335491e-05, 3.52720088e-08],
         [6.75130710e-07, 1.23735078e+00, 1.00000000e+00, 2.77149617e-01, 8.37712763e-06],
         [2.06115362e-09, 3.04444453e-04, 8.15288827e-08, 1.00000000e+00, 2.06115362e-09],
         [2.06115362e-09, 6.75565231e-04, 4.39228177e-07, 2.12142918e-07, 1.00000000e+00]])

    ok_(np.allclose(expected, components))
