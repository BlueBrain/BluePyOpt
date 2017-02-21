"""Test ephys model objects"""

# pylint: disable=R0914

import os

import nose.tools as nt
from nose.plugins.attrib import attr

from bluepyopt import ephys

TESTDATA_DIR = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    'testdata')

simple_morphology_path = os.path.join(TESTDATA_DIR, 'simple.swc')


@attr('unit')
def test_CellEvaluator_init():
    """ephys.evaluators: Test CellEvaluator init"""
    sim = ephys.simulators.NrnSimulator()

    model = ephys.models.CellModel('test_model', params=[])

    fitness_calc = ephys.objectivescalculators.ObjectivesCalculator()

    evaluator = ephys.evaluators.CellEvaluator(
        cell_model=model,
        param_names=[],
        fitness_calculator=fitness_calc,
        sim=sim)

    nt.assert_true(isinstance(evaluator, ephys.evaluators.CellEvaluator))
    nt.assert_equal(
        str(evaluator),
        'cell evaluator:\n  cell model:\n    test_model:\n  morphology:\n  '
        'mechanisms:\n  params:\n\n  fitness protocols:\n  '
        'fitness calculator:\n    objectives:\n\n')


@attr('unit')
def test_CellEvaluator_evaluate():
    """ephys.evaluators: Test CellEvaluator evaluate"""
    sim = ephys.simulators.NrnSimulator()

    simple_morph = ephys.morphologies.NrnFileMorphology(
        simple_morphology_path,
        do_replace_axon=True)

    all_loc = ephys.locations.NrnSeclistLocation('all', 'all')

    cm = ephys.parameters.NrnRangeParameter(
        name='cm',
        param_name='cm',
        bounds=[.5, 1.5],
        locations=[all_loc])

    cell_model = ephys.models.CellModel('CellModel',
                                        morph=simple_morph,
                                        mechs=[],
                                        params=[cm])

    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name='soma_loc',
        seclist_name='somatic',
        sec_index=0,
        comp_x=.5)

    rec_soma = ephys.recordings.CompRecording(
        name='soma.v',
        location=soma_loc,
        variable='v')

    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.1,
        step_delay=100.0,
        step_duration=100,
        total_duration=200,
        location=soma_loc)

    protocol = ephys.protocols.SweepProtocol(
        name='prot',
        stimuli=[stim],
        recordings=[rec_soma])

    mean = -65

    efeature = ephys.efeatures.eFELFeature(name='test_eFELFeature',
                                           efel_feature_name='voltage_base',
                                           recording_names={'': 'soma.v'},
                                           stim_start=100.0,
                                           stim_end=200.0,
                                           exp_mean=-65,
                                           exp_std=1)

    s_obj = ephys.objectives.SingletonObjective(
        'singleton',
        feature=efeature)

    fitness_calc = ephys.objectivescalculators.ObjectivesCalculator(
        objectives=[s_obj])

    evaluator = ephys.evaluators.CellEvaluator(
        cell_model=cell_model,
        param_names=['cm'],
        fitness_calculator=fitness_calc,
        fitness_protocols={'sweep': protocol},
        sim=sim)

    responses = protocol.run(cell_model, {'cm': 1.0}, sim=sim)
    feature_value = efeature.calculate_feature(responses)

    score = evaluator.evaluate([1.0])
    expected_score = abs(mean - feature_value)

    nt.assert_almost_equal(score, expected_score)

    score_dict = evaluator.objective_dict(score)

    nt.assert_almost_equal(score_dict['singleton'], expected_score)
