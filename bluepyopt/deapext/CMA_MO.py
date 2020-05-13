"""Multi Objective CMA-es class"""

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
import copy
from math import log

import deap
from deap import base
from deap import cma

from .stoppingCriteria import MaxNGen
from . import utils

logger = logging.getLogger('__main__')

from deap.tools._hypervolume import hv as hv_c


def get_hv(to_evaluate):
    i = to_evaluate[0]
    wobj = to_evaluate[1]
    ref = to_evaluate[2]
    return hv_c.hypervolume(numpy.concatenate((wobj[:i], wobj[i + 1:])), ref)


def contribution(to_evaluate):
    def _reduce_method(meth):
        """Overwrite reduce"""
        return (getattr, (meth.__self__, meth.__func__.__name__))

    import copyreg
    import types
    copyreg.pickle(types.MethodType, _reduce_method)
    import pebble

    with pebble.ProcessPool(max_tasks=1) as pool:
        tasks = pool.schedule(get_hv, kwargs={'to_evaluate': to_evaluate})
        response = tasks.result()

    return response


class CMA_MO(cma.StrategyMultiObjective):
    """Multiple objective covariance matrix adaption"""

    def __init__(self,
                 centroids,
                 offspring_size,
                 sigma,
                 max_ngen,
                 IndCreator,
                 RandIndCreator,
                 map_function=None,
                 use_scoop=False):
        """Constructor

        Args:
            centroid (list): initial guess used as the starting point of
            the CMA-ES
            sigma (float): initial standard deviation of the distribution
            max_ngen (int): total number of generation to run
            IndCreator (fcn): function returning an individual of the pop
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
                starters = [next(generator) for i in range(lambda_)]
            else:
                starters = centroids

        cma.StrategyMultiObjective.__init__(self, starters, sigma,
                                            mu=int(lambda_ * 0.5),
                                            lambda_=lambda_)

        self.population = []
        self.problem_size = len(starters[0])

        self.map_function = map_function
        self.use_scoop = use_scoop

        # Toolbox specific to this CMA-ES
        self.toolbox = base.Toolbox()
        self.toolbox.register("generate", self.generate, IndCreator)
        self.toolbox.register("update", self.update)

        if self.use_scoop:
            if self.map_function:
                raise Exception(
                    'Impossible to use scoop is providing self defined map '
                    'function: %s' % self.map_function)
            from scoop import futures
            self.toolbox.register("map", futures.map)
        elif self.map_function:
            self.toolbox.register("map", self.map_function)

        # Set termination conditions
        self.active = True
        if max_ngen <= 0:
            max_ngen = 100 + 50 * (self.problem_size + 3) ** 2 / numpy.sqrt(
                self.lambda_)

        self.stopping_conditions = [MaxNGen(max_ngen)]

    def hyper_volume(self, front):
        """Compute the hypervolume contribution of each individual"""
        wobj = numpy.array([ind.fitness.values for ind in front])
        obj_ranges = (numpy.max(wobj, axis=0) - numpy.min(wobj, axis=0))
        ref = numpy.max(wobj, axis=0) + 1

        # Above 23 dimension, the hypervolume computation is too slow,
        # we settle for the 23 dimension showing the largest range of values
        max_ndim = 23
        if len(ref) > max_ndim:
            idxs = list(range(len(ref)))
            idxs = [idxs[k] for k in numpy.argsort(obj_ranges)]
            idxs = idxs[::-1]
            idxs = idxs[:max_ndim]
            wobj = wobj[:, idxs]
            ref = ref[idxs]

        # Prepare the data and send it to multiprocess
        for i in range(len(front)):
            to_evaluate.append([i, numpy.copy(wobj), numpy.copy(ref)])
        contrib_values = self.toolbox.map(contribution, to_evaluate)

        return list(contrib_values)

    def _select(self, candidates):
        """Select the best candidates of the population

        Fill the next population (chosen) with the Pareto fronts until there is
        not enouch space. When an entire front does not fit in the space left
        we rely on the hypervolume for this front. The remaining fronts are
        explicitly not chosen"""

        if len(candidates) <= self.mu:
            return candidates, []

        pareto_fronts = deap.tools.sortLogNondominated(candidates,
                                                       len(candidates))

        chosen = list()
        mid_front = None
        not_chosen = list()

        full = False
        for front in pareto_fronts:
            if len(chosen) + len(front) <= self.mu and not full:
                chosen += front
            elif mid_front is None and len(chosen) < self.mu:
                mid_front = front
                # With this front, we selected enough individuals
                full = True
            else:
                not_chosen += front

        # Hypervolume contribution to get the best candidates on the remaining
        # front
        k = self.mu - len(chosen)
        if k > 0:
            hyperv = self.hyper_volume(mid_front)
            _ = [mid_front[k] for k in numpy.argsort(hyperv)]
            chosen += _[:k]
            not_chosen += _[k:]

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
                logger.info('CMA stopped because of termination criteria: ' +
                            ' '.join(c.name))
                self.active = False
