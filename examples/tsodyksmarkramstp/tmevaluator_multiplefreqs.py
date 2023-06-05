# -*- coding: utf-8 -*-
"""Tsodyks-Markram model Evaluator used to fit data from multiple frequency
stimulations. This module contains an evaluator for the Tsodyks-Markram model.

@authors: Andras Ecker and Giuseppe Chindemi
@remark: Copyright (c) 2017, EPFL/Blue Brain Project
         This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>
         This library is free software; you can redistribute it and/or modify it
         under the terms of the GNU Lesser General Public License version 3.0 as
         published by the Free Software Foundation.
         This library is distributed in the hope that it will be useful, but
         WITHOUT ANY WARRANTY; without even the implied warranty of
         MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
         See the GNU Lesser General Public License for more details.
         You should have received a copy of the GNU Lesser General Public
         License along with this library; if not, write to the Free Software
         Foundation, Inc.,
         51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import numpy as np
import bluepyopt as bpop
import tmodesolve

try:
    xrange
except NameError:
    xrange = range


class TsodyksMarkramEvaluator(bpop.evaluators.Evaluator):
    def __init__(self, data, params):
        """
        BluePyOpt evulator class.

        Parameters
        ----------
        data : OrderedDict (or a Python 3 dict)
            Frequecies as keys and {t_stims, amps} numpy.ndarray with stim times (ms) and normalized amplitudes
        params : list
            List of parameters to fit. Every entry must be a tuple
            (name, lower bound, upper bound).
        """

        super(TsodyksMarkramEvaluator, self).__init__()
        self.t_stims = {freq:vals["t_spikes"] for freq, vals in data.items()}
        self.amplitudes = {freq:vals["amps"] for freq, vals in data.items()}
        self.params = params
        self.params = [bpop.parameters.Parameter(name, bounds=(minval, maxval))
                       for name, minval, maxval in self.params]

        # Bpop Objectives
        self.objectives = []
        for freq, _ in data.items():
            self.objectives.extend([bpop.objectives.Objective("%s_amplitude_%i"%(freq, i))
                                    for i in xrange(len(self.t_stims[freq]))])

    def generate_model(self, freq, individual):
        """Calls numerical solver `tmodesolve.py` and returns amplitudes based on the input parameters"""

        amps, tm_statevars = tmodesolve.solve_TM(self.t_stims[freq], *individual)
        return amps, tm_statevars

    def evaluate_with_lists(self, individual):
        """Errors used by BluePyOpt for the optimization"""

        errors = []
        for freq, _ in self.t_stims.items():
            candidate_amps, _ = self.generate_model(freq, individual)
            errors.extend(np.power(self.amplitudes[freq] - candidate_amps, 2).tolist())
        return errors

    def init_simulator_and_evaluate_with_lists(self, individual):
        """Calls evaluate_with_lists. Is called during IBEA optimisation."""
        return self.evaluate_with_lists(individual)
