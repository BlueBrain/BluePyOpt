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
import numpy

import deap
import deap.base
import deap.algorithms
import deap.tools

from . import algorithms
from . import tools
from . import DEAPOptimisation

logger = logging.getLogger('__main__')


class IBEADEAPOptimisation(DEAPOptimisation):

    """IBEA DEAP class"""

    def __init__(self,
                 evaluator=None,
                 use_scoop=False,
                 seed=1,
                 offspring_size=10,
                 eta=10,
                 mutpb=1.0,
                 cxpb=1.0,
                 map_function=None,
                 hof=None,
                 selector_name=None,
                 fitness_reduce=numpy.sum):
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
            fitness_reduce (fcn): function used to reduce the objective values
                to a single fitness score
         """

        super(IBEADEAPOptimisation, self).__init__(evaluator=evaluator,
                                                   use_scoop=use_scoop,
                                                   seed=seed,
                                                   map_function=map_function,
                                                   hof=hof,
                                                   fitness_reduce=fitness_reduce)

        self.offspring_size = offspring_size
        self.eta = eta
        self.cxpb = cxpb
        self.mutpb = mutpb

        self.selector_name = selector_name
        if self.selector_name is None:
            self.selector_name = 'IBEA'

        self.setup_deap()
        self.setup_deapIBEA()

    def setup_deapIBEA(self):
        """Set up optimisation"""

        # Register the mate operator
        self.toolbox.register(
            "mate",
            deap.tools.cxSimulatedBinaryBounded,
            eta=self.eta,
            low=self.lbounds,
            up=self.ubounds)

        # Register the mutation operator
        self.toolbox.register(
            "mutate",
            deap.tools.mutPolynomialBounded,
            eta=self.eta,
            low=self.lbounds,
            up=self.ubounds,
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

    def run(self,
            max_ngen=10,
            offspring_size=None,
            continue_cp=False,
            cp_filename=None,
            cp_frequency=1):
        """Run optimisation"""
        # Allow run function to override offspring_size
        # TODO probably in the future this should not be an object field anymore
        # keeping for backward compatibility
        if offspring_size is None:
            offspring_size = self.offspring_size

        # Generate the population object
        pop = self.toolbox.population(n=offspring_size)

        stats = self.get_stats()

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
