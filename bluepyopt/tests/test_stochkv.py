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


def _remove_first_line(string):
    """Remove first line of string"""

    return '\n'.join(string.split('\n')[1:])


def test_run():
    """StochKv example: test run"""

    import stochkvcell  # NOQA
    py_response, hoc_response, hoc_string = stochkvcell.run_stochkv_model()

    # print py_response['Step.soma.v']['time']
    nt.assert_true(
        py_response['Step.soma.v']['time'].equals(
            hoc_response['Step.soma.v']['time']))
    nt.assert_true(
        py_response['Step.soma.v']['voltage'].equals(
            hoc_response['Step.soma.v']['voltage']))

    expected_hoc_filename = os.path.join(
        STOCHKV_PATH,
        stochkvcell.stochkv_hoc_filename)

    with open(expected_hoc_filename) as expected_hoc_file:
        expected_hoc_string = expected_hoc_file.read()

    nt.assert_equal(
        _remove_first_line(hoc_string),
        _remove_first_line(expected_hoc_string))

'''
class TestL5PCModel(object):

    """Test L5PC model"""

    def __init__(self):
        self.l5pc_cell = None
        self.nrn = None

    def setup(self):
        """Set up class"""
        sys.path.insert(0, L5PC_PATH)

        import l5pc_model  # NOQA
        self.l5pc_cell = l5pc_model.create()
        nt.assert_is_instance(
            self.l5pc_cell,
            bluepyopt.ephys.models.CellModel)
        self.nrn = ephys.simulators.NrnSimulator()

    def test_instantiate(self):
        """L5PC: test instantiation of l5pc cell model"""
        self.l5pc_cell.freeze(release_parameters)
        self.l5pc_cell.instantiate(sim=self.nrn)

    def teardown(self):
        """Teardown"""
        self.l5pc_cell.destroy(sim=self.nrn)


class TestL5PCEvaluator(object):

    """Test L5PC evaluator"""

    def __init__(self):
        self.l5pc_evaluator = None

    def setup(self):
        """Set up class"""

        import l5pc_evaluator  # NOQA

        self.l5pc_evaluator = l5pc_evaluator.create()

        nt.assert_is_instance(
            self.l5pc_evaluator,
            bluepyopt.ephys.evaluators.CellEvaluator)

    @attr('slow')
    def test_eval(self):
        """L5PC: test evaluation of l5pc evaluator"""

        result = self.l5pc_evaluator.evaluate_with_dicts(
            param_dict=release_parameters)

        expected_results = load_from_json('expected_results.json')

        # Use two lines below to update expected result
        # expected_results['TestL5PCEvaluator.test_eval'] = result
        # dump_to_json(expected_results, 'expected_results.json')

        nt.assert_items_equal(
            result,
            expected_results['TestL5PCEvaluator.test_eval'])

    def teardown(self):
        """Teardown"""
        pass

'''
