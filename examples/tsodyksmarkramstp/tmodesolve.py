# -*- coding: utf-8 -*-
"""Tsodyks-Markram model ODE solver
This module contains functions to solve the Tsodyks-Markram
model. (same equations as in Maass and Markram 2002)

@author: Andras Ecker
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


def solve_TM(t_stims, USE, Trec, Tfac, ASE):
    """Solve Tsodyks-Markram model and produce corresponding amplitudes.

    Parameters
    ----------
    t_stims : numpy.ndarray
        Array of stimulation times (ms)
    USE : float
        Utilization of Synaptic Efficacy. Has to be in the interval [0, 1].
    Trec : float
        Recovery time constant (ms).
    Tfac : float
        Facilitation time constant (ms).
    ASE : float
        Absolute Synaptic Efficacy.

    Returns
    -------
    Ampls : numpy.ndarray
        Normalized amplitudes corresponding to input parameters
    tm_statevars : dictionary
        Value of state variables at stimulation times
    """

    # Initialize state vectors
    U = np.zeros_like(t_stims)
    R = np.zeros_like(t_stims)
    Ampls = np.zeros_like(t_stims)
    R[0] = 1
    U[0] = USE
    Ampls[0] = ASE*U[0]*R[0]
    R[0] = R[0] - R[0]*U[0]
    U[0] = U[0] + USE*(1-U[0])
    last_stim = t_stims[0]

    for i in range(1, len(t_stims)):
        delta_t = t_stims[i] - last_stim
        R[i] = 1 + (R[i-1] - 1)*np.exp(-delta_t/Trec)
        U[i] = USE + (U[i-1] - USE)*np.exp(-delta_t/Tfac)
        Ampls[i] = ASE*U[i]*R[i]
        R[i] = R[i] - R[i]*U[i]
        U[i] = U[i] + USE*(1-U[i])
        last_stim = t_stims[i]

    tm_statevars = {"R": R, "U": U}

    return Ampls, tm_statevars
