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

from collections import deque

from deap import base
from deap import cma

logger = logging.getLogger('__main__')

def _closest_feasible(individual, lbounds, ubounds):
    """returns the closest individual in the parameter bounds"""
    # TO DO: Fix 1e-9 hack
    for i,(u,l,el) in enumerate(zip(ubounds, lbounds, individual)):
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
                 IndCreator,
                 fitness_reduce=numpy.sum,
                 cma_params={}):
        """Constructor

        Args:
            centroid (list): initial guess used as the starting point of
            the CMA-ES
            sigma (float): initial standard deviation of the distribution
            lr_scale (float): scaling for the learning rates
            max_ngen (int): total number of generation to run
            IndCreator (fcn): individual creating function
            fitness_reduce (fcn): used to reduce the list of objective values
            to a single fitness value
            cma_params (dict): kwargs passed to the cma.Strategy constructor
            (see https://deap.readthedocs.io/en/master/api/algo.html#deap.cma.Strategy)
        """
        
        cma.Strategy.__init__(self, centroid, sigma, **cma_params)

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
        self.conditions = {"MaxIter": False,
                           "TolHistFun": False,
                           "EqualFunVals": False,
                           "TolX": False,
                           "TolUpSigma": False,
                           "Stagnation": False,
                           "ConditionCov": False,
                           "NoEffectAxis": False,
                           "NoEffectCoor": False}
        self.equalfunvalues = list()
        self.bestvalues = list()
        self.medianvalues = list()
        self.mins = deque(maxlen= 10 + int(numpy.ceil(30. *
                                     self.problem_size / self.lambda_)))
        self.SIGMA0 = sigma
        self.TOLHISTFUN = 10 ** -12
        self.EQUALFUNVALS = 1. / 3.
        self.TOLX = 10 ** -12
        self.TOLUPSIGMA = 10 ** 20
        self.CONDITIONCOV = 10 ** 14
        self.EQUALFUNVALS_K = int(numpy.ceil(0.1 + self.lambda_ / 4.))
        self.MAXITER = max_ngen if max_ngen > 0 else 100 + 50 * \
                        (self.problem_size + 3) ** 2 / numpy.sqrt(self.lambda_)
        self.NOEFFECTAXIS_INDEX = None
        self.STAGNATION_ITER = None

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

    def check_termination(self, t):
        # Update time-dependant termination conditions
        self.STAGNATION_ITER = int(
            numpy.ceil(0.2 * t + 120 + 30. * self.problem_size / self.lambda_))
        self.NOEFFECTAXIS_INDEX = t % self.problem_size

        # Count the number of times the k'th best solution is equal to
        # the best solution. At this point the population is sorted
        # (method update)
        if self.population[-1].fitness == self.population[
                -self.EQUALFUNVALS_K].fitness:
            self.equalfunvalues.append(1)

        # Log the best and median value of this population
        self.bestvalues.append(self.population[-1].fitness.values)
        self.medianvalues.append(self.population[int(
            round(len(self.population) / 2.))].fitness.values)

        # The maximum number of iteration per CMA-ES is reached
        if t >= self.MAXITER:
            self.conditions["MaxIter"] = True

        # The range of the best values is smaller than the threshold
        self.mins.append(
            numpy.min([ind.fitness.values[0] for ind in self.population]))
        if (len(self.mins) == self.mins.maxlen) and max(self.mins) - min(
                self.mins) < self.TOLHISTFUN:
            self.conditions["TolHistFun"] = True

        # If in 1/3rd of the last problem_size iterations the best and
        # k'th best solutions are equal
        if t > self.problem_size and sum(self.equalfunvalues[
                -self.problem_size:]) / float(self.problem_size) > \
                self.EQUALFUNVALS:
            self.conditions["EqualFunVals"] = True

        # All components of pc and sqrt(diag(C)) are smaller than
        # the threshold
        if all(self.pc < self.TOLX) and all(
                numpy.sqrt(numpy.diag(self.C)) < self.TOLX):
            self.conditions["TolX"] = True

        # The sigma ratio is bigger than a threshold
        if self.sigma / self.SIGMA0 > float(
                self.diagD[-1] ** 2) * self.TOLUPSIGMA:
            self.conditions["TolUpSigma"] = True

        # Stagnation
        if len(self.bestvalues) > self.STAGNATION_ITER and len(
                self.medianvalues) > self.STAGNATION_ITER and \
                numpy.median(self.bestvalues[-20:]) >= numpy.median(
            self.bestvalues[
            -self.STAGNATION_ITER:-self.STAGNATION_ITER + 20]) and \
                numpy.median(self.medianvalues[-20:]) >= numpy.median(
            self.medianvalues[
            -self.STAGNATION_ITER:-self.STAGNATION_ITER + 20]):
            self.conditions["Stagnation"] = True

        # The condition number of the covariance matrix is too large
        if self.cond > self.CONDITIONCOV:
            self.conditions["ConditionCov"] = True

        # The coordinate axis std is too low
        if all(self.centroid == self.centroid + 0.1 * self.sigma * self.diagD[
                -self.NOEFFECTAXIS_INDEX] * self.B[-self.NOEFFECTAXIS_INDEX]):
            self.conditions["NoEffectAxis"] = True

        # The main axis std has no effect
        if any(self.centroid == self.centroid + 0.2 *
               self.sigma * numpy.diag(self.C)):
            self.conditions["NoEffectCoor"] = True

        stop_causes = [k for k, v in self.conditions.items() if v]
        if len(stop_causes):
            logger.info('CMA stopped because of termination criteria: ' +
                        ' '.join(stop_causes))
            self.active = False
