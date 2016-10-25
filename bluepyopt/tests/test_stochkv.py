"""Test l5pc example"""

import os
import sys
import nose.tools as nt

STOCHKV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            '../../examples/stochkv'))

sys.path.insert(0, STOCHKV_PATH)

from bluepyopt import ephys

neuron_sim = ephys.simulators.NrnSimulator()

neuron_sim.neuron.h.nrn_load_dll(
    os.path.join(
        STOCHKV_PATH,
        'x86_64/.libs/libnrnmech.so'))


def test_import():
    """StochKv example: test import"""

    import stochkvcell  # NOQA


def test_run():
    """StochKv example: test run"""

    import stochkvcell  # NOQA
    for deterministic in [True, False]:
        py_response, hoc_response, different_seed_response, hoc_string = \
            stochkvcell.run_stochkv_model(deterministic=deterministic)

        nt.assert_true(
            py_response['Step.soma.v']['time'].equals(
                hoc_response['Step.soma.v']['time']))
        nt.assert_true(
            py_response['Step.soma.v']['voltage'].equals(
                hoc_response['Step.soma.v']['voltage']))
        if deterministic:
            nt.assert_true(
                py_response['Step.soma.v']['voltage'].equals(
                    different_seed_response['Step.soma.v']['voltage']))
        else:
            nt.assert_false(
                py_response['Step.soma.v']['voltage'].equals(
                    different_seed_response['Step.soma.v']['voltage']))

        expected_hoc_filename = os.path.join(
            STOCHKV_PATH,
            stochkvcell.stochkv_hoc_filename(deterministic=deterministic))

        with open(expected_hoc_filename) as expected_hoc_file:
            expected_hoc_string = expected_hoc_file.read()

        nt.assert_equal(
            hoc_string,
            expected_hoc_string)
