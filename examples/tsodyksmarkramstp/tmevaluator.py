"""Tsodyks-Markram model Evaluator.
This module contains an evaluator for the Tsodyks-Markram model.
 
@author: Giuseppe Chindemi
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
import bluepyopt as bpop
import numpy as np
import tmodeint


class TsodyksMarkramEvaluator(bpop.evaluators.Evaluator):
    def __init__(self, t, v, tstim, params):
        """
        Parameters
        ----------
        t : numpy.ndarray
            Time vector.
        v : numpy.ndarray
            Voltage vector, must have same dimension of t.
        tstim : numpy.ndarray
            Time of the stimuli.
        params : list
            List of parameters to fit. Every entry must be a tuple 
            (name, lower bound, upper bound). 
        """
        super(TsodyksMarkramEvaluator, self).__init__()
        self.v = v
        self.t = t
        self.stimidx = np.searchsorted(t, tstim)
        self.dx = t[1] - t[0]
        self.nsamples = len(v)
        self.params = params
        # Find voltage baseline
        bs_stop = np.searchsorted(t, tstim[0])
        self.vrest = np.mean(v[:bs_stop])
        # Compute time windows where to compare model and data
        offset = 0.005  # s
        window = 0.04  # s
        window_samples = int(np.round(window/self.dx))
        psp_start = np.searchsorted(t, tstim+offset)
        psp_stop = psp_start + window_samples
        psp_stop[-1] += 2*window_samples  # Extend last psp window (RTR case)
        self.split_idx = list(zip(psp_start, psp_stop))
        # Parameters to be optimized
        self.params = [bpop.parameters.Parameter(name, bounds=(minval, maxval))
                       for name, minval, maxval in self.params]
        # Objectives
        self.objectives = [bpop.objectives.Objective('interval_%d' % (i,))
                           for i in range(len(self.split_idx))]

    def generate_model(self, individual):
        v, _ = tmodeint.integrate(self.stimidx, self.nsamples, self.dx,
                                  self.vrest, *individual)
        return v

    def evaluate_with_lists(self, individual):
        candidate_v = self.generate_model(individual)
        errors = [np.linalg.norm(self.v[t0:t1] - candidate_v[t0:t1])
                  for t0, t1 in self.split_idx]
        return errors

    def evaluate_with_lists_aggregate(self, param_values):
        errors = self.evaluate_with_lists(param_values)
        return np.linalg.norm(errors)

