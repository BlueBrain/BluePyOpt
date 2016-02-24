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

# pylint: disable=R0912


import random

import logging

import deap
import deap.creator
import deap.base
import deap.algorithms
import deap.tools
import pickle

logger = logging.getLogger('__main__')

# TODO decide which variables go in constructor, which ones go in 'run' function
# TODO abstract the algorithm by creating a class for every algorithm, that way
# settings of the algorithm can be stored in objects of these classes


class Optimisation(object):

    """Optimisation class"""

    _instance_counter = 0

    def __init__(self, evaluator=None):
        """Constructor"""

        self.evaluator = evaluator


class DEAPOptimisation(Optimisation):

    """DEAP Optimisation class"""

    _instance_counter = 0

    def __init__(self, evaluator=None,
                 use_scoop=False,
                 seed=1,
                 offspring_size=10,
                 eta=10,
                 mutpb=1.0,
                 cxpb=1.0):
        """Constructor"""

        super(DEAPOptimisation, self).__init__(evaluator=evaluator)

        Optimisation._instance_counter += 1

        # Disabling for now because it clashes with scoop
        # TODO has to be reenabled ! (until deap.creator global classes are
        # fixed)
        # if Optimisation._instance_counter > 1:
        #    raise Exception(
        #        'At the moment only one Optimisation object is allowed '
        #        'to exist simultaneously')

        self.deap_classnames = []

        self.use_scoop = use_scoop
        self.seed = seed
        self.offspring_size = offspring_size
        self.eta = eta
        self.cxpb = cxpb
        self.mutpb = mutpb
        # Create a DEAP toolbox
        self.toolbox = deap.base.Toolbox()

        self.setup_deap()

    def __del__(self):
        """Destructor"""
        self.destroy_deap()

    def create_deap_class(self, name, base, **kwargs):
        """Create a class in deap.creator"""

        deap.creator.create(name, base, **kwargs)
        self.deap_classnames.append(name)

    def setup_deap(self):
        """Set up optimisation"""

        # Number of objectives
        OBJ_SIZE = len(self.evaluator.objectives)

        class WeightedSumFitness(deap.base.Fitness):

            """Fitness that compares by weighted sum"""

            def __init__(self, values=()):
                deap.base.Fitness.__init__(self, values)

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

        # Create a fitness function
        # By default DEAP selector will try to maximise fitness values,
        # so we add a -1 weight value to minise
        self.create_deap_class("WeightedSumFitness",
                               WeightedSumFitness,
                               weights=[-1.0] * OBJ_SIZE)

        # Create an individual that consists of a list
        self.create_deap_class(
            "ListIndividual",
            list,
            fitness=deap.creator.WeightedSumFitness)

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
        # An indiviual is create by 'deap.creator.Individual' and parameters
        # are initially
        # picked by 'uniform'
        self.toolbox.register(
            "Individual",
            deap.tools.initIterate,
            deap.creator.ListIndividual,
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
        self.toolbox.register("select", deap.tools.selIBEA)

        # toolbox.register("select", deap.tools.selIBEA)
        # toolbox.register("select", deap.tools.selIBEA)

        if self.use_scoop:
            from scoop import futures
            self.toolbox.register("map", futures.map)

            def _reduce_method(meth):
                """Overwrite reduce"""
                return (getattr, (meth.__self__, meth.__func__.__name__))
            import copy_reg
            import types
            copy_reg.pickle(types.MethodType, _reduce_method)

        # import multiprocessing

        # pool = multiprocessing.Pool()
        # self.toolbox.register("map", pool.map)

    def destroy_deap(self):
        """Destroy deap class"""

        for classname in self.deap_classnames:
            if hasattr(deap.creator, classname):
                delattr(deap.creator, classname)
        Optimisation._instance_counter -= 1

    def run(self, max_ngen=10, continue_cp=False, cp_filename=None):
        """Run optimisation"""

        # Total number of generation to run
        NGEN = max_ngen

        # Crossover, mutation probabilities
        CXPB = self.cxpb
        MUTPB = self.mutpb

        # Total population size of EA
        # ALPHA = POP_SIZE
        # Total parent population size of EA
        MU = self.offspring_size
        # Total offspring size of EA
        # LAMBDA = OFFSPRING_SIZE

        # Generate the population object
        pop = self.toolbox.population(n=MU)

        hof = deap.tools.HallOfFame(10)

        stats = deap.tools.Statistics(key=lambda ind: ind.fitness.sum)

        import numpy
        stats.register("avg", numpy.mean)
        stats.register("std", numpy.std)
        stats.register("min", numpy.min)
        stats.register("max", numpy.max)

        pop, log, history = eaAlphaMuPlusLambdaCheckpoint(
            pop,
            self.toolbox,
            MU,
            None,
            CXPB,
            MUTPB,
            NGEN,
            stats=stats,
            halloffame=hof,
            continue_cp=continue_cp,
            cp_filename=cp_filename)

        return pop, hof, log, history

# pylint: disable=R0912, R0914

# TODO this function shouldn't be here


def eaAlphaMuPlusLambdaCheckpoint(
        population,
        toolbox,
        mu,
        _,
        cxpb,
        mutpb,
        ngen,
        stats=None,
        halloffame=None,
        checkpoint_freq=1,
        cp_filename=None,
        continue_cp=False):
    r"""This is the :math:`(~\alpha,\mu~,~\lambda)` evolutionary algorithm."""

    if continue_cp:
        # A file name has been given, then load the data from the file
        cp = pickle.load(open(cp_filename, "r"))
        population = cp["population"]
        parents = cp["parents"]
        start_gen = cp["generation"]
        halloffame = cp["halloffame"]
        logbook = cp["logbook"]
        history = cp["history"]
        random.setstate(cp["rndstate"])
    else:
        # Start a new evolution
        start_gen = 1
        parents = population[:]
        logbook = deap.tools.Logbook()
        logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])
        history = deap.tools.History()

        # TODO this first loop should be not be repeated !

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in population if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        record = stats.compile(population) if stats is not None else {}
        logbook.record(gen=start_gen, nevals=len(invalid_ind), **record)

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(population)

        if history is not None:
            history.update(population)

    if history is not None:
        toolbox.decorate("mate", history.decorator)
        toolbox.decorate("mutate", history.decorator)

    # Begin the generational process
    for gen in range(start_gen + 1, ngen + 1):
        # Vary the parents
        if hasattr(toolbox, 'variate'):
            offspring = toolbox.variate(parents, toolbox, cxpb, mutpb)
        else:
            offspring = deap.algorithms.varAnd(parents, toolbox, cxpb, mutpb)

        population[:] = parents + offspring

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offspring)

        if history is not None:
            history.update(offspring)

        # Select the next generation parents
        parents[:] = toolbox.select(population, mu)

        # Update the statistics with the new population
        record = stats.compile(population) if stats is not None else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)

        print logbook.stream

        if cp_filename and checkpoint_freq:
            if gen % checkpoint_freq == 0:
                cp = dict(population=population, generation=gen,
                          parents=parents,
                          halloffame=halloffame,
                          history=history,
                          logbook=logbook, rndstate=random.getstate())
                pickle.dump(
                    cp,
                    open(cp_filename, "wb"))
                logger.debug('Wrote checkpoint to %s', cp_filename)

    return population, logbook, history
