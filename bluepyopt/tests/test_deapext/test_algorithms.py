"""bluepyopt.optimisations tests"""

import numpy
import deap.creator
import deap.benchmarks

import nose.tools as nt

import bluepyopt.deapext.algorithms

from nose.plugins.attrib import attr


@attr('unit')
def test_DEAPOptimisation_constructor():
    """deapext.algorithms: Testing constructor eaAlphaMuPlusLambdaCheckpoint"""

    deap.creator.create('fit', deap.base.Fitness, weights=(-1.0,))
    deap.creator.create(
        'ind',
        numpy.ndarray,
        fitness=deap.creator.__dict__['fit'])

    population = [deap.creator.__dict__['ind'](x)
                  for x in numpy.random.uniform(0, 1,
                                                (10, 2))]

    toolbox = deap.base.Toolbox()
    toolbox.register("evaluate", deap.benchmarks.sphere)

    population, logbook, history = \
        bluepyopt.deapext.algorithms.eaAlphaMuPlusLambdaCheckpoint(
            population=population,
            toolbox=toolbox,
            mu=1.0,
            cxpb=1.0,
            mutpb=1.0,
            ngen=1,
            stats=None,
            halloffame=None,
            cp_frequency=1,
            cp_filename=None,
            continue_cp=False)

    nt.assert_true(isinstance(population, list))
    nt.assert_equal(len(population), 10)
    nt.assert_true(isinstance(logbook, deap.tools.support.Logbook))
    nt.assert_true(isinstance(history, deap.tools.support.History))
