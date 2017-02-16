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
'''

@attr('unit')
def test_eFELFeature():
    """ephys.efeatures: Testing eFELFeature creation"""
    recording_names = {'': 'square_pulse_step1.soma.v'}
    efeature = efeatures.eFELFeature(name='test_eFELFeature',
                                     efel_feature_name='voltage_base',
                                     recording_names=recording_names,
                                     stim_start=700,
                                     stim_end=2700,
                                     exp_mean=1,
                                     exp_std=1)

    response = TimeVoltageResponse('mock_response')
    testdata_dir = joinp(os.path.dirname(os.path.abspath(__file__)), 'testdata')
    response.read_csv(joinp(testdata_dir, 'TimeVoltageResponse.csv'))
    responses = {'square_pulse_step1.soma.v': response, }

    ret = efeature.calculate_feature(responses, raise_warnings=True)
    nt.assert_almost_equal(ret, -72.069487699766668)

    score = efeature.calculate_score(responses)
    nt.assert_almost_equal(score, 73.06948769976667)

    nt.eq_(efeature.name, 'test_eFELFeature')
    nt.ok_('voltage_base' in str(efeature))


@attr('unit')
def test_eFELFeature_double_settings():
    """ephys.efeatures: Testing eFELFeature double_settings"""
    recording_names = {'': 'square_pulse_step1.soma.v'}
    efeature = efeatures.eFELFeature(name='test_eFELFeature',
                                     efel_feature_name='voltage_base',
                                     recording_names=recording_names,
                                     stim_start=700,
                                     stim_end=2700,
                                     exp_mean=1,
                                     exp_std=1)
    efeature_ds = efeatures.eFELFeature(
        name='test_eFELFeature_other_perc',
        efel_feature_name='voltage_base',
        recording_names=recording_names,
        stim_start=700,
        stim_end=2700,
        exp_mean=1,
        exp_std=1,
        double_settings={
            'voltage_base_start_perc': 0.01})

    response = TimeVoltageResponse('mock_response')
    testdata_dir = joinp(os.path.dirname(os.path.abspath(__file__)), 'testdata')
    response.read_csv(joinp(testdata_dir, 'TimeVoltageResponse.csv'))
    responses = {'square_pulse_step1.soma.v': response, }

    vb_other_perc = efeature_ds.calculate_feature(
        responses,
        raise_warnings=True)
    vb = efeature.calculate_feature(responses, raise_warnings=True)

    nt.assert_true(vb_other_perc != vb)


@attr('unit')
def test_eFELFeature_int_settings():
    """ephys.efeatures: Testing eFELFeature int_settings"""
    recording_names = {'': 'square_pulse_step1.soma.v'}
    efeature = efeatures.eFELFeature(name='test_eFELFeature',
                                     efel_feature_name='Spikecount',
                                     recording_names=recording_names,
                                     stim_start=1200,
                                     stim_end=2000,
                                     exp_mean=1,
                                     exp_std=1)
    efeature_strict = efeatures.eFELFeature(
        name='test_eFELFeature_strict',
        efel_feature_name='Spikecount',
        recording_names=recording_names,
        stim_start=1200,
        stim_end=2000,
        exp_mean=1,
        exp_std=1,
        int_settings={
            'strict_stiminterval': True})

    response = TimeVoltageResponse('mock_response')
    testdata_dir = joinp(os.path.dirname(os.path.abspath(__file__)), 'testdata')
    response.read_csv(joinp(testdata_dir, 'TimeVoltageResponse.csv'))
    responses = {'square_pulse_step1.soma.v': response, }

    spikecount = efeature.calculate_feature(responses)
    spikecount_strict = efeature_strict.calculate_feature(responses)

    nt.assert_true(spikecount_strict != spikecount)


@attr('unit')
def test_eFELFeature_serialize():
    """ephys.efeatures: Testing eFELFeature serialization"""
    recording_names = {'': 'square_pulse_step1.soma.v'}
    efeature = efeatures.eFELFeature(name='test_eFELFeature',
                                     efel_feature_name='voltage_base',
                                     recording_names=recording_names,
                                     stim_start=700,
                                     stim_end=2700,
                                     exp_mean=1,
                                     exp_std=1)
    serialized = efeature.to_dict()
    deserialized = instantiator(serialized)
    nt.ok_(isinstance(deserialized, efeatures.eFELFeature))
    nt.eq_(deserialized.stim_start, 700)
    nt.eq_(deserialized.recording_names, recording_names)

'''
