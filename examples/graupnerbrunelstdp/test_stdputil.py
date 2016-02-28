import unittest
import stdputil
import numpy as np
import numpy.testing as npt


def test_protocol_outcome():
    """
    Test against Fig. 3 of Graupner and Brunel (2012).
    TODO, Ask permission to Michael to add testing files.

    Notes
    -----
    Data used for the test were kindly provprot_ided by Dr. M. Graupner.
    Fig. 3F cannot be reproduced because generated using an approximate
    solution.
    """
    # Case 1: Fig. 3B
    mgspike = np.loadtxt('/gpfs/bbp.cscs.ch/home/chindemi/proj32/graupner/data/post_spike.dat')
    dt = mgspike[:, 0]
    outcome = np.zeros(len(dt))
    for i in xrange(len(dt)):
        p = stdputil.Protocol(['pre', 'post'], [dt[i] * 1e-3], 5.0, 200.0)
        outcome[i] = stdputil.protocol_outcome(p, stdputil.param_hippocampal)
    npt.assert_allclose(outcome, mgspike[:, 1], rtol=1e-05)

    # Case 2: Fig. 3D
    mgspike = np.loadtxt('/gpfs/bbp.cscs.ch/home/chindemi/proj32/graupner/data/post_burst_100.dat')
    dt = mgspike[:, 0]
    outcome = np.zeros(len(dt))
    for i in xrange(len(dt)):
        p = stdputil.Protocol(['post', 'post', 'pre'], [11.5e-3, -dt[i] * 1e-3], 5.0, 100.0)
        outcome[i] = stdputil.protocol_outcome(p, stdputil.param_hippocampal)
    npt.assert_allclose(outcome, mgspike[:, 1], rtol=1e-05)

    # Case 3: Fig. 3E
    mgspike = np.loadtxt('/gpfs/bbp.cscs.ch/home/chindemi/proj32/graupner/data/post_burst_30.dat')
    dt = mgspike[:, 0]
    outcome = np.zeros(len(dt))
    for i in xrange(len(dt)):
        p = stdputil.Protocol(['post', 'post', 'pre'], [11.5e-3, -dt[i] * 1e-3], 5.0, 30.0)
        outcome[i] = stdputil.protocol_outcome(p, stdputil.param_hippocampal)
    npt.assert_allclose(outcome, mgspike[:, 1], rtol=1e-05)

