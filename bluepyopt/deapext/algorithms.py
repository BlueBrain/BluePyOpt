"""Optimisation class"""

"""
Copyright (c) 2016-2020, EPFL/Blue Brain Project

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

# pylint: disable=R0914, R0912


import random
import logging
import shutil
import os

import deap.algorithms
import deap.tools
import pickle
from tqdm.auto import tqdm
from .stoppingCriteria import MaxNGen
import streamlit as st
logger = logging.getLogger('__main__')
import numpy as np
def _define_fitness(pop, obj_size):
	''' Re-instanciate the fitness of the individuals for it to matches the
	evaluation function.
	'''
	from .optimisations import WSListIndividual

	new_pop = []
	if pop:
		for ind in pop:
			new_pop.append(WSListIndividual(list(ind), obj_size=obj_size))

	return new_pop


def _evaluate_invalid_fitness(toolbox, population):
	'''Evaluate the individuals with an invalid fitness

	Returns the count of individuals with invalid fitness
	'''
	invalid_ind = [ind for ind in population if not ind.fitness.valid]
	fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
	for ind, fit in zip(invalid_ind, fitnesses):
		ind.fitness.values = fit

	return len(invalid_ind)


def _update_history_and_hof(halloffame, history, population):
	'''Update the hall of fame with the generated individuals

	Note: History and Hall-of-Fame behave like dictionaries
	'''
	if halloffame is not None:
		halloffame.update(population)

	history.update(population)


def _record_stats(stats, logbook, gen, population, invalid_count):
	'''Update the statistics with the new population'''
	record = stats.compile(population) if stats is not None else {}
	logbook.record(gen=gen, nevals=invalid_count, **record)

from deap import tools
def _get_offspring_time_diminishing_eta(parents, toolbox, cxpb, mutpb,gen, ngen):
	'''return the offspring, use toolbox.variate if possible'''


	BOUND_LOW = []
	BOUND_UP = []
	NDIM = len(parents[0])
	fit_dim = len(parents[0].fitness.values)
	for x in range(0,len(parents[0])):
		BOUND_LOW.append(toolbox.uniformparams.args[0][x])
		BOUND_UP.append(toolbox.uniformparams.args[1][x])
	ETA = int(30.0*(1-(gen/ngen)))
	toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=ETA)
	toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=ETA, indpb=1.0/NDIM)
	if (1-(gen/ngen))/2.0>0.05:
		mutpb = (1-(gen/ngen))/2.0
	else:
		mutpb = 0.05
	if (1-(gen/ngen))>0.4:
		cxpb = (1-(gen/ngen))/1.1
	else:
		cxpb = 0.4
	if hasattr(toolbox, 'variate'):
		return toolbox.variate(parents, toolbox, cxpb, mutpb)
	return deap.algorithms.varAnd(parents, toolbox, cxpb, mutpb)

def _get_offspring(parents, toolbox, cxpb, mutpb):
	"""return the offspring, use toolbox.variate if possible"""

	if hasattr(toolbox, "variate"):
		return toolbox.variate(parents, toolbox, cxpb, mutpb)
	return deap.algorithms.varAnd(parents, toolbox, cxpb, mutpb)


def _check_stopping_criteria(criteria, params):
	for c in criteria:
		c.check(params)
		if c.criteria_met:
			logger.info('Run stopped because of stopping criteria: ' +
						c.name)
			return True
	else:
		return False

def filter_parents(parents):
	#Remove the genes that represent the cliff
	#edge. Possibly counter productive.
	import copy
	parentsc = copy.copy(parents)
	orig_len = len(parents)
	cnt = 0
	for p in parentsc:
		flag=False
		for fv in p.fitness.values:
			if fv == 1000.0:
				flag=True
		if flag:
			cnt += 1
	while cnt > 0:
		for i, p in enumerate(parentsc):
			flag=False
			for fv in p.fitness.values:
				if fv == 1000.0:
					flag=True
			if flag:
				del parentsc[i]
				cnt -= 1
	cnt=0
	while len(parentsc) < orig_len:
		parentsc.append(parentsc[cnt])
		cnt+=1
	return parentsc


def eaAlphaMuPlusLambdaCheckpoint(
		population,
		toolbox,
		mu,
		cxpb,
		mutpb,
		ngen,
		stats=None,
		halloffame=None,
		cp_frequency=1,
		cp_filename=None,
		continue_cp=False):
	r"""This is the :math:`(~\alpha,\mu~,~\lambda)` evolutionary algorithm

	Args:
		population(list of deap Individuals)
		toolbox(deap Toolbox)
		mu(int): Total parent population size of EA
		cxpb(float): Crossover probability
		mutpb(float): Mutation probability
		ngen(int): Total number of generation to run
		stats(deap.tools.Statistics): generation of statistics
		halloffame(deap.tools.HallOfFame): hall of fame
		cp_frequency(int): generations between checkpoints
		cp_filename(string): path to checkpoint filename
		continue_cp(bool): whether to continue
	"""

	if cp_filename:
		cp_filename_tmp = cp_filename + '.tmp'

	if continue_cp:
		# A file name has been given, then load the data from the file
		cp = pickle.load(open(cp_filename, "rb"))
		population = cp["population"]
		parents = cp["parents"]
		start_gen = cp["generation"]
		halloffame = cp["halloffame"]
		logbook = cp["logbook"]
		history = cp["history"]
		random.setstate(cp["rndstate"])
		obj_size = len(population[0].fitness.wvalues)
		population = _define_fitness(population, obj_size)
		parents = _define_fitness(parents, obj_size)
		_evaluate_invalid_fitness(toolbox, parents)
		_evaluate_invalid_fitness(toolbox, population)

	else:
		prog_bar = st.progress(0)
		# Start a new evolution
		start_gen = 1
		parents = population[:]
		logbook = deap.tools.Logbook()
		logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])
		history = deap.tools.History()

		invalid_count = _evaluate_invalid_fitness(toolbox, population)
		_update_history_and_hof(halloffame, history, population)
		_record_stats(stats, logbook, start_gen, population, invalid_count)
		logger.info(logbook.stream)
	stopping_criteria = [MaxNGen(ngen)]

	# Begin the generational process
	gen = start_gen + 1
	stopping_params = {"gen": gen}
	pbar = tqdm(total=ngen)
	while not(_check_stopping_criteria(stopping_criteria, stopping_params)):
		#offspring = _get_offspring(parents, toolbox, cxpb, mutpb)
		offspring = _get_offspring_time_diminishing_eta(parents, toolbox, cxpb, mutpb,gen,ngen)
		population = parents + offspring
		population.append(halloffame[0])
		#flo = np.sum(copy.copy(halloffame[0].fitness.values))
		#stopping_params.update({'hof':flo})
		stop = _check_stopping_criteria(stopping_criteria, stopping_params)

		invalid_count = _evaluate_invalid_fitness(toolbox, offspring)
		_update_history_and_hof(halloffame, history, population)
		_record_stats(stats, logbook, gen, population, invalid_count)
		# Select the next generation parents
		##
		# was /4
		##
		parents = toolbox.select(population, int(mu/4.0)) # try 2.5 as divisor.

		logger.info(logbook.stream)

		if(cp_filename and cp_frequency and
		   gen % cp_frequency == 0):
			cp = dict(population=population,
					  generation=gen,
					  parents=parents,
					  halloffame=halloffame,
					  history=history,
					  logbook=logbook,
					  rndstate=random.getstate())
			pickle.dump(cp, open(cp_filename_tmp, "wb"))
			if os.path.isfile(cp_filename_tmp):
				shutil.copy(cp_filename_tmp, cp_filename)
				logger.debug('Wrote checkpoint to %s', cp_filename)
		current_prog = gen / ngen
		prog_bar.progress(current_prog)
		gen += 1
		stopping_params["gen"] = gen
		pbar.update(1)
	pbar.update(1)
	pbar.close()

	return population, halloffame, logbook, history
