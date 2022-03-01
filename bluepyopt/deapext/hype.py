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
import numpy


def hypesub(la, A, actDim, bounds, pvec, alpha, k):
    """HypE algorithm sub function"""

    h = numpy.zeros(la)
    i = numpy.argsort(A[:, actDim - 1])
    S = A[i]
    pvec = pvec[i]

    for i in range(1, S.shape[0] + 1):

        if i < S.shape[0]:
            extrusion = S[i, actDim - 1] - S[i - 1, actDim - 1]
        else:
            extrusion = bounds[actDim - 1] - S[i - 1, actDim - 1]

        if actDim == 1:
            if i > k:
                break
            if alpha[i - 1] >= 0:
                h[pvec[0:i]] += extrusion * alpha[i - 1]
        elif extrusion > 0.0:
            h += extrusion * hypesub(
                la, S[0:i, :], actDim - 1, bounds, pvec[0:i], alpha, k
            )

    return h


def hypeIndicatorExact(points, bounds, k):
    """HypE algorithm. Python implementation of the Matlab code available at
    https://sop.tik.ee.ethz.ch/download/supplementary/hype/

    Args:
        points(array): 2D array containing the objective values of the
        population
        bounds(array): 1D array containing the reference point from which to
        compute the hyper-volume
        k(int): HypE parameter
    """

    Ps = points.shape[0]
    if k < 0:
        k = Ps
    actDim = points.shape[1]
    pvec = numpy.arange(points.shape[0])

    alpha = []
    for i in range(1, k + 1):
        j = numpy.arange(1, i)
        alpha.append(numpy.prod((k - j) / (Ps - j) / i))
    alpha = numpy.asarray(alpha)

    return hypesub(points.shape[0], points, actDim, bounds, pvec, alpha, k)


def hypeIndicatorSampled(points, bounds, k, nrOfSamples):
    """Monte-Carlo approximation of the HypE algorithm. Python implementation
    of the Matlab code available at
    https://sop.tik.ee.ethz.ch/download/supplementary/hype/

    Args:
        points(array): 2D array containing the objective values of the
        population
        bounds(array): 1D array containing the reference point from which to
        compute the hyper-volume
        k(int): HypE parameter
        nrOfSamples(int): number of random samples to use for the
        Monte-Carlo approximation
    """

    nrP = points.shape[0]
    dim = points.shape[1]
    F = numpy.zeros(nrP)

    BoxL = numpy.min(points, axis=0)

    alpha = []
    for i in range(1, k + 1):
        j = numpy.arange(1, i)
        alpha.append(numpy.prod((k - j) / (nrP - j) / i))
    alpha = numpy.asarray(alpha + [0.0] * nrP)

    S = numpy.random.uniform(low=BoxL, high=bounds, size=(nrOfSamples, dim))

    dominated = numpy.zeros(nrOfSamples, dtype="uint")
    for j in range(1, nrP + 1):
        B = S - points[j - 1]
        ind = numpy.sum(B >= 0, axis=1) == dim
        dominated[ind] += 1

    for j in range(1, nrP + 1):
        B = S - points[j - 1]
        ind = numpy.sum(B >= 0, axis=1) == dim
        x = dominated[ind]
        F[j - 1] = numpy.sum(alpha[x - 1])

    F = F * numpy.prod(bounds - BoxL) / nrOfSamples

    return F
