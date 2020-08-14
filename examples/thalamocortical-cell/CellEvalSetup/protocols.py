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

# pylint: disable=R0914

import numpy
import warnings
import collections
import copy
import json
import bluepyopt.ephys as ephys

import os

import argparse
parser = argparse.ArgumentParser(description='cell')
parser.add_argument('--live', action="store_true", default=False,
                  help='plot live')
args, unknown = parser.parse_known_args()

live_plot = False

if live_plot:
    import matplotlib.pyplot as plt


class StepProtocolCustom(ephys.protocols.StepProtocol):

    """Step protocol with custom options to turn stochkv_det on or off"""

    def __init__(
            self,
            name=None,
            step_stimulus=None,
            holding_stimulus=None,
            recordings=None,
            cvode_active=None):
        """Constructor"""

        super(StepProtocolCustom, self).__init__(
            name,
            step_stimulus=step_stimulus,
            holding_stimulus=holding_stimulus,
            recordings=recordings,
            cvode_active=cvode_active)


    def run(self, cell_model, param_values, sim=None, isolate=None):
        """Run protocol"""

        responses = {}

        responses.update(super(StepProtocolCustom, self).run(
            cell_model,
            param_values,
            sim=sim,
            isolate=isolate))

        
        for mechanism in cell_model.mechanisms:
            mechanism.deterministic = True
        self.cvode_active = True

        return responses


class RampProtocol(ephys.protocols.SweepProtocol):

    """Protocol consisting of ramp and holding current"""

    def __init__(
            self,
            name=None,
            ramp_stimulus=None,
            holding_stimulus=None,
            recordings=None,
            cvode_active=None):
        """Constructor
        Args:
            name (str): name of this object
            step_stimulus (list of Stimuli): Stimulus objects used in protocol
            recordings (list of Recordings): Recording objects used in the
                protocol
            cvode_active (bool): whether to use variable time step
        """

        super(RampProtocol, self).__init__(
            name,
            stimuli=[
                ramp_stimulus,
                holding_stimulus]
            if holding_stimulus is not None else [ramp_stimulus],
            recordings=recordings,
            cvode_active=cvode_active)

        self.ramp_stimulus = ramp_stimulus
        self.holding_stimulus = holding_stimulus

    @property
    def step_delay(self):
        """Time stimulus starts"""
        return self.ramp_stimulus.ramp_delay

    @property
    def step_duration(self):
        """Time stimulus starts"""
        return self.ramp_stimulus.ramp_duration
