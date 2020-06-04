"""eFeature classes"""

"""
Copyright (c) 2016, EPFL/Blue Brain Project

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

import logging

from bluepyopt.ephys.base import BaseEPhys
from bluepyopt.ephys.serializer import DictMixin

logger = logging.getLogger(__name__)


class EFeature(BaseEPhys):

    """EPhys feature"""
    pass


class eFELFeature(EFeature, DictMixin):

    """eFEL feature"""

    SERIALIZED_FIELDS = ('name', 'efel_feature_name', 'recording_names',
                         'stim_start', 'stim_end', 'exp_mean',
                         'exp_std', 'threshold', 'comment')

    def __init__(
            self,
            name,
            efel_feature_name=None,
            recording_names=None,
            stim_start=None,
            stim_end=None,
            exp_mean=None,
            exp_std=None,
            threshold=None,
            stimulus_current=None,
            comment='',
            interp_step=None,
            double_settings=None,
            int_settings=None,
            string_settings=None,
            force_max_score=False,
            max_score=250
    ):
        """Constructor

        Args:
            name (str): name of the eFELFeature object
            efel_feature_name (str): name of the eFeature in the eFEL library
                (ex: 'AP1_peak')
            recording_names (dict): eFEL features can accept several recordings
                as input
            stim_start (float): stimulation start time (ms)
            stim_end (float): stimulation end time (ms)
            exp_mean (float): experimental mean of this eFeature
            exp_std(float): experimental standard deviation of this eFeature
            threshold(float): spike detection threshold (mV)
            comment (str): comment
            interp_step(float): interpolation step (ms)
            double_settings(dict): dictionary with efel double settings that
                should be set before extracting the features
            int_settings(dict): dictionary with efel int settings that
                should be set before extracting the features
            string_settings(dict): dictionary with efel string settings that
                should be set before extracting the features
        """

        super(eFELFeature, self).__init__(name, comment)

        self.recording_names = recording_names
        self.efel_feature_name = efel_feature_name
        self.exp_mean = exp_mean
        self.exp_std = exp_std
        self.stim_start = stim_start
        self.stim_end = stim_end
        self.threshold = threshold
        self.interp_step = interp_step
        self.stimulus_current = stimulus_current
        self.double_settings = double_settings
        self.int_settings = int_settings
        self.string_settings = string_settings
        self.force_max_score = force_max_score
        self.max_score = max_score

    def _construct_efel_trace(self, responses):
        """Construct trace that can be passed to eFEL"""

        trace = {}
        if '' not in self.recording_names:
            raise Exception(
                'eFELFeature: \'\' needs to be in recording_names')
        for location_name, recording_name in self.recording_names.items():
            if location_name == '':
                postfix = ''
            else:
                postfix = ';%s' % location_name

            if recording_name not in responses:
                logger.debug(
                    "Recording named %s not found in responses %s",
                    recording_name,
                    str(responses))
                return None

            if responses[self.recording_names['']] is None or \
                    responses[recording_name] is None:
                return None
            trace['T%s' % postfix] = \
                responses[self.recording_names['']]['time']
            trace['V%s' % postfix] = responses[recording_name]['voltage']
            trace['stim_start%s' % postfix] = [self.stim_start]
            trace['stim_end%s' % postfix] = [self.stim_end]

        return trace

    def _setup_efel(self):
        """Set up efel before extracting the feature"""

        import efel
        efel.reset()

        if self.threshold is not None:
            efel.setThreshold(self.threshold)

        if self.stimulus_current is not None:
            efel.setDoubleSetting('stimulus_current', self.stimulus_current)

        if self.interp_step is not None:
            efel.setDoubleSetting('interp_step', self.interp_step)

        if self.double_settings is not None:
            for setting_name, setting_value in self.double_settings.items():
                efel.setDoubleSetting(setting_name, setting_value)

        if self.int_settings is not None:
            for setting_name, setting_value in self.int_settings.items():
                efel.setIntSetting(setting_name, setting_value)

        if self.string_settings is not None:
            for setting_name, setting_value in self.string_settings.items():
                efel.setStrSetting(setting_name, setting_value)

    def calculate_feature(self, responses, raise_warnings=False):
        """Calculate feature value"""

        efel_trace = self._construct_efel_trace(responses)

        if efel_trace is None:
            feature_value = None
        else:
            self._setup_efel()

            import efel
            values = efel.getMeanFeatureValues(
                [efel_trace],
                [self.efel_feature_name],
                raise_warnings=raise_warnings)
            feature_value = values[0][self.efel_feature_name]

            efel.reset()

        logger.debug(
            'Calculated value for %s: %s',
            self.name,
            str(feature_value))

        return feature_value

    def calculate_score(self, responses, trace_check=False):
        """Calculate the score"""

        efel_trace = self._construct_efel_trace(responses)

        if efel_trace is None:
            score = self.max_score
        else:
            self._setup_efel()

            import efel
            score = efel.getDistance(
                efel_trace,
                self.efel_feature_name,
                self.exp_mean,
                self.exp_std,
                trace_check=trace_check,
                error_dist=self.max_score
            )
            if self.force_max_score:
                score = min(score, self.max_score)

            efel.reset()

        logger.debug('Calculated score for %s: %f', self.name, score)

        return score

    def __str__(self):
        """String representation"""

        return "%s for %s with stim start %s and end %s, " \
            "exp mean %s and std %s and AP threshold override %s" % \
            (self.efel_feature_name,
             self.recording_names,
             self.stim_start,
             self.stim_end,
             self.exp_mean,
             self.exp_std,
             self.threshold)
