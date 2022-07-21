"""Multi Objective CMA-es class"""

"""
Copyright (c) 2016-2022, EPFL/Blue Brain Project

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
import copy
from math import log

import deap
from deap import base
from deap import cma

from .stoppingCriteria import MaxNGen
from . import utils
from . import hype

logger = logging.getLogger("__main__")


def get_hyped(pop, ubound_score=250., threshold_improvement=240.):
    """Compute the hypervolume contribution of each individual.
    The fitness space is first bounded and all dimension who do not show
    improvement are ignored.
    """

    # Cap the obj at 250
    points = numpy.array([ind.fitness.values for ind in pop])
    points[points > ubound_score] = ubound_score
    lbounds = numpy.min(points, axis=0)
    ubounds = numpy.max(points, axis=0)

    # Remove the dimensions that do not show any improvement
    to_remove = []
    for i, lb in enumerate(lbounds):
        if lb >= threshold_improvement:
            to_remove.append(i)
    points = numpy.delete(points, to_remove, axis=1)
    lbounds = numpy.delete(lbounds, to_remove)
    ubounds = numpy.delete(ubounds, to_remove)

    if not len(lbounds):
        logger.warning("No dimension along which to compute the hypervolume.")
        return [0.] * len(pop)

    # Rescale the objective space
    # Note: 2 here is a magic number used to make the hypercube larger than it
    # really is. It makes sure that the individual always have a non-zero
    # hyper-volume contribution and improves the results while avoiding an
    # edge case.
    points = (points - lbounds) / numpy.max(ubounds.flatten())
    ubounds = numpy.max(points, axis=0) + 2.0

    hv = hype.hypeIndicatorSampled(
        points=points, bounds=ubounds, k=5, nrOfSamples=1000000
    )
    return hv


class CMA_MO(cma.StrategyMultiObjective):
    """Multiple objective covariance matrix adaption"""

    def __init__(
        self,
        centroids,
        offspring_size,
        sigma,
        max_ngen,
        IndCreator,
        RandIndCreator,
        weight_hv=0.5,
        map_function=None,
        use_scoop=False,
    ):
        """Constructor

        Args:
            centroid (list): initial guess used as the starting point of
            the CMA-ES
            offspring_size (int): number of offspring individuals in each
                 generation
            sigma (float): initial standard deviation of the distribution
            max_ngen (int): total number of generation to run
            IndCreator (fcn): function returning an individual of the pop
            RandIndCreator (fcn): function creating a random individual.
            weight_hv (float): between 0 and 1. Weight given to the
                hypervolume contribution when computing the score of an
                individual in MO-CMA. The weight of the fitness contribution
                is computed as 1 - weight_hv.
            map_function (map): function used to map (parallelize) the
                 evaluation function calls
            use_scoop (bool): use scoop map for parallel computation
        """

        if offspring_size is None:
            lambda_ = int(4 + 3 * log(len(RandIndCreator())))
        else:
            lambda_ = offspring_size

        if centroids is None:
            starters = [RandIndCreator() for i in range(lambda_)]
        else:
            if len(centroids) != lambda_:
                from itertools import cycle

                generator = cycle(centroids)
                starters = [
                    copy.deepcopy(next(generator)) for i in range(lambda_)
                ]
            else:
                starters = centroids

        cma.StrategyMultiObjective.__init__(
            self, starters, sigma, mu=int(lambda_ * 0.5), lambda_=lambda_
        )

        self.population = []
        self.problem_size = len(starters[0])

        self.weight_hv = weight_hv

        self.map_function = map_function
        self.use_scoop = use_scoop

        # Toolbox specific to this CMA-ES
        self.toolbox = base.Toolbox()
        self.toolbox.register("generate", self.generate, IndCreator)
        self.toolbox.register("update", self.update)

        if self.use_scoop:
            if self.map_function:
                raise Exception(
                    "Impossible to use scoop and provide self defined map "
                    "function: %s" % self.map_function
                )
            from scoop import futures

            self.map_function = futures.map

        # Set termination conditions
        self.active = True
        if max_ngen <= 0:
            max_ngen = 100 + 50 * (self.problem_size + 3) ** 2 / numpy.sqrt(
                self.lambda_
            )

        self.stopping_conditions = [MaxNGen(max_ngen)]

    def _select(self, candidates):
        """Select the best candidates of the population

         Fill the next population (chosen) with the Pareto fronts until there
         is not enough space. When an entire front does not fit in the space
         left we rely on a mixture of hypervolume and fitness. The respective
         weights of hypervolume and fitness are "hv" and "1-hv". The remaining
         fronts are explicitly not chosen"""

        if self.weight_hv == 0.0:
            fit = [numpy.sum(ind.fitness.values) for ind in candidates]
            idx_scores = list(numpy.argsort(fit))

        elif self.weight_hv == 1.0:
            hv = get_hyped(candidates)
            idx_scores = list(numpy.argsort(hv))[::-1]

        else:
            hv = get_hyped(candidates)
            idx_hv = list(numpy.argsort(hv))[::-1]
            fit = [numpy.sum(ind.fitness.values) for ind in candidates]
            idx_fit = list(numpy.argsort(fit))
            scores = []
            for i in range(len(candidates)):
                score = (self.weight_hv * idx_hv.index(i)) + (
                    (1.0 - self.weight_hv) * idx_fit.index(i)
                )
                scores.append(score)
            idx_scores = list(numpy.argsort(scores))

        chosen = [candidates[i] for i in idx_scores[: self.mu]]
        not_chosen = [candidates[i] for i in idx_scores[self.mu:]]
        return chosen, not_chosen

    def get_population(self, to_space):
        """Returns the population in the original parameter space"""
        pop = copy.deepcopy(self.population)
        for i, ind in enumerate(pop):
            for j, v in enumerate(ind):
                pop[i][j] = to_space[j](v)
        return pop

    def get_parents(self, to_space):
        """Returns the population in the original parameter space"""
        pop = copy.deepcopy(self.parents)
        for i, ind in enumerate(pop):
            for j, v in enumerate(ind):
                pop[i][j] = to_space[j](v)
        return pop

    def generate_new_pop(self, lbounds, ubounds):
        """Generate a new population bounded in the normalized space"""
        self.population = self.toolbox.generate()
        return utils.bound(self.population, lbounds, ubounds)

    def update_strategy(self):
        self.toolbox.update(self.population)

    def set_fitness(self, fitnesses):
        for f, ind in zip(fitnesses, self.population):
            ind.fitness.values = f

    def set_fitness_parents(self, fitnesses):
        for f, ind in zip(fitnesses, self.parents):
            ind.fitness.values = f

    def check_termination(self, gen):
        stopping_params = {
            "gen": gen,
            "population": self.population,
        }

        [c.check(stopping_params) for c in self.stopping_conditions]
        for c in self.stopping_conditions:
            if c.criteria_met:
                logger.info(
                    "CMA stopped because of termination criteria: " +
                    " ".join(c.name)
                )
                self.active = False
