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

# pylint: disable=R0912, R0914

import logging
import numpy
import pickle
import random
from functools import partial

from deap import base
from deap import tools

from . import DEAPOptimisation, ListIndividual
from . import cma_es
from . import multi_cma_es

logger = logging.getLogger('__main__')


def _update_history_and_hof(halloffame, history, population):
    """
    Update the hall of fame with the generated individuals

    Note: History and Hall-of-Fame behave like dictionaries
    """
    if halloffame is not None:
        halloffame.update(population)

    history.update(population)


def _record_stats(stats, logbook, gen, population, evals, sigma):
    """Update the statistics with the new population"""
    record = stats.compile(population) if stats is not None else {}
    logbook.record(gen=gen, nevals=evals, sigma=sigma, **record)
    return record


def _ind_convert_space(ind, convert_fcn):
    return [f(x) for f, x in zip(convert_fcn, ind)]


class CMADEAPOptimisation(DEAPOptimisation):
    """CMA DEAP class"""

    def __init__(self,
                 evaluator=None,
                 use_scoop=False,
                 seed=1,
                 swarm_size=1,
                 centroids=None,
                 sigma=0.4,
                 lr_scale=1.,
                 map_function=None,
                 hof=None,
                 fitness_reduce=numpy.sum,
                 multi_objective=False):
        """Constructor

        Args:
            evaluator (Evaluator): Evaluator object
            swarm_size (int): Number of CMA-ES to run in parrallel
            centroids (list): list of initial guesses used as the starting 
                points of the CMA-ES
            sigma (float): initial standard deviation of the distribution
            lr_scale (float): scaling parameter for the learning rate of the CMA
            seed (float): Random number generator seed
            map_function (function): Function used to map (parallelise) the
                evaluation function calls
            hof (hof): Hall of Fame object
            fitness_reduce (fcn): function used to reduce the objective values
                to a single fitness score
        """

        super(CMADEAPOptimisation, self).__init__(evaluator=evaluator,
                                                  use_scoop=use_scoop,
                                                  seed=seed,
                                                  map_function=map_function,
                                                  hof=hof,
                                                  fitness_reduce=fitness_reduce)

        self.swarm_size = swarm_size
        self.lr_scale = lr_scale
        self.centroids = centroids
        self.sigma = sigma

        if multi_objective:
            self.cma_creator = multi_cma_es
        else:
            self.cma_creator = cma_es

        # In case initial guesses were provided, rescale them to the norm space
        if self.centroids is not None:
            self.centroids = [self.toolbox.Individual(_ind_convert_space(ind,
                                                                         self.to_norm))
                              for ind in centroids]

        # Instantiate functions converting individuals from the original
        # parameter space to (and from) a normalized space bounded to [-1.;1]
        bounds_radius = (self.ubounds - self.lbounds) / 2.
        bounds_mean = (self.ubounds + self.lbounds) / 2.
        self.to_norm = []
        self.to_space = []
        for r, m in zip(bounds_radius, bounds_mean):
            self.to_norm.append(
                partial(lambda param, bm, br: (param - bm) / br, bm=m, br=r))
            self.to_space.append(
                partial(lambda param, bm, br: (param * br) + bm, bm=m, br=r))

        # Overwrite the bounds with -1. and 1.
        self.lbounds = numpy.full(self.problem_size, -1.)
        self.ubounds = numpy.full(self.problem_size, 1.)

        self.setup_deap()

    def run(self,
            max_ngen=0,
            cp_frequency=1,
            continue_cp=False,
            cp_filename=None):
        """ Implementation of a single objective population of CMA-ES
            (using the termination criteria presented in *Hansen, 2009,
            Benchmarking a BI-Population CMA-ES on the BBOB-2009
            Function Testbed*).

        Args:
            max_ngen(int): Total number of generation to run
            cp_frequency(int): generations between checkpoints
            cp_filename(string): path to checkpoint filename
            continue_cp(bool): whether to continue
        """

        stats = self.get_stats()

        if continue_cp:
            # A file name has been given, then load the data from the file
            cp = pickle.load(open(cp_filename, "br"))
            gen = cp["generation"]
            self.hof = cp["halloffame"]
            logbook = cp["logbook"]
            history = cp["history"]
            random.setstate(cp["rndstate"])
            numpy.random.set_state(cp["np_rndstate"])
            swarm = cp["swarm"]

        else:
            history = tools.History()
            logbook = tools.Logbook()
            logbook.header = ["gen", "nevals", "sigma"] + stats.fields

            swarm = []
            for i in range(self.swarm_size):

                if self.centroids is None:
                    starter = self.toolbox.RandomIndividual()
                else:
                    starter = self.centroids[i % len(self.centroids)]

                # Instantiate the CMA strategies centered on the centroids
                swarm.append(self.cma_creator(centroid=starter,
                                              sigma=self.sigma,
                                              lr_scale=self.lr_scale,
                                              max_ngen=max_ngen,
                                              IndCreator=self.toolbox.Individual))
            gen = 1

        # Run until a termination criteria is met for every CMA strategy
        active_cma = numpy.sum([c.active for c in swarm])
        tot_pop = []
        while active_cma:
            logger.info("Generation {}".format(gen))
            logger.info("Number of active CMA strategy: {} / {}".format(
                active_cma, len(swarm)))

            # Generate the new populations
            n_out = 0
            for c in swarm:
                if c.active:
                    n_out += c.generate_new_pop(lbounds=self.lbounds,
                                                ubounds=self.ubounds)
            logger.info("Number of individuals outside of bounds: {} ({:.2f}%)"
                        "".format(n_out, 100. * n_out / swarm[0].lambda_ /
                                  self.swarm_size))

            # Get all the individuals in the original space for evaluation
            to_evaluate = []
            for c in swarm:
                if c.active:
                    to_evaluate += c.get_population(self.to_space)

            # Compute the fitnesses and dispatch them to all the CMA-ES
            fitnesses = self.toolbox.map(self.toolbox.evaluate, to_evaluate)
            fitnesses = list(map(list, fitnesses))
            nevals = len(to_evaluate)
            for c in swarm:
                if c.active:
                    c.set_fitness(fitnesses[:len(c.population)])
                    fitnesses = fitnesses[len(c.population):]

            # Update the hall of fame, history and logbook
            tot_pop = []
            for c in swarm:
                tot_pop += c.get_population(self.to_space)
            mean_sigma = numpy.mean([c.sigma for c in swarm])
            _update_history_and_hof(self.hof, history, tot_pop)
            record = _record_stats(stats, logbook, gen, tot_pop, nevals,
                                   mean_sigma)
            logger.info(logbook.stream)

            # Update the CMA strategy using the new fitness and check if
            # termination conditions were reached
            for c in swarm:
                if c.active:
                    c.update_strategy()
                    c.check_termination(gen)
            active_cma = numpy.sum([c.active for c in swarm])

            if cp_filename and cp_frequency and gen % cp_frequency == 0:
                cp = dict(population=tot_pop,
                          generation=gen,
                          halloffame=self.hof,
                          history=history,
                          logbook=logbook,
                          rndstate=random.getstate(),
                          np_rndstate=numpy.random.get_state(),
                          swarm=swarm)
                pickle.dump(cp, open(cp_filename, "wb"))
                logger.debug('Wrote checkpoint to %s', cp_filename)

            gen += 1

        return tot_pop, self.hof, logbook, history
