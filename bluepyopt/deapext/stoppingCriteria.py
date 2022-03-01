"""StoppingCriteria class"""

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

from collections import deque

import bluepyopt.stoppingCriteria

logger = logging.getLogger("__main__")


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


class MaxNGen(bluepyopt.stoppingCriteria.StoppingCriteria):
    """Max ngen stopping criteria class"""

    name = "Max ngen"

    def __init__(self, max_ngen):
        """Constructor"""
        super(MaxNGen, self).__init__()
        self.max_ngen = max_ngen

    def check(self, kwargs):
        """Check if the maximum number of iteration is reached"""
        gen = kwargs.get("gen")
        if gen > self.max_ngen:
            self.criteria_met = True


class Stagnation(bluepyopt.stoppingCriteria.StoppingCriteria):
    """Stagnation stopping criteria class"""

    name = "Stagnation"

    def __init__(self, lambda_, problem_size):
        """Constructor"""
        super(Stagnation, self).__init__()

        self.lambda_ = lambda_
        self.problem_size = problem_size
        self.stagnation_iter = None

        self.best = []
        self.median = []

    def check(self, kwargs):
        """Check if the population stopped improving"""
        ngen = kwargs.get("gen")
        population = kwargs.get("population")
        fitness = [ind.fitness.reduce for ind in population]
        fitness.sort()

        self.best.append(fitness[0])
        self.median.append(fitness[int(round(len(fitness) / 2.0))])
        self.stagnation_iter = int(
            numpy.ceil(
                0.2 * ngen + 120 + 30.0 * self.problem_size / self.lambda_
            )
        )

        cbest = len(self.best) > self.stagnation_iter
        cmed = len(self.median) > self.stagnation_iter
        cbest2 = numpy.median(self.best[-20:]) >= numpy.median(
            self.best[-self.stagnation_iter:-self.stagnation_iter + 20]
        )
        cmed2 = numpy.median(self.median[-20:]) >= numpy.median(
            self.median[-self.stagnation_iter:-self.stagnation_iter + 20]
        )
        if cbest and cmed and cbest2 and cmed2:
            self.criteria_met = True


class TolHistFun(bluepyopt.stoppingCriteria.StoppingCriteria):
    """TolHistFun stopping criteria class"""

    name = "TolHistFun"

    def __init__(self, lambda_, problem_size):
        """Constructor"""
        super(TolHistFun, self).__init__()
        self.tolhistfun = 10 ** -12
        self.mins = deque(
            maxlen=10 + int(numpy.ceil(30.0 * problem_size / lambda_))
        )

    def check(self, kwargs):
        """Check if the range of the best values is smaller than
        the threshold"""
        population = kwargs.get("population")
        self.mins.append(numpy.min([ind.fitness.reduce for ind in population]))

        if (
            len(self.mins) == self.mins.maxlen
            and max(self.mins) - min(self.mins) < self.tolhistfun
        ):
            self.criteria_met = True


class EqualFunVals(bluepyopt.stoppingCriteria.StoppingCriteria):
    """EqualFunVals stopping criteria class"""

    name = "EqualFunVals"

    def __init__(self, lambda_, problem_size):
        """Constructor"""
        super(EqualFunVals, self).__init__()
        self.problem_size = problem_size
        self.equalvals = float(problem_size) / 3.0
        self.equalvals_k = int(numpy.ceil(0.1 + lambda_ / 4.0))
        self.equalvalues = []

    def check(self, kwargs):
        """Check if in 1/3rd of the last problem_size iterations the best and
        k'th best solutions are equal"""
        ngen = kwargs.get("gen")
        population = kwargs.get("population")

        fitness = [ind.fitness.reduce for ind in population]
        fitness.sort()

        if isclose(fitness[0], fitness[-self.equalvals_k], rel_tol=1e-6):
            self.equalvalues.append(1)
        else:
            self.equalvalues.append(0)

        if (
            ngen > self.problem_size
            and sum(self.equalvalues[-self.problem_size:]) > self.equalvals
        ):
            self.criteria_met = True


class TolX(bluepyopt.stoppingCriteria.StoppingCriteria):
    """TolX stopping criteria class"""

    name = "TolX"

    def __init__(self):
        """Constructor"""
        super(TolX, self).__init__()
        self.tolx = 10 ** -12

    def check(self, kwargs):
        """Check if all components of pc and sqrt(diag(C)) are smaller than
        a threshold"""
        pc = kwargs.get("pc")
        C = kwargs.get("C")

        if all(pc < self.tolx) and all(numpy.sqrt(numpy.diag(C)) < self.tolx):
            self.criteria_met = True


class TolUpSigma(bluepyopt.stoppingCriteria.StoppingCriteria):
    """TolUpSigma stopping criteria class"""

    name = "TolUpSigma"

    def __init__(self, sigma0):
        """Constructor"""
        super(TolUpSigma, self).__init__()
        self.sigma0 = sigma0
        self.tolupsigma = 10 ** 20

    def check(self, kwargs):
        """Check if the sigma/sigma0 ratio is bigger than a threshold"""
        sigma = kwargs.get("sigma")
        diagD = kwargs.get("diagD")

        if sigma / self.sigma0 > float(diagD[-1] ** 2) * self.tolupsigma:
            self.criteria_met = True


class ConditionCov(bluepyopt.stoppingCriteria.StoppingCriteria):
    """ConditionCov stopping criteria class"""

    name = "ConditionCov"

    def __init__(self):
        """Constructor"""
        super(ConditionCov, self).__init__()
        self.conditioncov = 10 ** 14

    def check(self, kwargs):
        """Check if the condition number of the covariance matrix is
        too large"""
        cond = kwargs.get("cond")

        if cond > self.conditioncov:
            self.criteria_met = True


class NoEffectAxis(bluepyopt.stoppingCriteria.StoppingCriteria):
    """NoEffectAxis stopping criteria class"""

    name = "NoEffectAxis"

    def __init__(self, problem_size):
        """Constructor"""
        super(NoEffectAxis, self).__init__()
        self.conditioncov = 10 ** 14
        self.problem_size = problem_size

    def check(self, kwargs):
        """Check if the coordinate axis std is too low"""
        ngen = kwargs.get("gen")
        centroid = kwargs.get("centroid")
        sigma = kwargs.get("sigma")
        diagD = kwargs.get("diagD")
        B = kwargs.get("B")

        noeffectaxis_index = ngen % self.problem_size

        if all(
            centroid
            == centroid
            + 0.1 * sigma * diagD[-noeffectaxis_index] * B[-noeffectaxis_index]
        ):
            self.criteria_met = True


class NoEffectCoor(bluepyopt.stoppingCriteria.StoppingCriteria):
    """NoEffectCoor stopping criteria class"""

    name = "NoEffectCoor"

    def __init__(self):
        """Constructor"""
        super(NoEffectCoor, self).__init__()

    def check(self, kwargs):
        """Check if main axis std has no effect"""
        centroid = kwargs.get("centroid")
        sigma = kwargs.get("sigma")
        C = kwargs.get("C")

        if any(centroid == centroid + 0.2 * sigma * numpy.diag(C)):
            self.criteria_met = True
