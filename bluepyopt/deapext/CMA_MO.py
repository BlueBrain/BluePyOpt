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
import copy
from math import sqrt, log, exp

import deap
from deap import base
from deap import cma

from . import MaxNGen, Stagnation
from .utils import _closest_feasible, _bound
from . import tools

logger = logging.getLogger('__main__')


class CMA_MO(cma.StrategyMultiObjective):

    """Multiple objective covariance matrix adaption"""

    def __init__(self,
                 centroids,
                 offspring_size,
                 sigma,
                 max_ngen,
                 IndCreator,
                 RandIndCreator):
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

        cma.StrategyMultiObjective.__init__(self, starters, sigma, mu=int(lambda_/2.), 
                                            lambda_=lambda_, indicator=deap.tools.additive_epsilon)
        
        self.population = []
        self.problem_size = len(starters[0])

        # Toolbox specific to this CMA-ES
        self.toolbox = base.Toolbox()
        self.toolbox.register("generate", self.generate, IndCreator)
        self.toolbox.register("update", self.update)

        # Set termination conditions
        self.active = True
        if max_ngen <= 0:
            max_ngen = 100 + 50 * (self.problem_size + 3) ** 2 / numpy.sqrt(
                self.lambda_)

        self.stopping_conditions = [
            MaxNGen(max_ngen),
            Stagnation(self.lambda_, self.problem_size),
        ]

    def _select(self, candidates):
        if len(candidates) <= self.mu:
            return candidates, []

        pareto_fronts = deap.tools.sortLogNondominated(candidates, len(candidates))

        chosen = list()
        mid_front = None
        not_chosen = list()

        # Fill the next population (chosen) with the fronts until there is not enouch space
        # When an entire front does not fit in the space left we rely on the hypervolume
        # for this front
        # The remaining fronts are explicitely not chosen
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

        # Separate the mid front to accept only k individuals
        k = self.mu - len(chosen)
        if k > 0:
            fit = [numpy.mean(ind.fitness.values) for ind in mid_front]
            for g in range(k):
                chosen.append(mid_front.pop(numpy.argmin(fit)))
            not_chosen += mid_front
            
            #_ = tools.selIBEA(mid_front, k)
            #chosen += [mid_front[g] for g in _]
            #not_chosen += [ind for g,ind in enumerate(mid_front) if g not in _]
            
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
        return _bound(self.population, lbounds, ubounds)

    def update_strategy(self):
        self.toolbox.update(self.population)

    def set_fitness(self, fitnesses):
        for f, ind in zip(fitnesses, self.population):
            ind.fitness.values = f

    def set_fitness_parents(self, fitnesses):
        for f, ind in zip(fitnesses, self.parents):
            ind.fitness.values = f

    def check_termination(self, ngen):
        stopping_params = {
            "ngen": ngen,
            "population": self.population,
        }

        [c.check(stopping_params) for c in self.stopping_conditions]
        for c in self.stopping_conditions:
            if c.criteria_met:
                logger.info('CMA stopped because of termination criteria: ' +
                            ' '.join(type(c).__name__))
                self.active = False
