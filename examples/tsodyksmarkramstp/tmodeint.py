"""Tsodyks-Markram model ODEINT.
This module contains functions to numerically integrate the Tsodyks-Markram
model. The current implementation is a port of an Igor Pro (WaveMetrics)
routine, written by Rodrigo Perin with the help of Raphael Holzer. Many thanks
to Misha Tsodyks and Henry Markram for their support during all development
stages.

@author: Giuseppe Chindemi, Rodrigo Perin
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

# pylint: disable=E741


import numpy as np

try:
    xrange
except NameError:
    xrange = range


def integrate(sampstim, nsamples, dt, vRest, Trec, Tfac,
              ASE, USE, Rinput, Tmem, Tinac, latency):
    """Integrate Tsodyks-Markram model and produce corresponding voltage trace.

    Parameters
    ----------
    sampstim : numpy.ndarray
        Array of sample indices where stimulation occurs.
    nsamples : int
        Number of samples in the trace.
    dt : float
        Time step of the trace.
    vRest : float
        Membrane resting potential (V).
    Trec : float
        Recovery time constant (ms).
    Tfac : float
        Facilitation time constant (ms).
    ASE : float
        Absolute Synaptic Efficacy.
    USE : float
        Utilization of Synaptic Efficacy. Has to be in the interval [0, 1].
    Rinput : float
        Input resistance (MOhm).
    Tmem : float
        Membrane time constant (ms).
    Tinac : float
        Inactivation time constant (ms).
    latency : float
        PSP latency (ms).

    Returns
    -------
    vtrace : numpy.ndarray
        Voltage trace corresponding to the input parameters.
    tm_statevar : dictionary
        Integral of all state variables.
    """
    AP = np.zeros(nsamples)
    I = np.zeros(nsamples)  # NOQA
    R = np.zeros(nsamples)
    E = np.zeros(nsamples)
    U = np.zeros(nsamples)
    P = np.zeros(nsamples)
    # Set stimuli in AP vector
    psp_offset = int(np.round(1e-3 * latency / dt))
    AP[sampstim + psp_offset] = 1
    # Initialize state vectors
    R[0] = 1
    E[0] = 0
    P[0] = 0
    U[0] = USE
    # Integrate TM model ODE
    for i in xrange(1, nsamples):
        R[i] = R[i - 1] + dt * (1 - R[i - 1] - E[i - 1]) * \
            1e3 / Trec - U[i - 1] * R[i - 1] * AP[i - 1]
        E[i] = E[i - 1] - dt * E[i - 1] * 1e3 / Tinac + U[i - 1] * \
            R[i - 1] * AP[i - 1]
        U[i] = U[i - 1] - dt * (U[i - 1] - USE) * 1e3 / \
            Tfac + USE * (1 - U[i - 1]) * AP[i - 1]
        P[i] = P[i - 1] + dt * (Rinput * ASE / 10 **
                                6 * E[i - 1] - P[i - 1]) * 1e3 / Tmem
    # Update state
    P = P + vRest
    E = E * ASE / 10**12
    I = 1 - R - E  # NOQA
    tm_statevar = {'recovered': R, 'effective': E, 'used': U, 'inactive': I}
    return P, tm_statevar
