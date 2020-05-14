"""CMA Optimisation class"""

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

import logging
import numpy
import pickle
import random
import functools

import deap.tools

from .CMA_SO import CMA_SO
from .CMA_MO import CMA_MO
from . import utils

import bluepyopt.optimisations

logger = logging.getLogger('__main__')


def _ind_convert_space(ind, convert_fcn):
    return [f(x) for f, x in zip(convert_fcn, ind)]


class DEAPOptimisationCMA(bluepyopt.optimisations.Optimisation):

    """Optimisation class for CMA-based evolution strategies"""

    def __init__(self,
                 evaluator=None,
                 use_scoop=False,
                 seed=1,
                 offspring_size=None,
                 centroids=None,
                 sigma=0.4,
                 map_function=None,
                 hof=None,
                 selector_name="single_objective",
                 fitness_reduce=numpy.sum):
        """Constructor

        Args:
            evaluator (Evaluator): Evaluator object
            seed (float): Random number generator seed
            offspring_size (int): Number of offspring individuals in each
                generation
            centroids (list): list of initial guesses used as the starting
                points of the CMA-ES
            sigma (float): initial standard deviation of the distribution
            map_function (function): Function used to map (parallelize) the
                evaluation function calls
            hof (hof): Hall of Fame object
            selector_name (str): The selector used in the evolutionary
                algorithm, possible values are 'single_objective' or
                'multi_objective'
            fitness_reduce (fcn): function used to reduce the objective values
                to a single fitness score
        """

        super(DEAPOptimisationCMA, self).__init__(evaluator=evaluator)

        self.use_scoop = use_scoop
        self.seed = seed
        self.map_function = map_function

        self.hof = hof
        if self.hof is None:
            self.hof = deap.tools.HallOfFame(10)

        self.fitness_reduce = fitness_reduce
        self.offspring_size = offspring_size
        self.centroids = centroids
        self.sigma = sigma

        self.selector_name = selector_name
        if self.selector_name == 'single_objective':
            self.cma_creator = CMA_SO
        elif self.selector_name == 'multi_objective':
            self.cma_creator = CMA_MO
        else:
            raise Exception("The selector_name has to be 'single_objective' "
                            "or 'multi_objective'. Not "
                            "{}".format(self.selector_name))

        # Number of objective values
        self.problem_size = len(self.evaluator.params)

        # Number of parameters
        self.ind_size = len(self.evaluator.objectives)

        # Create a DEAP toolbox
        self.toolbox = deap.base.Toolbox()

        # Bounds for the parameters
        self.lbounds = [p.lower_bound for p in self.evaluator.params]
        self.ubounds = [p.upper_bound for p in self.evaluator.params]

        # Instantiate functions converting individuals from the original
        # parameter space to (and from) a normalized space bounded to [-1.;1]
        self.ubounds = numpy.asarray(self.ubounds)
        self.lbounds = numpy.asarray(self.lbounds)
        bounds_radius = (self.ubounds - self.lbounds) / 2.
        bounds_mean = (self.ubounds + self.lbounds) / 2.

        self.to_norm = []
        self.to_space = []
        for r, m in zip(bounds_radius, bounds_mean):
            self.to_norm.append(
                functools.partial(lambda param, bm, br: (param - bm) / br,
                                  bm=m, br=r))
            self.to_space.append(
                functools.partial(lambda param, bm, br: (param * br) + bm,
                                  bm=m, br=r))

        # Overwrite the bounds with -1. and 1.
        self.lbounds = numpy.full(self.problem_size, -1.)
        self.ubounds = numpy.full(self.problem_size, 1.)

        self.setup_deap()

        # In case initial guesses were provided, rescale them to the norm space
        if self.centroids is not None:
            self.centroids = [self.toolbox.Individual(
                _ind_convert_space(ind, self.to_norm)) for ind in centroids]

    def setup_deap(self):
        """Set up optimisation"""

        # Set random seed
        random.seed(self.seed)
        numpy.random.seed(self.seed)

        # Register the 'uniform' function
        self.toolbox.register("uniformparams",
                              utils.uniform,
                              self.lbounds,
                              self.ubounds,
                              self.ind_size)

        # Register the individual format
        self.toolbox.register(
            "Individual",
            functools.partial(utils.WSListIndividual,
                              obj_size=self.ind_size,
                              reduce_fcn=self.fitness_reduce)
        )

        # A Random Indiviual is create by ListIndividual and parameters are
        # initially picked by 'uniform'
        self.toolbox.register(
            "RandomInd",
            deap.tools.initIterate,
            functools.partial(utils.WSListIndividual,
                              obj_size=self.ind_size,
                              reduce_fcn=self.fitness_reduce),
            self.toolbox.uniformparams)

        # Register the population format. It is a list of individuals
        self.toolbox.register(
            "population",
            deap.tools.initRepeat,
            list,
            self.toolbox.RandomInd)

        # Register the evaluation function for the individuals
        self.toolbox.register("evaluate", self.evaluator.evaluate_with_lists)

        import copyreg
        import types
        copyreg.pickle(types.MethodType, utils.reduce_method)

        if self.use_scoop:
            if self.map_function:
                raise Exception(
                    'Impossible to use scoop is providing self defined map '
                    'function: %s' % self.map_function)

            from scoop import futures
            self.toolbox.register("map", futures.map)

        elif self.map_function:
            self.toolbox.register("map", self.map_function)

    def run(self,
            max_ngen=0,
            cp_frequency=1,
            continue_cp=False,
            cp_filename=None):
        """ Run the optimizer until a stopping criteria is met.

        Args:
            max_ngen(int): Total number of generation to run
            cp_frequency(int): generations between checkpoints
            continue_cp(bool): whether to continue
            cp_filename(string): path to checkpoint filename
        """

        stats = self.get_stats()

        if continue_cp:

            # A file name has been given, then load the data from the file
            cp = pickle.load(open(cp_filename, "br"))
            gen = cp["generation"]
            self.hof = cp["halloffame"]
            logbook = cp["logbook"]
            history = cp["history"]
            random.setstate(cp["rndstate"])
            numpy.random.set_state(cp["np_rndstate"])
            CMA_es = cp["CMA_es"]
            CMA_es.map_function = self.map_function

        else:

            history = deap.tools.History()
            logbook = deap.tools.Logbook()
            logbook.header = ["gen", "nevals"] + stats.fields

            # Instantiate the CMA strategy centered on the centroids
            CMA_es = self.cma_creator(centroids=self.centroids,
                                      offspring_size=self.offspring_size,
                                      sigma=self.sigma,
                                      max_ngen=max_ngen,
                                      IndCreator=self.toolbox.Individual,
                                      RandIndCreator=self.toolbox.RandomInd,
                                      map_function=self.map_function,
                                      use_scoop=self.use_scoop)

            if self.selector_name == 'multi_objective':
                to_evaluate = CMA_es.get_parents(self.to_space)
                fitness = self.toolbox.map(self.toolbox.evaluate, to_evaluate)
                fitness = list(map(list, fitness))
                CMA_es.set_fitness_parents(fitness)
            gen = 1

        pop = CMA_es.get_population(self.to_space)

        # Run until a termination criteria is met
        while CMA_es.active:
            logger.info("Generation {}".format(gen))

            # Generate the new populations
            n_out = CMA_es.generate_new_pop(lbounds=self.lbounds,
                                            ubounds=self.ubounds)
            logger.debug("Number of individuals outside of bounds: {} "
                         "({:.2f}%)".format(n_out, 100. *
                                            n_out / len(CMA_es.population)))

            # Get all the individuals in the original space for evaluation
            to_evaluate = CMA_es.get_population(self.to_space)

            # Compute the fitness
            fitness = self.toolbox.map(self.toolbox.evaluate, to_evaluate)
            fitness = list(map(list, fitness))
            nevals = len(to_evaluate)
            CMA_es.set_fitness(fitness)

            # Update the hall of fame, history and logbook
            pop = CMA_es.get_population(self.to_space)
            utils.update_history_and_hof(self.hof, history, pop)
            record = utils.record_stats(stats, logbook, gen, pop, nevals)
            logger.info(logbook.stream)

            # Update the CMA strategy using the new fitness and check if
            # termination conditions were reached
            CMA_es.update_strategy()
            CMA_es.check_termination(gen)

            if cp_filename and cp_frequency and gen % cp_frequency == 0:

                # Map function shouldn't be pickled
                temp_mf = CMA_es.map_function
                CMA_es.map_function = None

                cp = dict(population=pop,
                          generation=gen,
                          halloffame=self.hof,
                          history=history,
                          logbook=logbook,
                          rndstate=random.getstate(),
                          np_rndstate=numpy.random.get_state(),
                          CMA_es=CMA_es)
                pickle.dump(cp, open(cp_filename, "wb"))
                logger.debug('Wrote checkpoint to %s', cp_filename)

                CMA_es.map_function = temp_mf

            gen += 1

        return pop, self.hof, logbook, history

    def get_stats(self):
        """Get the stats that will be saved during optimisation"""
        stats = deap.tools.Statistics(key=lambda ind: ind.fitness.reduce)
        stats.register("avg", numpy.mean)
        stats.register("std", numpy.std)
        stats.register("min", numpy.min)
        stats.register("max", numpy.max)
        return stats
