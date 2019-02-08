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

import deap
import deap.base
import deap.algorithms
import deap.tools

from . import algorithms
from . import tools

import bluepyopt.optimisations

logger = logging.getLogger('__main__')

# TODO decide which variables go in constructor,which ones go in 'run' function
# TODO abstract the algorithm by creating a class for every algorithm, that way
# settings of the algorithm can be stored in objects of these classes


class WeightedSumFitness(deap.base.Fitness):

    """Fitness that compares by weighted sum"""

    def __init__(self, values=(), obj_size=None):
        self.weights = [-1.0] * obj_size if obj_size is not None else [-1]

        super(WeightedSumFitness, self).__init__(values)

    @property
    def weighted_sum(self):
        """Weighted sum of wvalues"""
        return sum(self.wvalues)

    @property
    def sum(self):
        """Weighted sum of values"""
        return sum(self.values)

    def __le__(self, other):
        return self.weighted_sum <= other.weighted_sum

    def __lt__(self, other):
        return self.weighted_sum < other.weighted_sum

    def __deepcopy__(self, _):
        """Override deepcopy"""

        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result


class WSListIndividual(list):

    """Individual consisting of list with weighted sum field"""

    def __init__(self, *args, **kwargs):
        """Constructor"""
        self.fitness = WeightedSumFitness(obj_size=kwargs['obj_size'])
        del kwargs['obj_size']
        super(WSListIndividual, self).__init__(*args, **kwargs)


class DEAPOptimisation(bluepyopt.optimisations.Optimisation):

    """DEAP Optimisation class"""

    def __init__(self, evaluator=None,
                 use_scoop=False,
                 seed=1,
                 offspring_size=10,
                 eta=10,
                 mutpb=1.0,
                 cxpb=1.0,
                 map_function=None,
                 hof=None,
                 selector_name=None):
        """Constructor

        Args:
            evaluator (Evaluator): Evaluator object
            seed (float): Random number generator seed
            offspring_size (int): Number of offspring individuals in each
                generation
            eta (float): Parameter that controls how far the crossover and
            mutation operator disturbe the original individuals
            mutpb (float): Mutation probability
            cxpb (float): Crossover probability
            map_function (function): Function used to map (parallelise) the
                evaluation function calls
            hof (hof): Hall of Fame object
            selector_name (str): The selector used in the evolutionary
                algorithm, possible values are 'IBEA' or 'NSGA2'
        """

        super(DEAPOptimisation, self).__init__(evaluator=evaluator)

        self.use_scoop = use_scoop
        self.seed = seed
        self.offspring_size = offspring_size
        self.eta = eta
        self.cxpb = cxpb
        self.mutpb = mutpb
        self.map_function = map_function

        self.selector_name = selector_name
        if self.selector_name is None:
            self.selector_name = 'IBEA'

        self.hof = hof
        if self.hof is None:
            self.hof = deap.tools.HallOfFame(10)

        # Create a DEAP toolbox
        self.toolbox = deap.base.Toolbox()

        self.setup_deap()

    def setup_deap(self):
        """Set up optimisation"""

        # Number of objectives
        OBJ_SIZE = len(self.evaluator.objectives)

        # Set random seed
        random.seed(self.seed)

        # Eta parameter of crossover / mutation parameters
        # Basically defines how much they 'spread' solution around
        # The lower this value, the more spread
        ETA = self.eta

        # Number of parameters
        IND_SIZE = len(self.evaluator.params)

        # Bounds for the parameters

        LOWER = []
        UPPER = []

        for parameter in self.evaluator.params:
            LOWER.append(parameter.lower_bound)
            UPPER.append(parameter.upper_bound)

        # Define a function that will uniformly pick an individual
        def uniform(lower_list, upper_list, dimensions):
            """Fill array """

            if hasattr(lower_list, '__iter__'):
                return [random.uniform(lower, upper) for lower, upper in
                        zip(lower_list, upper_list)]
            else:
                return [random.uniform(lower_list, upper_list)
                        for _ in range(dimensions)]

        # Register the 'uniform' function
        self.toolbox.register("uniformparams", uniform, LOWER, UPPER, IND_SIZE)

        # Register the individual format
        # An indiviual is create by WSListIndividual and parameters
        # are initially
        # picked by 'uniform'
        self.toolbox.register(
            "Individual",
            deap.tools.initIterate,
            functools.partial(WSListIndividual, obj_size=OBJ_SIZE),
            self.toolbox.uniformparams)

        # Register the population format. It is a list of individuals
        self.toolbox.register(
            "population",
            deap.tools.initRepeat,
            list,
            self.toolbox.Individual)

        # Register the evaluation function for the individuals
        # import deap_efel_eval1
        self.toolbox.register("evaluate", self.evaluator.evaluate_with_lists)

        # Register the mate operator
        self.toolbox.register(
            "mate",
            deap.tools.cxSimulatedBinaryBounded,
            eta=ETA,
            low=LOWER,
            up=UPPER)

        # Register the mutation operator
        self.toolbox.register(
            "mutate",
            deap.tools.mutPolynomialBounded,
            eta=ETA,
            low=LOWER,
            up=UPPER,
            indpb=0.5)

        # Register the variate operator
        self.toolbox.register("variate", deap.algorithms.varAnd)

        # Register the selector (picks parents from population)
        if self.selector_name == 'IBEA':
            self.toolbox.register("select", tools.selIBEA)
        elif self.selector_name == 'NSGA2':
            self.toolbox.register("select", deap.tools.emo.selNSGA2)
        else:
            raise ValueError('DEAPOptimisation: Constructor selector_name '
                             'argument only accepts "IBEA" or "NSGA2"')

        def _reduce_method(meth):
            """Overwrite reduce"""
            return (getattr, (meth.__self__, meth.__func__.__name__))
        import copyreg
        import types
        copyreg.pickle(types.MethodType, _reduce_method)

        if self.use_scoop:
            if self.map_function:
                raise Exception(
                    'Impossible to use scoop is providing self '
                    'defined map function: %s' %
                    self.map_function)

            from scoop import futures
            self.toolbox.register("map", futures.map)

        elif self.map_function:
            self.toolbox.register("map", self.map_function)

    def run(self,
            max_ngen=10,
            offspring_size=None,
            continue_cp=False,
            cp_filename=None,
            cp_frequency=1):
        """Run optimisation"""
        # Allow run function to override offspring_size
        # TODO probably in the future this should not be an object field
        # anymore
        # keeping for backward compatibility
        if offspring_size is None:
            offspring_size = self.offspring_size

        # Generate the population object
        pop = self.toolbox.population(n=offspring_size)

        stats = deap.tools.Statistics(key=lambda ind: ind.fitness.sum)
        import numpy
        stats.register("avg", numpy.mean)
        stats.register("std", numpy.std)
        stats.register("min", numpy.min)
        stats.register("max", numpy.max)

        pop, hof, log, history = algorithms.eaAlphaMuPlusLambdaCheckpoint(
            pop,
            self.toolbox,
            offspring_size,
            self.cxpb,
            self.mutpb,
            max_ngen,
            stats=stats,
            halloffame=self.hof,
            cp_frequency=cp_frequency,
            continue_cp=continue_cp,
            cp_filename=cp_filename)

        # Update hall of fame
        self.hof = hof

        return pop, self.hof, log, history


class IBEADEAPOptimisation(DEAPOptimisation):

    """IBEA DEAP class"""

    def __init__(self, *args, **kwargs):
        """Constructor"""

        super(IBEADEAPOptimisation, self).__init__(*args, **kwargs)
