"""Utils function"""

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
import random

import deap.base

# pylint: disable=R0914, R0912


class WeightedReducedFitness(deap.base.Fitness):

    """Fitness that compares by weighted objective values"""

    def __init__(self, values=(), obj_size=None, reduce_fcn=numpy.sum):
        self.weights = [-1.0] * obj_size if obj_size is not None else [-1]
        self.reduce_fcn = reduce_fcn

        super(WeightedReducedFitness, self).__init__(values)

    @property
    def reduce(self):
        """Reduce of values"""
        return self.reduce_fcn(self.values)

    @property
    def weighted_reduce(self):
        """Reduce of weighted values"""
        return self.reduce_fcn(self.wvalues)

    def __le__(self, other):
        return self.weighted_reduce <= other.weighted_reduce

    def __lt__(self, other):
        return self.weighted_reduce < other.weighted_reduce

    def __deepcopy__(self, _):
        """Override deepcopy"""

        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result


class WSListIndividual(list):

    """Individual consisting of a list with weighted fitness"""

    def __init__(self, *args, **kwargs):
        """Constructor"""

        reduce_fcn = kwargs.get("reduce_fcn", numpy.sum)
        self.fitness = WeightedReducedFitness(
            obj_size=kwargs["obj_size"], reduce_fcn=reduce_fcn
        )

        # Index of the parent, used by MO-CMA
        self._ps = "p", 0

        del kwargs["obj_size"]
        if "reduce_fcn" in kwargs:
            del kwargs["reduce_fcn"]
        super(WSListIndividual, self).__init__(*args, **kwargs)


def update_history_and_hof(halloffame, history, population):
    """Update the hall of fame with the generated individuals
    Note: History and Hall-of-Fame behave like dictionaries
    """
    if halloffame is not None:
        halloffame.update(population)

    history.update(population)


def record_stats(stats, logbook, gen, population, invalid_count):
    """Update the statistics with the new population"""
    record = stats.compile(population) if stats is not None else {}
    logbook.record(gen=gen, nevals=invalid_count, **record)


def closest_feasible(individual, lbounds, ubounds):
    """Returns the closest individual in the parameter bounds"""
    # TODO: Fix 1e-9 hack
    for i, (u, l, el) in enumerate(zip(ubounds, lbounds, individual)):
        if el >= u:
            individual[i] = u - 1e-9
        elif el <= l:
            individual[i] = l + 1e-9
    return individual


def bound(population, lbounds, ubounds):
    """Bounds the population based on lower and upper parameter bounds."""
    n_out = 0
    for i, ind in enumerate(population):
        if numpy.any(numpy.less(ind, lbounds)) or numpy.any(
            numpy.greater(ind, ubounds)
        ):
            population[i] = closest_feasible(ind, lbounds, ubounds)
            n_out += 1
    return n_out


def uniform(lower_list, upper_list, dimensions):
    """Uniformly pick an individual"""
    if hasattr(lower_list, "__iter__"):
        return [
            random.uniform(lower, upper) for lower, upper in
            zip(lower_list, upper_list)
        ]
    else:
        return [random.uniform(lower_list, upper_list) for _ in
                range(dimensions)]


def reduce_method(meth):
    """Overwrite reduce"""
    return (getattr, (meth.__self__, meth.__func__.__name__))


def run_next_gen(criteria, terminator):
    """Condition to stay inside the loop."""
    if terminator is None:
        return criteria
    return criteria and not terminator.is_set()
