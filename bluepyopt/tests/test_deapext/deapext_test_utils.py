import random
import numpy as np

from deap import base
from deap import creator


def make_mock_population(features_count=5, population_count=5):
    """Create pop of inds that we have full control over,creating a DEAP one"""
    # TODO: Use mock instead
    class Individual(object):
        class Fitness(object):
            def __init__(self, wvalues, valid):
                self.wvalues = wvalues
                self.valid = valid

        def __init__(self, wvalues, valid, ibea_fitness):
            self.fitness = Individual.Fitness(wvalues, valid)
            self.ibea_fitness = ibea_fitness

    MU, SIGMA = 0, 1
    np.random.seed(0)
    random.seed(0)

    # create individuals w/ a random weight values, and an ibea_fitness
    # according to their position
    return [Individual(np.random.normal(MU, SIGMA, features_count), bool(
        i % 2), i) for i in range(population_count)]


def make_population(features_count=5, population_count=5):
    '''create population w/ DEAP Individuals
    '''

    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    random.seed(0)

    population = [creator.Individual(range(i * features_count,
                                           (i + 1) * features_count))
                  for i in range(population_count)]
    return population
