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

from deap import base
from deap import cma

from . import MaxNGen, Stagnation
from .utils import _closest_feasible, _bound

logger = logging.getLogger('__main__')


class CMA_ELITIST(cma.StrategyOnePlusLambda):

    """Elitist single objective covariance matrix adaptation"""

    def __init__(self,
                 centroids,
                 offspring_size,
                 sigma,
                 max_ngen,
                 IndCreator,
                 RandIndCreator,
                 map_function=None):
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
            starter = RandIndCreator()
        else:
            starter = centroids[0]

        cma.StrategyOnePlusLambda.__init__(self, starter, sigma, lambda_ = lambda_)

        self.population = []
        self.problem_size = len(starter)

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
    
    @property
    def parents(self):
        return [self.parent]

    def update(self, population):
        """Update the current covariance matrix strategy from the population"""
        population.sort(key=lambda ind: ind.fitness.reduce_weight, reverse=True)
        lambda_succ = sum(self.parent.fitness.reduce_weight <= ind.fitness.reduce_weight for ind in population)
        p_succ = float(lambda_succ) / self.lambda_
        self.psucc = (1 - self.cp) * self.psucc + self.cp * p_succ
        
        if self.parent.fitness.reduce_weight <= population[0].fitness.reduce_weight:
            x_step = (population[0] - numpy.array(self.parent)) / self.sigma
            self.parent = copy.deepcopy(population[0])
            if self.psucc < self.pthresh:
                self.pc = (1 - self.cc) * self.pc + sqrt(self.cc * (2 - self.cc)) * x_step
                self.C = (1 - self.ccov) * self.C + self.ccov * numpy.outer(self.pc, self.pc)
            else:
                self.pc = (1 - self.cc) * self.pc
                self.C = (1 - self.ccov) * self.C + self.ccov * (numpy.outer(self.pc, self.pc) + self.cc * (2 - self.cc) * self.C)

        self.sigma = self.sigma * exp(1.0 / self.d * (self.psucc - self.ptarg) / (1.0 - self.ptarg))
        self.A = numpy.linalg.cholesky(self.C)

    def get_parents(self, to_space):
        """Returns the population in the original parameter space"""
        pop = copy.deepcopy(self.parents)
        for i, ind in enumerate(pop):
            for j, v in enumerate(ind):
                pop[i][j] = to_space[j](v)
        return pop

    def get_population(self, to_space):
        """Returns the population in the original parameter space"""
        pop = copy.deepcopy(self.population)
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
    
    def set_fitness_parents(self, fitnesses):
        self.parent.fitness.values = fitnesses[0]

    def set_fitness(self, fitnesses):
        for f, ind in zip(fitnesses, self.population):
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
