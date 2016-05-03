"""selIBEA tests"""

import numpy as np
from nose.tools import ok_, eq_

from bluepyopt.deapext.tools.selIBEA import (_calc_fitness_components,
                                             _mating_selection,
                                             )
from utils import make_mock_population

@attr('unit')
def test_calc_fitness_components():
    """selIBEA: test calc_fitness_components"""
    KAPPA = 0.05
    population = make_mock_population()

    components = _calc_fitness_components(population, kappa=KAPPA)

    expected = np.array(
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

    ok_(np.allclose(expected, components))


def test_mating_selection():
    PARENT_COUNT = 10
    population = make_mock_population()
    parents = _mating_selection(population, PARENT_COUNT, 5)
    eq_(len(parents), PARENT_COUNT)
    expected = [1, 1, 1, 1, 1, 0, 1, 0, 0, 0]
    eq_(expected, [ind.ibea_fitness for ind in parents])
