#!/usr/bin/env python
import random
import time

import numpy as np

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

import stdputil as stl


def initRepeatBounded(container, func, bounds):
    """Call the function *container* with a generator function corresponding to the calling *len(bounds)* times the
     function *func* with arguments *bounds[i]*.

     Adapted from deap.tools.initRepeat to allow individual initialization using bounded random numbers.

    :param container:
    :param func:
    :param bounds:
    :return:
    """
    return container(func(*b) for b in bounds)


def graupnerParam(individual):
    """Create the parameter set for the Graupner model from an *individual*.

    :param individual: iterable
    :rtype : dict
    """
    gparam = dict(theta_d=1.0, theta_p=1.3, rho_star=0.5, beta=0.75)  # Fixed params

    # Add individual-specific parameters
    for name, value in zip(individual.gene_names, individual):
        gparam[name] = value

    return gparam


def evalGraupner(individual, protocols, sg, stderr):
    param = graupnerParam(individual)

    err = []
    for i in xrange(len(protocols)):
        res = stl.protocol_outcome(protocols[i], param)

        err.append(np.abs(sg[i] - res) / stderr[i])

    return err


# Select data
protocols, sg, stdev, stderr = stl.load_neviansakmann()

# Graupner model parameters and boundaries
graup_params = [('tau_ca', 1e-3, 100e-3),
                ('C_pre', 0.1, 5.0),
                ('C_post', 0.1, 5.0),
                ('gamma_d', 5.0, 5000.0),
                ('gamma_p', 5.0, 2500.0),
                ('sigma', 0.35, 70.7),
                ('tau', 2.5, 2500.0),
                ('D', 0.0, 50e-3),
                ('b', 1.0, 10.0)]

# Optimization parameters
OBJ = len(protocols)
NGEN = 2 ** 8
MU = 2 ** 10
LAMBDA = 2 ** 10
CXPB = 0.7
MUTPB = 0.3
ETA = 25

creator.create('Fitness', base.Fitness, weights=[-1.0] * OBJ, ids=[p.prot_id for p in protocols])
creator.create('Individual', list, fitness=creator.Fitness, gene_names=[gp[0] for gp in graup_params])

toolbox = base.Toolbox()
toolbox.register('attr_float', random.uniform)
toolbox.register('Individual', initRepeatBounded, creator.Individual, toolbox.attr_float,
                 [(gp[1], gp[2]) for gp in graup_params])
toolbox.register('population', tools.initRepeat, list, toolbox.Individual)
toolbox.register('evaluate', evalGraupner, protocols=protocols, sg=sg, stderr=stderr)
toolbox.register('mate', tools.cxUniform, indpb=0.2)
toolbox.register('mutate', tools.mutPolynomialBounded, eta=ETA, indpb=0.25, low=[gp[1] for gp in graup_params],
                 up=[gp[2] for gp in graup_params])
toolbox.register('select', tools.selIBEA)

if __name__ == '__main__':
    # Draw random seed
    seed = int(time.time())
    date = time.strftime('%y%m%d_%H%M%S', time.localtime(seed))
    random.seed(seed)

    pop = toolbox.population(n=MU)

    hof = tools.ParetoFront()

    stats = tools.MultiStatistics({'tau_ca': tools.Statistics(key=lambda ind: ind[0]),
                                   'C_pre': tools.Statistics(key=lambda ind: ind[1]),
                                   'C_post': tools.Statistics(key=lambda ind: ind[2]),
                                   'gamma_d': tools.Statistics(key=lambda ind: ind[3]),
                                   'gamma_p': tools.Statistics(key=lambda ind: ind[4]),
                                   'sigma': tools.Statistics(key=lambda ind: ind[5]),
                                   'tau': tools.Statistics(key=lambda ind: ind[6]),
                                   'D': tools.Statistics(key=lambda ind: ind[7]),
                                   'b': tools.Statistics(key=lambda ind: ind[8])})
    stats.register("mean", np.mean, axis=0)
    stats.register("std", np.std, axis=0)

    pop, logbook = algorithms.eaAlphaMuPlusLambda(pop, toolbox, MU, None, CXPB, MUTPB, NGEN, stats=stats,
                                                  halloffame=hof, verbose=True)
