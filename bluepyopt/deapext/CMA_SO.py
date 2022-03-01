"""Single Objective CMA-es class"""

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
from math import sqrt, log
import copy

from deap import base
from deap import cma

from .stoppingCriteria import (
    MaxNGen,
    Stagnation,
    TolHistFun,
    EqualFunVals,
    NoEffectAxis,
    TolUpSigma,
    TolX,
    ConditionCov,
    NoEffectCoor,
)

from . import utils

logger = logging.getLogger("__main__")


class CMA_SO(cma.Strategy):
    """Single objective covariance matrix adaption"""

    def __init__(
        self,
        centroids,
        offspring_size,
        sigma,
        max_ngen,
        IndCreator,
        RandIndCreator,
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
             map_function (map): function used to map (parallelize) the
                 evaluation function calls
             use_scoop (bool): use scoop map for parallel computation
        """

        if offspring_size is None:
            lambda_ = int(4 + 3 * log(len(RandIndCreator())))
        else:
            lambda_ = offspring_size

        if centroids is None:
            starter = RandIndCreator()
        else:
            starter = centroids[0]

        cma.Strategy.__init__(self, starter, sigma, lambda_=lambda_)

        self.population = []
        self.problem_size = len(starter)

        self.map_function = map_function
        self.use_scoop = use_scoop

        # Toolbox specific to this CMA-ES
        self.toolbox = base.Toolbox()
        self.toolbox.register("generate", self.generate, IndCreator)
        self.toolbox.register("update", self.update)

        # Set termination conditions
        self.active = True
        if max_ngen <= 0:
            max_ngen = 100 + 50 * (self.problem_size + 3) ** 2 / numpy.sqrt(
                self.lambda_
            )

        self.stopping_conditions = [
            MaxNGen(max_ngen),
            Stagnation(self.lambda_, self.problem_size),
            TolHistFun(self.lambda_, self.problem_size),
            EqualFunVals(self.lambda_, self.problem_size),
            NoEffectAxis(self.problem_size),
            TolUpSigma(float(self.sigma)),
            TolX(),
            ConditionCov(),
            NoEffectCoor(),
        ]

    def update(self, population):
        """Update the current covariance matrix strategy from the
        population"""

        population.sort(key=lambda ind: ind.fitness.weighted_reduce,
                        reverse=True)

        old_centroid = self.centroid
        self.centroid = numpy.dot(self.weights, population[0:self.mu])

        c_diff = self.centroid - old_centroid

        # Cumulation : update evolution path
        self.ps = (1 - self.cs) * self.ps + sqrt(
            self.cs * (2 - self.cs) * self.mueff
        ) / self.sigma * numpy.dot(
            self.B, (1.0 / self.diagD) * numpy.dot(self.B.T, c_diff)
        )  # noqa

        hsig = float(
            (
                numpy.linalg.norm(self.ps)
                / sqrt(1.0 - (1.0 - self.cs) **
                (2.0 * (self.update_count + 1.0)))
                / self.chiN
                < (1.4 + 2.0 / (self.dim + 1.0))
            )
        )  # noqa

        self.update_count += 1

        self.pc = (1 - self.cc) * self.pc + hsig * sqrt(
            self.cc * (2 - self.cc) * self.mueff
        ) / self.sigma * c_diff

        # Update covariance matrix
        artmp = population[0:self.mu] - old_centroid
        self.C = (
            (
                1
                - self.ccov1
                - self.ccovmu
                + (1 - hsig) * self.ccov1 * self.cc * (2 - self.cc)
            )
            * self.C
            + self.ccov1 * numpy.outer(self.pc, self.pc)
            + self.ccovmu * numpy.dot((self.weights * artmp.T), artmp)
            / self.sigma ** 2
        )

        self.sigma *= numpy.exp(
            (numpy.linalg.norm(self.ps) / self.chiN - 1.0) * self.cs
            / self.damps
        )

        self.diagD, self.B = numpy.linalg.eigh(self.C)
        indx = numpy.argsort(self.diagD)

        self.cond = self.diagD[indx[-1]] / self.diagD[indx[0]]

        self.diagD = self.diagD[indx] ** 0.5
        self.B = self.B[:, indx]
        self.BD = self.B * self.diagD

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
        return utils.bound(self.population, lbounds, ubounds)

    def update_strategy(self):
        self.toolbox.update(self.population)

    def set_fitness(self, fitnesses):
        for f, ind in zip(fitnesses, self.population):
            ind.fitness.values = f

    def check_termination(self, gen):
        stopping_params = {
            "gen": gen,
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
                logger.info(
                    "CMA stopped because of termination criteria: " +
                    " ".join(c.name)
                )
                self.active = False
