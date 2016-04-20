"""Optimisation class"""

"""
Copyright (c) 2016, EPFL/Blue Brain Project

 This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>

 This library is free software; you can redistribute it and/or modify it under
 the terms of the GNU Lesser General Public License version 3.0 as published
 by the Free Software Foundation.

 This library is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
 details.

 You should have received a copy of the GNU Lesser General Public License
 along with this library; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# pylint: disable=R0914, R0912


import random
import logging

import deap
import deap.algorithms
import deap.tools
import pickle

logger = logging.getLogger('__main__')


def eaAlphaMuPlusLambdaCheckpoint(
        population,
        toolbox,
        mu,
        _,
        cxpb,
        mutpb,
        ngen,
        stats=None,
        halloffame=None,
        cp_frequency=1,
        cp_filename=None,
        continue_cp=False):
    r"""This is the :math:`(~\alpha,\mu~,~\lambda)` evolutionary algorithm."""

    if continue_cp:
        # A file name has been given, then load the data from the file
        cp = pickle.load(open(cp_filename, "r"))
        population = cp["population"]
        parents = cp["parents"]
        start_gen = cp["generation"]
        halloffame = cp["halloffame"]
        logbook = cp["logbook"]
        history = cp["history"]
        random.setstate(cp["rndstate"])
    else:
        # Start a new evolution
        start_gen = 1
        parents = population[:]
        logbook = deap.tools.Logbook()
        logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])
        history = deap.tools.History()

        # TODO this first loop should be not be repeated !

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in population if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        record = stats.compile(population) if stats is not None else {}
        logbook.record(gen=start_gen, nevals=len(invalid_ind), **record)

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(population)

        if history is not None:
            history.update(population)

    # if history is not None:
    #    toolbox.decorate("mate", history.decorator)
    #    toolbox.decorate("mutate", history.decorator)

    # Begin the generational process
    for gen in range(start_gen + 1, ngen + 1):
        # Vary the parents
        if hasattr(toolbox, 'variate'):
            offspring = toolbox.variate(parents, toolbox, cxpb, mutpb)
        else:
            offspring = deap.algorithms.varAnd(parents, toolbox, cxpb, mutpb)

        population[:] = parents + offspring

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offspring)

        if history is not None:
            history.update(offspring)

        # Select the next generation parents
        parents[:] = toolbox.select(population, mu)

        # Update the statistics with the new population
        record = stats.compile(population) if stats is not None else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)

        logger.info(logbook.stream)

        if cp_filename and cp_frequency:
            if gen % cp_frequency == 0:
                cp = dict(population=population, generation=gen,
                          parents=parents,
                          halloffame=halloffame,
                          history=history,
                          logbook=logbook, rndstate=random.getstate())
                pickle.dump(
                    cp,
                    open(cp_filename, "wb"))
                logger.debug('Wrote checkpoint to %s', cp_filename)

    return population, logbook, history
