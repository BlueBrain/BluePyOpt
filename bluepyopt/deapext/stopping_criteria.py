"""StoppingCriteria class"""

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

from math import isclose
from collections import deque

logger = logging.getLogger('__main__')


class StoppingCriteria(object):
    """Stopping Criteria class"""

    def __init__(self):
        """Constructor"""
        self.criteria_met = False
        pass

    def check(self, **kwargs):
        """Check if the stopping criteria is met"""
        pass

    def reset(self):
        self.criteria_met = False


class MaxNGen(StoppingCriteria):
    """Max ngen stopping criteria class"""

    def __init__(self, max_ngen):
        """Constructor"""
        super(MaxNGen, self).__init__()
        self.max_ngen = max_ngen

    def check(self, **kwargs):
        """Check if the maximum number of iteration is reached"""
        ngen = kwargs.get("ngen")

        if ngen > self.max_ngen:
            self.criteria_met = True


class Stagnation(StoppingCriteria):
    """Stagnation stopping criteria class"""

    def __init__(self, lambda_, problem_size):
        """Constructor"""
        super(Stagnation, self).__init__()

        self.lambda_ = lambda_
        self.problem_size = problem_size
        self.stagnation_iter = None

        self.best = []
        self.median = []

    def check(self, **kwargs):
        """Check if the if the population stopped improving"""
        ngen = kwargs.get("ngen")
        population = kwargs.get("population")
        fitness = sort([ind.fitness.reduce for ind in population])

        self.best.append(fitness[0])
        self.median.append(fitness[int(round(len(fitness) / 2.))])
        self.stagnation_iter = int(numpy.ceil(
            0.2 * ngen + 120 + 30. * self.problem_size / self.lambda_))

        if len(self.best) > self.stagnation_iter and \
                len(self.median) > self.stagnation_iter and \
                numpy.median(self.best[-20:]) >= numpy.median(
            self.best[-self.stagnation_iter:-self.stagnation_iter + 20]) and \
                numpy.median(self.median[-20:]) >= numpy.median(
            self.median[-self.stagnation_iter:-self.stagnation_iter + 20]):
            self.criteria_met = True


class TolHistFun(StoppingCriteria):
    """TolHistFun stopping criteria class"""

    def __init__(self, lambda_, problem_size):
        """Constructor"""
        super(TolHistFun, self).__init__()
        self.tolhistfun = 10 ** -12
        self.mins = deque(
            maxlen=10 + int(numpy.ceil(30. * problem_size / lambda_)))

    def check(self, **kwargs):
        """Check if the range of the best values is smaller than
        the threshold"""
        population = kwargs.get("population")
        self.mins.append(numpy.min([ind.fitness.reduce for ind in population]))

        if len(self.mins) == self.mins.maxlen and max(self.mins) - min(
                self.mins) < self.tolhistfun:
            self.criteria_met = True


class EqualFunVals(StoppingCriteria):
    """EqualFunVals stopping criteria class"""

    def __init__(self, lambda_, problem_size):
        """Constructor"""
        super(EqualFunVals, self).__init__()
        self.problem_size = problem_size
        self.equalvals = float(problem_size) / 3.
        self.equalvals_k = int(numpy.ceil(0.1 + lambda_ / 4.))
        self.equalvalues = []

    def check(self, **kwargs):
        """Check if in 1/3rd of the last problem_size iterations the best and
        k'th best solutions are equal"""
        ngen = kwargs.get("ngen")
        population = kwargs.get("population")

        fitness = sort([ind.fitness.reduce for ind in population])
        if isclose(fitness[0], fitness[-self.equalvals_k], ret_tol=1e-6):
            self.equalvalues.append(1)
        else:
            self.equalvalues.append(0)

        if ngen > self.problem_size and \
                sum(self.equalvalues[-self.problem_size:]) > self.equalvals:
            self.criteria_met = True


class TolX(StoppingCriteria):
    """TolX stopping criteria class"""

    def __init__(self):
        """Constructor"""
        super(TolX, self).__init__()
        self.tolx = 10 ** -12

    def check(self, **kwargs):
        """Check if all components of pc and sqrt(diag(C)) are smaller than
        a threshold"""
        pc = kwargs.get("pc")
        C = kwargs.get("C")

        if all(pc < self.tolx) and all(numpy.sqrt(numpy.diag(C)) < self.tolx):
            self.criteria_met = True


class TolUpSigma(StoppingCriteria):
    """TolUpSigma stopping criteria class"""

    def __init__(self, sigma0):
        """Constructor"""
        super(TolUpSigma, self).__init__()
        self.sigma0 = sigma0
        self.tolupsigma = 10 ** 20

    def check(self, **kwargs):
        """Check if the sigma/sigma0 ratio is bigger than a threshold"""
        sigma = kwargs.get("sigma")
        diagD = kwargs.get("diagD")

        if sigma / self.sigma0 > float(diagD[-1] ** 2) * self.tolupsigma:
            self.criteria_met = True


class ConditionCov(StoppingCriteria):
    """ConditionCov stopping criteria class"""

    def __init__(self):
        """Constructor"""
        super(ConditionCov, self).__init__()
        self.conditioncov = 10 ** 14

    def check(self, **kwargs):
        """Check if the condition number of the covariance matrix is
        too large"""
        cond = kwargs.get("cond")

        if cond > self.conditioncov:
            self.criteria_met = True


class NoEffectAxis(StoppingCriteria):
    """NoEffectAxis stopping criteria class"""

    def __init__(self, problem_size):
        """Constructor"""
        super(NoEffectAxis, self).__init__()
        self.conditioncov = 10 ** 14
        self.problem_size = problem_size

    def check(self, **kwargs):
        """Check if the coordinate axis std is too low"""
        ngen = kwargs.get("ngen")
        centroid = kwargs.get("centroid")
        sigma = kwargs.get("sigma")
        diagD = kwargs.get("diagD")
        B = kwargs.get("B")

        noeffectaxis_index = ngen % self.problem_size

        if all(centroid == centroid + 0.1 * sigma * diagD[-noeffectaxis_index] *
               B[-noeffectaxis_index]):
            self.criteria_met = True


class NoEffectCoor(StoppingCriteria):
    """NoEffectCoor stopping criteria class"""

    def __init__(self):
        """Constructor"""
        super(NoEffectCoor, self).__init__()

    def check(self, **kwargs):
        """Check if main axis std has no effect"""
        centroid = kwargs.get("centroid")
        sigma = kwargs.get("sigma")
        C = kwargs.get("C")

        if any(centroid=centroid + 0.2 * sigma * numpy.diag(C)):
            self.criteria_met = True
