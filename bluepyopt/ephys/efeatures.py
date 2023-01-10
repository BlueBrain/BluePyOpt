"""eFeature classes"""

"""
Copyright (c) 2016-2020, EPFL/Blue Brain Project

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
import numpy as np

from bluepyopt.ephys.base import BaseEPhys
from bluepyopt.ephys.serializer import DictMixin
from .extra_features_utils import *

logger = logging.getLogger(__name__)


def masked_cosine_distance(exp, model):
    from scipy.spatial import distance

    exp_mask = np.isfinite(exp)
    model_mask = np.isfinite(model)
    valid_mask = exp_mask & model_mask

    score = distance.cosine(
        exp[valid_mask], model[valid_mask]
    )

    score *= sum(exp_mask) / len(valid_mask)

    return score


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


class extraFELFeature(EFeature, DictMixin):
    """extraFEL feature"""

    SERIALIZED_FIELDS = ('name', 'extrafel_feature_name', 'recording_names',
                         'somatic_recording_name', 'fcut', 'fs',
                         'channel_ids', 'stim_start', 'stim_end',
                         'exp_mean', 'exp_std', 'threshold', 'comment')

    def __init__(
            self,
            name,
            extrafel_feature_name=None,
            recording_names=None,
            somatic_recording_name=None,
            fcut=None,
            fs=None,
            filt_type=None,
            ms_cut=None,
            upsample=None,
            skip_first_spike=True,
            skip_last_spike=True,
            channel_ids=None,
            stim_start=None,
            stim_end=None,
            exp_mean=None,
            exp_std=None,
            threshold=None,
            comment='',
            interp_step=None,
            double_settings=None,
            int_settings=None,
            force_max_score=False,
            max_score=250,
    ):
        """Constructor

        Args:
            name (str): name of the extraFELFeature object
            extrafel_feature_name (str): name of the eFeature in the
                spikefeatures library (ex: 'halfwidth')
            recording_names (dict): eFEL features can accept several
                recordings as input
            somatic_recording_name (str): intracellualar recording from soma,
                used to detect spikes. If None, spikes are detected from
                extracellular trace
            fcut (float, array, or None): cutoff frequency(ies) for filter. If
                float, a high-pass filter is used. If array-like a bandpass
                filter is used. If None, traces are note filtered
            fs (float): sampling frequency to resample extracellular traces
                (in kHz)
            filt_type (str): type of the bandpass filter used
                (default 'filtfilt')
            ms_cut (float, list, or None): cut in ms before and after the
                intra peak. If scalar, the cut is symmetrical
            upsample (int, or None): upsample factor for average waveform
                before computing features
            skip_first_spike (bool): if True, the first spike is skipped
                before computing the average waveform
                (to avoid artifacts)
            skip_last_spike (bool): if True, the last spike is skipped
                before computing the average waveform
                (to avoid artifacts)
            channel_ids (int, np.array, or None): if None, all channels are
                used to compute the feature and calculate the score
                (using the cosine_dist). If int, a single channel is used and
                the score is the normalised deviation form the exp value.
                If list/array, the cosine distance is computed over a subset
                of channels
            stim_start (float): stimulation start time (ms)
            stim_end (float): stimulation end time (ms)
            exp_mean (list of floats): experimental mean of this eFeature
            exp_std (list of floats): experimental standard deviation
                of this eFeature
            threshold (float): spike detection threshold (mV)
            comment (str): comment
            interp_step (float): interpolation step (ms)
            double_settings (dict): dictionary with efel double settings that
                should be set before extracting the features
            int_settings (dict): dictionary with efel int settings that
                should be set before extracting the features
        """

        super(extraFELFeature, self).__init__(name, comment)

        self.recording_names = recording_names
        self.somatic_recording_name = somatic_recording_name
        self.extrafel_feature_name = extrafel_feature_name
        self.fcut = fcut
        self.fs = fs
        self.filt_type = filt_type
        self.ms_cut = ms_cut
        self.upsample = upsample
        self.skip_first_spike = skip_first_spike
        self.skip_last_spike = skip_last_spike
        self.channel_ids = channel_ids
        self.exp_mean = exp_mean
        self.exp_std = exp_std
        self.stim_start = stim_start
        self.stim_end = stim_end
        self.threshold = threshold
        self.interp_step = interp_step
        self.double_settings = double_settings
        self.int_settings = int_settings
        self.force_max_score = force_max_score
        self.max_score = max_score

    def _construct_somatic_efel_trace(self, responses):
        """Construct trace that can be passed to eFEL"""

        trace = {}
        if self.somatic_recording_name not in responses:
            logger.debug(
                "Recording named %s not found in responses %s",
                self.somatic_recording_name,
                str(responses),
            )
            return None

        if responses[self.somatic_recording_name] is None:
            return None

        response = responses[self.somatic_recording_name]

        trace["T"] = response["time"]
        trace["V"] = response["voltage"]
        trace["stim_start"] = [self.stim_start]
        trace["stim_end"] = [self.stim_end]

        return trace

    def _setup_efel(self):
        """Set up efel before extracting the feature"""

        import efel

        efel.reset()

        if self.threshold is not None:
            efel.setThreshold(self.threshold)

        if self.interp_step is not None:
            efel.setDoubleSetting("interp_step", self.interp_step)

        if self.double_settings is not None:
            for setting_name, setting_value in self.double_settings.items():
                efel.setDoubleSetting(setting_name, setting_value)

        if self.int_settings is not None:
            for setting_name, setting_value in self.int_settings.items():
                efel.setIntSetting(setting_name, setting_value)

    def _get_peak_times(self, responses, raise_warnings=False):

        efel_trace = self._construct_somatic_efel_trace(responses)

        if efel_trace is None:
            peak_times = None
        else:
            self._setup_efel()

            import efel

            peaks = efel.getFeatureValues(
                [efel_trace], ["peak_time"], raise_warnings=raise_warnings
            )
            peak_times = peaks[0]["peak_time"]

            efel.reset()

        return peak_times

    def calculate_feature(
            self,
            responses,
            raise_warnings=False,
            return_waveforms=False,
    ):
        from .extra_features_utils import calculate_features

        """Calculate feature value"""
        peak_times = self._get_peak_times(
            responses, raise_warnings=raise_warnings
        )

        if len(peak_times) > 1 and self.skip_first_spike:
            peak_times = peak_times[1:]

        if len(peak_times) > 1 and self.skip_last_spike:
            peak_times = peak_times[:-1]

        if responses[self.recording_names[""]] is not None:
            response = responses[self.recording_names[""]]
        else:
            return None

        if np.std(np.diff(response["time"])) > 0.001 * np.mean(
                np.diff(response["time"])
        ):
            assert self.fs is not None
            logger.info("extraFELFeature.calculate_feature: interpolate")
            response_interp = _interpolate_response(response, fs=self.fs)
        else:
            response_interp = response

        if self.fcut is not None:
            logger.info("extraFELFeature.calculate_feature: enabled")
            response_filter = _filter_response(response_interp,
                                               fcut=self.fcut,
                                               filt_type=self.filt_type)
        else:
            logger.info("extraFELFeature.calculate_feature: filter disabled")
            response_filter = response_interp

        ewf = _get_waveforms(response_filter, peak_times, self.ms_cut)
        mean_wf = np.mean(ewf, axis=0)

        values = calculate_features(
            mean_wf,
            self.fs * 1000,
            upsample=self.upsample,
            feature_names=[self.extrafel_feature_name]
        )

        feature_value = values[self.extrafel_feature_name]

        if self.channel_ids is not None:
            feature_value = feature_value[self.channel_ids]

        logger.debug(
            "Calculated value for %s: %s", self.name, str(feature_value)
        )

        if return_waveforms:
            return feature_value, mean_wf
        else:
            return feature_value

    def calculate_score(self, responses, trace_check=False):
        """Calculate the score"""

        if (
                responses[self.recording_names[""].replace("soma.v",
                                                           "MEA.LFP")]
                is None
                or responses[self.recording_names[""]] is None
        ):
            return self.max_score

        feature_value = self.calculate_feature(responses)

        if np.isscalar(feature_value):
            # scalar feature
            if np.isfinite(feature_value):
                score = np.abs((feature_value - self.exp_mean)) / self.exp_std
            else:
                score = self.max_score
            if not np.isfinite(score):
                logger.debug(
                    f"Found score nan value {self.extrafel_feature_name} "
                    f"- std: {self.exp_std} - channel: {self.channel_ids}"
                )
                score = self.max_score
        else:
            score = masked_cosine_distance(
                np.asarray(self.exp_mean),
                np.asarray(feature_value)
            )

        if np.isnan(score):
            score = self.max_score

        if self.force_max_score:
            score = min(score, self.max_score)

        logger.debug("Calculated score for %s: %f", self.name, score)

        return score

    def __str__(self):
        """String representation"""

        return ("%s for %s with stim start %s and end %s, "
                "exp mean %s and std %s and AP threshold override %s"
                % (self.extrafel_feature_name,
                   self.recording_names,
                   self.stim_start,
                   self.stim_end,
                   self.exp_mean,
                   self.exp_std,
                   self.threshold)
                )


def _interpolate_response(response, fs=20.0):
    from scipy.interpolate import interp1d

    x = response["time"]
    y = response["voltage"]
    f = interp1d(x, y, axis=1)
    xnew = np.arange(np.min(x), np.max(x), 1.0 / fs)
    ynew = f(xnew)  # use interpolation function returned by `interp1d`

    response_new = {}
    response_new["time"] = xnew
    response_new["voltage"] = ynew

    return response_new


def _filter_response(response, fcut=[0.5, 6000], order=2, filt_type="lfilter"):
    import scipy.signal as ss

    fs = 1 / np.mean(np.diff(response["time"])) * 1000
    fn = fs / 2.0

    trace = response["voltage"]

    if isinstance(fcut, (float, int, np.floating, np.integer)):
        btype = "highpass"
        band = fcut / fn
    else:
        assert isinstance(fcut, (list, np.ndarray)) and len(fcut) == 2
        btype = "bandpass"
        band = np.array(fcut) / fn

    b, a = ss.butter(order, band, btype=btype)

    if len(trace.shape) == 2:
        if filt_type == "filtfilt":
            filtered = ss.filtfilt(b, a, trace, axis=1)
        else:
            filtered = ss.lfilter(b, a, trace, axis=1)
    else:
        if filt_type == "filtfilt":
            filtered = ss.filtfilt(b, a, trace)
        else:
            filtered = ss.lfilter(b, a, trace)

    response_new = {}
    response_new["time"] = response["time"]
    response_new["voltage"] = filtered

    return response_new


def _get_waveforms(response, peak_times, snippet_len_ms):
    times = response["time"]
    traces = response["voltage"]

    assert np.std(np.diff(times)) < 0.001 * np.mean(
        np.diff(times)
    ), "Sampling frequency must be constant"

    fs = 1.0 / np.mean(np.diff(times))  # kHz

    reference_frames = (peak_times * fs).astype(int)

    if isinstance(snippet_len_ms, (tuple, list, np.ndarray)):
        snippet_len_before = int(snippet_len_ms[0] * fs)
        snippet_len_after = int(snippet_len_ms[1] * fs)
    else:
        snippet_len_before = int((snippet_len_ms + 1) / 2 * fs)
        snippet_len_after = int((snippet_len_ms - snippet_len_before) * fs)

    num_snippets = len(peak_times)
    if len(traces.shape) == 2:
        num_channels = traces.shape[0]
    else:
        num_channels = 1
        traces = traces[np.newaxis, :]
    num_frames = len(times)
    snippet_len_total = int(snippet_len_before + snippet_len_after)
    waveforms = np.zeros(
        (num_snippets, num_channels, snippet_len_total), dtype=traces.dtype
    )

    for i in range(num_snippets):
        snippet_chunk = np.zeros(
            (num_channels, snippet_len_total), dtype=traces.dtype
        )
        if 0 <= reference_frames[i] < num_frames:
            snippet_range = np.array(
                [
                    int(reference_frames[i]) - snippet_len_before,
                    int(reference_frames[i]) + snippet_len_after,
                ]
            )
            snippet_buffer = np.array([0, snippet_len_total], dtype="int")
            # The following handles the out-of-bounds cases
            if snippet_range[0] < 0:
                snippet_buffer[0] -= snippet_range[0]
                snippet_range[0] -= snippet_range[0]
            if snippet_range[1] >= num_frames:
                snippet_buffer[1] -= snippet_range[1] - num_frames
                snippet_range[1] -= snippet_range[1] - num_frames
            snippet_chunk[:, snippet_buffer[0]:snippet_buffer[1]] = \
                traces[:, snippet_range[0]:snippet_range[1]]
        waveforms[i] = snippet_chunk

    return waveforms
