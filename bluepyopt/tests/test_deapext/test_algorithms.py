"""bluepyopt.optimisations tests"""

import numpy
import mock

import deap.creator
import deap.benchmarks

import nose.tools as nt

import bluepyopt.deapext.algorithms

from nose.plugins.attrib import attr


@attr('unit')
def test_eaAlphaMuPlusLambdaCheckpoint():
    """deapext.algorithms: Testing eaAlphaMuPlusLambdaCheckpoint"""

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
    toolbox.register("mate", lambda x, y: (x, y))
    toolbox.register("mutate", lambda x: (x,))
    toolbox.register("select", lambda pop, mu: pop)
    toolbox.register("variate", lambda par, toolb, cxpb, mutpb: par)

    population, hof, logbook, history = \
        bluepyopt.deapext.algorithms.eaAlphaMuPlusLambdaCheckpoint(
            population=population,
            toolbox=toolbox,
            mu=1.0,
            cxpb=1.0,
            mutpb=1.0,
            ngen=2,
            stats=None,
            halloffame=None,
            cp_frequency=1,
            cp_filename=None,
            continue_cp=False)

    nt.assert_true(isinstance(population, list))
    nt.assert_equal(len(population), 20)
    nt.assert_true(isinstance(logbook, deap.tools.support.Logbook))
    nt.assert_true(isinstance(history, deap.tools.support.History))


@attr('unit')
def test_eaAlphaMuPlusLambdaCheckpoint_with_checkpoint():
    """deapext.algorithms: Testing eaAlphaMuPlusLambdaCheckpoint"""

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
    toolbox.register("mate", lambda x, y: (x, y))
    toolbox.register("mutate", lambda x: (x,))
    toolbox.register("select", lambda pop, mu: pop)

    with mock.patch('pickle.dump'):
        with mock.patch('bluepyopt.deapext.algorithms.open',
                        return_value=None):
            population, hof, logbook, history = \
                bluepyopt.deapext.algorithms.eaAlphaMuPlusLambdaCheckpoint(
                    population=population,
                    toolbox=toolbox,
                    mu=1.0,
                    cxpb=1.0,
                    mutpb=1.0,
                    ngen=2,
                    stats=None,
                    halloffame=None,
                    cp_frequency=1,
                    cp_filename='cp_test',
                    continue_cp=False)

    import random
    with mock.patch('pickle.load', return_value={'population': population,
                                                 'logbook': logbook,
                                                 'history': history,
                                                 'parents': None,
                                                 'halloffame': None,
                                                 'rndstate': random.getstate(),
                                                 'generation': 1}):
        with mock.patch('bluepyopt.deapext.algorithms.open',
                        return_value=None):
            new_population, hof, logbook, history = \
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
                    cp_filename='cp_test',
                    continue_cp=True)

    nt.assert_equal(new_population, population)
