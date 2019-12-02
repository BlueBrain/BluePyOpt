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

import random
import logging
import functools
import copyreg
import types
import numpy

import deap
import deap.base
import deap.tools

import bluepyopt.optimisations

logger = logging.getLogger('__main__')


# TODO decide which variables go in constructor,which ones go in 'run' function
# TODO abstract the algorithm by creating a class for every algorithm, that way
# settings of the algorithm can be stored in objects of these classes


def _reduce_method(meth):
    """Overwrite reduce"""
    return (getattr, (meth.__self__, meth.__func__.__name__))


def _uniform(lower_list, upper_list, dimensions):
    """Fill array that will uniformly pick an individual """

    if hasattr(lower_list, '__iter__'):
        return [random.uniform(lower, upper) for lower, upper in
                zip(lower_list, upper_list)]
    else:
        return [random.uniform(lower_list, upper_list)
                for _ in range(dimensions)]


class ReduceFitness(deap.base.Fitness):
    """Fitness that compares by weighted"""

    def __init__(self, values=(), obj_size=None, reduce_fcn=numpy.sum):
        self.weights = [-1.0] * obj_size if obj_size is not None else [-1]
        self.reduce_fcn = reduce_fcn
        super(ReduceFitness, self).__init__(values)

    @property
    def reduce(self):
        return self.reduce_fcn(self.values)

    @property
    def reduce_weight(self):
        """Weighted reduce of wvalues"""
        return self.reduce_fcn(self.wvalues)

    def __le__(self, other):
        return self.reduce_weight <= other.reduce_weight

    def __lt__(self, other):
        return self.reduce_weight < other.reduce_weight

    def __deepcopy__(self, _):
        """Override deepcopy"""

        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result


class ListIndividual(list):
    """Individual consisting of list with weighted fitness field"""

    def __init__(self, *args, **kwargs):
        """Constructor"""
        self.fitness = ReduceFitness(obj_size=kwargs['obj_size'],
                                     reduce_fcn=kwargs['reduce_fcn'])
        del kwargs['obj_size']
        del kwargs['reduce_fcn']
        super(ListIndividual, self).__init__(*args, **kwargs)


class DEAPOptimisation(bluepyopt.optimisations.Optimisation):
    """DEAP Optimisation class"""

    def __init__(self,
                 evaluator=None,
                 use_scoop=False,
                 seed=1,
                 map_function=None,
                 hof=None,
                 fitness_reduce=numpy.sum):
        """Constructor

        Args:
            evaluator (Evaluator): Evaluator object
            seed (float): Random number generator seed
            map_function (function): Function used to map (parallelise) the
                evaluation function calls
            hof (hof): Hall of Fame object
            fitness_reduce (fcn): function used to reduce the objective values
                to a single fitness score
        """

        super(DEAPOptimisation, self).__init__(evaluator=evaluator)

        self.use_scoop = use_scoop
        self.seed = seed
        self.map_function = map_function
        self.fitness_reduce = fitness_reduce

        self.hof = hof
        if self.hof is None:
            self.hof = deap.tools.HallOfFame(10)

        # Number of objective values
        self.problem_size = len(self.evaluator.params)

        # Number of parameters
        self.ind_size = len(self.evaluator.objectives)

        # Create a DEAP toolbox
        self.toolbox = deap.base.Toolbox()

        # Bounds for the parameters
        self.lbounds = numpy.asarray(
            [p.lower_bound for p in self.evaluator.params])
        self.ubounds = numpy.asarray(
            [p.upper_bound for p in self.evaluator.params])

        self.setup_deap()

    def setup_deap(self):
        """Set up optimisation"""

        # Set random seed
        random.seed(self.seed)
        numpy.random.seed(self.seed)

        # Register the 'uniform' function
        self.toolbox.register("uniformparams", _uniform, self.lbounds,
                              self.ubounds,
                              self.ind_size)

        # Register the individual format
        self.toolbox.register(
            "Individual",
            functools.partial(ListIndividual,
                              obj_size=self.ind_size,
                              reduce_fcn=self.fitness_reduce)
        )

        # A Random Indiviual is create by ListIndividual and parameters are
        # initially picked by 'uniform'
        self.toolbox.register(
            "RandomIndividual",
            deap.tools.initIterate,
            functools.partial(ListIndividual,
                              obj_size=self.ind_size,
                              reduce_fcn=self.fitness_reduce),
            self.toolbox.uniformparams)

        # Register the population format. It is a list of individuals
        self.toolbox.register(
            "population",
            deap.tools.initRepeat,
            list,
            self.toolbox.RandomIndividual)

        # Register the evaluation function for the individuals
        self.toolbox.register("evaluate", self.evaluator.evaluate_with_lists)

        copyreg.pickle(types.MethodType, _reduce_method)

        if self.use_scoop:
            if self.map_function:
                raise Exception(
                    'Impossible to use scoop is providing self defined map '
                    'function: %s' % self.map_function)

            from scoop import futures
            self.toolbox.register("map", futures.map)

        elif self.map_function:
            self.toolbox.register("map", self.map_function)

    def get_stats(self):
        """Get the stats that will be saved during optimisation"""
        stats = deap.tools.Statistics(key=lambda ind: ind.fitness.sum)
        stats.register("avg", numpy.mean)
        stats.register("std", numpy.std)
        stats.register("min", numpy.min)
        stats.register("max", numpy.max)
        return stats

    def run(self):
        """Run optimisation"""
        pass
