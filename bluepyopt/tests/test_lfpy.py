"""Functional LFPy test"""

import os
import sys
import pytest

L5PC_LFPY_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '../../examples/l5pc_lfpy'
    )
)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, L5PC_LFPY_PATH)

import l5pc_lfpy_evaluator
from generate_extra_features import release_params


@pytest.mark.slow
def test_lfpy_evaluator():
    """Test CellEvaluator with an LFPy cell and LFPy simulator"""

    evaluator = l5pc_lfpy_evaluator.create(
        feature_file=L5PC_LFPY_PATH + "/extra_features.json",
        cvode_active=False,
        dt=0.025,
    )

    responses = evaluator.run_protocols(
        protocols=evaluator.fitness_protocols.values(),
        param_values=release_params
    )
    values = evaluator.fitness_calculator.calculate_values(responses)

    assert len(values) == 21
    assert abs(values['Step1.soma.AP_height'] - 27.85963902931001) < 1e-5
    assert len(responses['Step1.MEA.v']["voltage"]) == 40
