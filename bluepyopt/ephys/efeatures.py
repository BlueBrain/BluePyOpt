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
            comment=''):
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
        """

        super(eFELFeature, self).__init__(name, comment)

        self.recording_names = recording_names
        self.efel_feature_name = efel_feature_name
        self.exp_mean = exp_mean
        self.exp_std = exp_std
        self.stim_start = stim_start
        self.stim_end = stim_end
        self.threshold = threshold

    def _construct_efel_trace(self, responses):
        """Construct trace that can be passed to eFEL"""

        trace = {}
        if '' not in self.recording_names:
            raise Exception(
                'eFELFeature: \'\' needs to be in recording_names')
        for location_name, recording_name in self.recording_names.iteritems():
            if location_name == '':
                postfix = ''
            else:
                postfix = ';%s' % location_name

            if responses[self.recording_names['']] is None or \
                    responses[recording_name] is None:
                return None
            trace['T%s' % postfix] = \
                responses[self.recording_names['']]['time']
            trace['V%s' % postfix] = responses[recording_name]['voltage']
            trace['stim_start%s' % postfix] = [self.stim_start]
            trace['stim_end%s' % postfix] = [self.stim_end]

        return trace

    def calculate_feature(self, responses, raise_warnings=False):
        """Calculate feature value"""

        efel_trace = self._construct_efel_trace(responses)

        if efel_trace is None:
            feature_value = None
        else:

            import efel
            efel.reset()

            values = efel.getMeanFeatureValues(
                [efel_trace],
                [self.efel_feature_name],
                raise_warnings=raise_warnings)
            feature_value = values[0][self.efel_feature_name]

            efel.reset()

        return feature_value

    def calculate_score(self, responses):
        """Calculate the score"""

        efel_trace = self._construct_efel_trace(responses)

        if efel_trace is None:
            score = 250.0
        else:
            import efel
            efel.reset()

            if self.threshold:
                efel.setThreshold(self.threshold)

            score = efel.getDistance(
                efel_trace,
                self.efel_feature_name,
                self.exp_mean,
                self.exp_std)

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
