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
import numpy
import deap.algorithms
import deap.tools
import pickle
logger = logging.getLogger('__main__')


def _evaluate_invalid_fitness(toolbox, population):
    '''Evaluate the individuals with an invalid fitness

    Returns the count of individuals with invalid fitness
    '''
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    return len(invalid_ind)


def _update_history_and_hof(halloffame, history, population):
    '''Update the hall of fame with the generated individuals

    Note: History and Hall-of-Fame behave like dictionaries
    '''
    if halloffame is not None:
        halloffame.update(population)

    history.update(population)


def _record_stats(stats, logbook, gen, population, invalid_count):
    '''Update the statistics with the new population'''
    record = stats.compile(population) if stats is not None else {}
    logbook.record(gen=gen, nevals=invalid_count, **record)


def _get_offspring(parents, toolbox, cxpb, mutpb):
    '''return the offsprint, use toolbox.variate if possible'''
    if hasattr(toolbox, 'variate'):
        return toolbox.variate(parents, toolbox, cxpb, mutpb)
    return deap.algorithms.varAnd(parents, toolbox, cxpb, mutpb)


def _get_median(population, percentage=0.3):
    '''return the median of the X% fittest individuals'''
    _ = [ind.fitness.sum for ind in population]
    _.sort()
    return numpy.median(_[:int(percentage * len(_))])


def eaAlphaMuPlusLambdaCheckpoint(
        population,
        toolbox,
        mu,
        cxpb,
        mutpb,
        ngen,
        stagnation=0,
        stagnation_perc=0.3,
        stats=None,
        halloffame=None,
        cp_frequency=1,
        cp_filename=None,
        continue_cp=False):
    r"""This is the :math:`(~\alpha,\mu~,~\lambda)` evolutionary algorithm

    Args:
        population(list of deap Individuals)
        toolbox(deap Toolbox)
        mu(int): Total parent population size of EA
        cxpb(float): Crossover probability
        mutpb(float): Mutation probability
        ngen(int): Total number of generation to run
        stagnation(int): number of evals after which to stop if the fitness stops improving
        stagnation_perc (float): percentage of the population to use for the stagnation criteria
        stats(deap.tools.Statistics): generation of statistics
        halloffame(deap.tools.HallOfFame): hall of fame
        cp_frequency(int): generations between checkpoints
        cp_filename(string): path to checkpoint filename
        continue_cp(bool): whether to continue
    """

    if continue_cp:
        # A file name has been given, then load the data from the file
        cp = pickle.load(open(cp_filename, "rb"))
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
        invalid_count = _evaluate_invalid_fitness(toolbox, population)
        _update_history_and_hof(halloffame, history, population)
        _record_stats(stats, logbook, start_gen, population, invalid_count)

    # Begin the generational process
    tot_nevals = 0
    for gen in range(start_gen + 1, ngen + 1):
        offspring = _get_offspring(parents, toolbox, cxpb, mutpb)

        population = parents + offspring

        invalid_count = _evaluate_invalid_fitness(toolbox, offspring)
        _update_history_and_hof(halloffame, history, population)
        _record_stats(stats, logbook, gen, population, invalid_count)
        tot_nevals += invalid_count

        # Select the next generation parents
        parents = toolbox.select(population, mu)

        logger.info(logbook.stream)

        if(cp_filename and cp_frequency and
           gen % cp_frequency == 0):
            cp = dict(population=population,
                      generation=gen,
                      parents=parents,
                      halloffame=halloffame,
                      history=history,
                      logbook=logbook,
                      rndstate=random.getstate())
            pickle.dump(cp, open(cp_filename, "wb"))
            logger.debug('Wrote checkpoint to %s', cp_filename)

        if stagnation:
            # Check if the median of the best individuals improved
            med = _get_median(population, stagnation_perc)
            if gen == start_gen+1 or med < best_med:
                best_nevals = tot_nevals
                best_med = med
            if tot_nevals-best_nevals > stagnation:
                logger.info("Reached stagnation termination criteria")
                break

    return population, halloffame, logbook, history
