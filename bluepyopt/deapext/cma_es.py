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

from deap import base
from deap import cma

logger = logging.getLogger('__main__')


def _closest_feasible(individual, lbounds, ubounds):
    """returns the closest individual in the parameter bounds"""
    # TO DO: Fix 1e-9 hack
    for i, (u, l, el) in enumerate(zip(ubounds, lbounds, individual)):
        if el >= u:
            individual[i] = u - 1e-9
        elif el <= l:
            individual[i] = l + 1e-9
    return individual


def _bound(population, lbounds, ubounds, IndCreator):
    """return the population bounded by the lower and upper parameter bounds."""
    n_out = 0
    for i, ind in enumerate(population):
        if numpy.any(numpy.less(ind, lbounds)) or numpy.any(
                numpy.greater(ind, ubounds)):
            new_ind = _closest_feasible(ind, lbounds, ubounds)
            population[i] = IndCreator(new_ind)
            n_out += 1
    return n_out


class cma_es(cma.Strategy):

    def __init__(self,
                 centroid,
                 sigma,
                 lr_scale,
                 max_ngen,
                 IndCreator):
        """Constructor

        Args:
            centroid (list): initial guess used as the starting point of
            the CMA-ES
            sigma (float): initial standard deviation of the distribution
            lr_scale (float): scaling for the learning rates
            max_ngen (int): total number of generation to run
            IndCreator (fcn): individual creating function
        """

        cma.Strategy.__init__(self, centroid, sigma)

        self.fitness_reduce = fitness_reduce

        # Rescale the learning rates
        self.cs *= lr_scale
        self.cc *= lr_scale
        self.ccov1 *= lr_scale
        self.ccovmu *= lr_scale

        self.population = []
        self.IndCreator = IndCreator

        self.problem_size = len(centroid)

        # Toolbox specific to this CMA-ES
        self.toolbox = base.Toolbox()
        self.toolbox.register("generate", self.generate, self.IndCreator)
        self.toolbox.register("update", self.update)

        # Set termination conditions
        self.active = True
        if max_ngen <= 0:
            max_ngen = 100 + 50 * (self.problem_size + 3) ** 2 / numpy.sqrt(
                self.lambda_)

        self.stopping_conditions = [
            MaxNGen(max_ngen),
            Stagnation(self.lambda_, self.problem_size),
            TolHistFun(self.lambda_, self.problem_size),
            EqualFunVals(self.lambda_, self.problem_size),
            NoEffectAxis(self.problem_size),
            TolUpSigma(float(self.sigma)),
            TolX(),
            ConditionCov(),
            NoEffectCoor()
        ]

    def get_population(self, to_space):
        # Returns the population in the original parameter space
        pop = []
        for ind in self.population:
            pop.append(self.IndCreator([f(e) for f, e in zip(to_space, ind)]))
            pop[-1].fitness = ind.fitness
            pop[-1].all_values = ind.all_values
        return pop

    def generate_new_pop(self, lbounds, ubounds):
        # Generate a new population bounded in the normalized space
        self.population = self.toolbox.generate()
        return _bound(self.population, lbounds, ubounds, self.IndCreator)

    def update_strategy(self):
        self.toolbox.update(self.population)

    def set_fitness(self, fitnesses):
        for f, ind in zip(fitnesses, self.population):
            ind.fitness.values = [self.fitness_reduce(f)]
            ind.all_values = f

    def check_termination(self, ngen):
        stopping_params = {
            "ngen": ngen,
            "population": self.population,
            "centroid": self.centroid,
            "pc": self.pc,
            "C": self.C,
            "B": self.B,
            "sigma": self.sigma,
            "diagD": self.diagD,
            "cond": self.cond,
        }

        [c.check(stopping_params) for c in self.stopping_conditions]
        for c in self.stopping_conditions:
            if c.criteria_met:
                logger.info('CMA stopped because of termination criteria: ' +
                            ' '.join(type(c).__name__))
                self.active = False
