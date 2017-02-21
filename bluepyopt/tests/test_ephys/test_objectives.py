"""Tests for ephys.efeatures"""

import os

import nose.tools as nt
from nose.plugins.attrib import attr

import bluepyopt.ephys as ephys


@attr('unit')
def test_EFeatureObjective():
    """ephys.objectives: Testing EFeatureObjective"""

    recording_names = {'': 'square_pulse_step1.soma.v'}

    mean = 1

    efeature = ephys.efeatures.eFELFeature(name='test_eFELFeature',
                                           efel_feature_name='voltage_base',
                                           recording_names=recording_names,
                                           stim_start=700,
                                           stim_end=2700,
                                           exp_mean=mean,
                                           exp_std=1)

    e_obj = ephys.objectives.EFeatureObjective(
        'singleton',
        features=[efeature])

    nt.assert_equal(e_obj.name, 'singleton')
    nt.assert_equal(e_obj.features, [efeature])

    response = ephys.responses.TimeVoltageResponse('mock_response')
    testdata_dir = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        'testdata')
    response.read_csv(os.path.join(testdata_dir, 'TimeVoltageResponse.csv'))
    responses = {'square_pulse_step1.soma.v': response, }

    efeature_value = efeature.calculate_feature(responses)

    nt.assert_almost_equal(
        e_obj.calculate_feature_scores(responses),
        [abs(efeature_value - mean)])


@attr('unit')
def test_SingletonObjective():
    """ephys.objectives: Testing SingletonObjective"""

    recording_names = {'': 'square_pulse_step1.soma.v'}

    mean = 1

    efeature = ephys.efeatures.eFELFeature(name='test_eFELFeature',
                                           efel_feature_name='voltage_base',
                                           recording_names=recording_names,
                                           stim_start=700,
                                           stim_end=2700,
                                           exp_mean=mean,
                                           exp_std=1)

    s_obj = ephys.objectives.SingletonObjective(
        'singleton',
        feature=efeature)

    nt.assert_equal(s_obj.name, 'singleton')
    nt.assert_equal(s_obj.features, [efeature])
    nt.assert_equal(str(s_obj), '( %s )' % str(efeature))

    response = ephys.responses.TimeVoltageResponse('mock_response')
    testdata_dir = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        'testdata')
    response.read_csv(os.path.join(testdata_dir, 'TimeVoltageResponse.csv'))
    responses = {'square_pulse_step1.soma.v': response, }

    efeature_value = efeature.calculate_feature(responses)

    nt.assert_almost_equal(
        s_obj.calculate_score(responses),
        abs(efeature_value - mean))


@attr('unit')
def test_MaxObjective():
    """ephys.objectives: Testing MaxObjective"""

    recording_names = {'': 'square_pulse_step1.soma.v'}

    mean = 1

    efeature1 = ephys.efeatures.eFELFeature(name='test_eFELFeature',
                                            efel_feature_name='voltage_base',
                                            recording_names=recording_names,
                                            stim_start=700,
                                            stim_end=2700,
                                            exp_mean=mean,
                                            exp_std=1)
    efeature2 = ephys.efeatures.eFELFeature(
        name='test_eFELFeature',
        efel_feature_name='steady_state_voltage',
        recording_names=recording_names,
        stim_start=700,
        stim_end=2700,
        exp_mean=mean,
        exp_std=1)

    max_obj = ephys.objectives.MaxObjective(
        'max',
        features=[efeature1, efeature2])

    nt.assert_equal(max_obj.name, 'max')
    nt.assert_equal(max_obj.features, [efeature1, efeature2])

    response = ephys.responses.TimeVoltageResponse('mock_response')
    testdata_dir = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        'testdata')
    response.read_csv(os.path.join(testdata_dir, 'TimeVoltageResponse.csv'))
    responses = {'square_pulse_step1.soma.v': response, }

    efeature_value1 = efeature1.calculate_feature(responses)
    efeature_value2 = efeature2.calculate_feature(responses)

    nt.assert_almost_equal(
        max_obj.calculate_score(responses),
        max(abs(efeature_value1 - mean), abs(efeature_value2 - mean)))


@attr('unit')
def test_WeightedSumObjective():
    """ephys.objectives: Testing WeightedSumObjective"""

    recording_names = {'': 'square_pulse_step1.soma.v'}

    mean = 1
    std = 1

    efeature = ephys.efeatures.eFELFeature(name='test_eFELFeature',
                                           efel_feature_name='voltage_base',
                                           recording_names=recording_names,
                                           stim_start=700,
                                           stim_end=2700,
                                           exp_mean=mean,
                                           exp_std=std)

    weight = .5

    w_obj = ephys.objectives.WeightedSumObjective(
        'weighted',
        features=[efeature],
        weights=[weight])

    nt.assert_equal(w_obj.name, 'weighted')
    nt.assert_equal(w_obj.features, [efeature])
    nt.assert_equal(w_obj.weights, [weight])

    response = ephys.responses.TimeVoltageResponse('mock_response')
    testdata_dir = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        'testdata')
    response.read_csv(os.path.join(testdata_dir, 'TimeVoltageResponse.csv'))
    responses = {'square_pulse_step1.soma.v': response, }

    efeature_value = efeature.calculate_feature(responses)

    nt.assert_almost_equal(
        w_obj.calculate_score(responses),
        abs(efeature_value - mean) * weight)

    nt.assert_raises(Exception, ephys.objectives.WeightedSumObjective,
                     'weighted',
                     features=[efeature],
                     weights=[1, 2])
