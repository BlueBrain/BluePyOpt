"""IBEA selector"""

from __future__ import division

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

The code in this file was original written in 2015 at the
BlueBrain Project, EPFL, Lausanne
The authors were Werner Van Geit, Michael Gevaert and Jean-Denis Courcol
It is based on a C implementation of the IBEA algorithm in the PISA
optimization framework developed at the ETH, Zurich
http://www.tik.ee.ethz.ch/pisa/selectors/ibea/?page=ibea.php
"""


import numpy as numpy
import itertools
import random


def selIBEA(population, mu, alpha=None, kappa=.05, tournament_n=4):
    """IBEA Selector"""

    if alpha is None:
        alpha = len(population)

    # Put all the objectives of all individuals in a matrix
    # DEAP selector are supposed to maximise the objective values
    # We take the negative objectives because this algorithm will minimise
    population_matrix = [
        [-x for x in individual.fitness.wvalues] for individual in population]

    # Calculate minimal square bounding box of the objectives
    min_box_bounds, max_box_bounds = _calc_box_bounds(population_matrix)

    # Calculate a matrix with the fitness components of every individual
    components = _calc_fitness_components(
        population_matrix,
        min_box_bounds,
        max_box_bounds,
        kappa=kappa)

    # Calculate the fitness values
    _calc_fitnesses(population, components)

    # Do the environmental selection
    population[:] = _environmental_selection(population, alpha)

    # Select the parents in a tournament
    parents = _mating_selection(population, mu, tournament_n)

    return parents


def _calc_box_bounds(population_matrix):
    """Calculate the minimal square bounding box of the objectives"""

    # Calculate the min/max over the columns
    min_bounds = list(numpy.min(population_matrix, axis=0))
    max_bounds = list(numpy.max(population_matrix, axis=0))

    # Return, parse to a list (indicators need lists, not numpy arrays)
    return list(min_bounds), list(max_bounds)


def _calc_fitness_components(
        population_matrix,
        min_box_bounds,
        max_box_bounds,
        kappa=None):
    """returns an N * N numpy array of doubles, which is their IBEA fitness """

    # Population size is the number of rows in the population_matrix
    pop_size = len(population_matrix)

    components_matrix = numpy.zeros((pop_size, pop_size))

    # pylint: disable=F0401, E0611
    import eps
    # pylint: enable=F0401, E0611

    # Calculator the indicator value for every element in the matrix
    # The code inside this for loop is (has to be) heavily optimised for speed
    for i in xrange(0, pop_size):
        ind1 = population_matrix[i]
        for j in itertools.chain(xrange(0, i), xrange(i + 1, pop_size)):
            ind2 = population_matrix[j]
            components_matrix[i, j] = eps.indicator(ind1,
                                                    ind2,
                                                    min_box_bounds,
                                                    max_box_bounds)

    # Calculate max of absolute value of all elements in matrix
    max_absolute_indicator = numpy.max(abs(components_matrix))

    # Normalisation
    components_matrix = \
        numpy.exp(numpy.multiply(components_matrix,
                                 -1.0 / (kappa * max_absolute_indicator)))

    return components_matrix


def _calc_fitnesses(population, components):
    """Calculate the IBEA fitness of every individual"""

    # Calculate sum of every column in the matrix, ignore diagonal elements
    column_sums = numpy.sum(components, axis=0) - numpy.diagonal(components)

    # Fill the 'ibea_fitness' field on the individuals with the fitness value
    for individual, ibea_fitness in zip(population, column_sums):
        individual.ibea_fitness = ibea_fitness


def _mating_selection(population, mu, tournament_n):
    """Returns the n_of_parents individuals with the best fitness"""

    parents = []
    for _ in xrange(mu):
        # Pick individuals for tournament
        tournament = [random.choice(population) for _ in range(tournament_n)]
        # Sort according to fitness
        tournament.sort(key=lambda ind: ind.ibea_fitness)
        # Winner is element with smallest fitness
        parents.append(tournament[0])

    return parents


def _environmental_selection(population, selection_size):
    """Returns the selection_size individuals with the best fitness"""

    # Sort the individuals based on their fitness
    population.sort(key=lambda ind: ind.ibea_fitness)

    # Return the first 'selection_size' elements
    return population[:selection_size]

__all__ = ['selIBEA']
