"""Extra features functions"""

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

import numpy as np

all_1D_features = [
    "peak_to_valley",
    "halfwidth",
    "peak_trough_ratio",
    "repolarization_slope",
    "recovery_slope",
    "neg_peak_relative",
    "pos_peak_relative",
    "neg_peak_diff",
    "pos_peak_diff",
    "neg_image",
    "pos_image",
]


def calculate_features(
    waveforms,
    sampling_frequency,
    upsample=None,
    feature_names=None,
    recovery_slope_window=0.7
):
    """Calculate features for all waveforms

    Parameters
    ----------
    waveforms  : numpy.ndarray (num_waveforms x num_samples)
        waveforms to compute features for
    sampling_frequency  : float
        rate at which the waveforms are sampled (Hz)
    feature_names : list or None (if None, compute all)
        features to compute
    recovery_slope_window : float
        windowlength in ms after peak wherein recovery slope is computed

    Returns
    -------
    metrics : dict  (num_waveforms x num_metrics)
        Dictionary with computed metrics. Keys are the metric names, values
            are the computed features

    """
    metrics = dict()

    if feature_names is None:
        feature_names = all_1D_features
    else:
        for name in feature_names:
            assert name in all_1D_features, f"{name} not in {all_1D_features}"

    if upsample is not None:
        assert upsample > 0
        waveforms = _upsample_wf(waveforms, int(upsample))
        sampling_frequency = upsample * sampling_frequency

    if "peak_to_valley" in feature_names:
        metrics["peak_to_valley"] = peak_to_valley(
            waveforms=waveforms, sampling_frequency=sampling_frequency
        )
    if "peak_trough_ratio" in feature_names:
        metrics["peak_trough_ratio"] = peak_trough_ratio(waveforms=waveforms)

    if "halfwidth" in feature_names:
        metrics["halfwidth"] = halfwidth(
            waveforms=waveforms, sampling_frequency=sampling_frequency
        )

    if "repolarization_slope" in feature_names:
        metrics["repolarization_slope"] = repolarization_slope(
            waveforms=waveforms,
            sampling_frequency=sampling_frequency,
        )

    if "recovery_slope" in feature_names:
        metrics["recovery_slope"] = recovery_slope(
            waveforms=waveforms,
            sampling_frequency=sampling_frequency,
            window=recovery_slope_window,
        )

    if "neg_peak_diff" in feature_names:
        metrics["neg_peak_diff"] = peak_time_diff(
            waveforms=waveforms, fs=sampling_frequency, sign="negative"
        )

    if "pos_peak_diff" in feature_names:
        metrics["pos_peak_diff"] = peak_time_diff(
            waveforms=waveforms, fs=sampling_frequency, sign="positive"
        )

    if "neg_peak_relative" in feature_names:
        metrics["neg_peak_relative"] = relative_amplitude(
            waveforms=waveforms, sign="negative"
        )

    if "pos_peak_relative" in feature_names:
        metrics["pos_peak_relative"] = relative_amplitude(
            waveforms=waveforms, sign="positive"
        )

    if "neg_image" in feature_names:
        metrics["neg_image"] = peak_image(waveforms=waveforms, sign="negative")

    if "pos_image" in feature_names:
        metrics["pos_image"] = peak_image(waveforms=waveforms, sign="positive")

    return metrics


def peak_to_valley(waveforms, sampling_frequency):
    """
    Time between trough and peak. If the peak precedes the trough,
    peak_to_valley is negative.

    Parameters
    ----------
    waveforms  : numpy.ndarray (num_waveforms x num_samples)
        waveforms to compute feature for
    sampling_frequency  : float
        rate at which the waveforms are sampled (Hz)

    Returns
    -------
    np.ndarray (num_waveforms)
        peak_to_valley in seconds

    """
    trough_idx, peak_idx = _get_trough_and_peak_idx(waveforms)
    ptv = (peak_idx - trough_idx) * (1 / sampling_frequency)
    ptv[ptv == 0] = np.nan
    return ptv


def peak_trough_ratio(waveforms):
    """
    Normalized ratio peak height and trough depth

    Assumes baseline is 0

    Parameters
    ----------
    waveforms  : numpy.ndarray (num_waveforms x num_samples)
        waveforms to compute feature for

    Returns
    -------

    np.ndarray (num_waveforms)
        Peak to trough ratio

    """
    trough_idx, peak_idx = _get_trough_and_peak_idx(waveforms)
    ptratio = np.empty(trough_idx.shape[0])
    ptratio[:] = np.nan
    for i in range(waveforms.shape[0]):
        if peak_idx[i] == 0 and trough_idx[i] == 0:
            continue
        ptratio[i] = np.abs(waveforms[i, peak_idx[i]] /
                            waveforms[i, trough_idx[i]])

    return ptratio


def halfwidth(waveforms, sampling_frequency, return_idx=False):
    """
    Width of waveform at its half of amplitude.
    If the peak precedes the trough, halfwidth is negative.

    Computes the width of the waveform peak at half it's height

    Parameters
    ----------
    waveforms  : numpy.ndarray (num_waveforms x num_samples)
        waveforms to compute features for
    sampling_frequency  : float
        rate at which the waveforms are sampled (Hz)
    return_idx : bool
        if true, also returns index of threshold crossing before and
        index of threshold crossing after peak

    Returns
    -------

    np.ndarray or (np.ndarray, np.ndarray, np.ndarray)
        Halfwidth of the waveforms or (Halfwidth of the waveforms,
        index_cross_pre_peak, index_cross_post_peak)

    """
    trough_idx, peak_idx = _get_trough_and_peak_idx(waveforms)
    hw = np.empty(waveforms.shape[0])
    hw[:] = np.nan
    cross_pre_pk = np.empty(waveforms.shape[0], dtype=int)
    cross_post_pk = np.empty(waveforms.shape[0], dtype=int)

    for i in range(waveforms.shape[0]):
        if peak_idx[i] >= trough_idx[i]:
            trough_val = waveforms[i, trough_idx[i]]
            threshold = (
                0.5 * trough_val
            )  # threshold is half of peak heigth (assuming baseline is 0)

            cpre_idx = np.where(waveforms[i, :trough_idx[i]] < threshold)[0]
            cpost_idx = np.where(waveforms[i, trough_idx[i]:] < threshold)[0]

            if len(cpre_idx) == 0 or len(cpost_idx) == 0:
                continue

            cross_pre_pk[i] = (
                cpre_idx[0] - 1
            )  # last occurence of waveform lower than thr, before peak
            cross_post_pk[i] = (
                cpost_idx[-1] + 1 + trough_idx[i]
            )  # first occurence of waveform lower than peak, after peak

            hw[i] = (cross_post_pk[i] - cross_pre_pk[i]) * (
                1 / sampling_frequency
            )  # + peak_idx[i]
        else:
            peak_val = waveforms[i, peak_idx[i]]
            threshold = (
                0.5 * peak_val
            )  # threshold is half of peak heigth (assuming baseline is 0)

            cpre_idx = np.where(waveforms[i, :peak_idx[i]] > threshold)[0]
            cpost_idx = np.where(waveforms[i, peak_idx[i]:] > threshold)[0]

            if len(cpre_idx) == 0 or len(cpost_idx) == 0:
                continue

            cross_pre_pk[i] = (
                cpre_idx[0] - 1
            )  # last occurence of waveform lower than thr, before peak
            cross_post_pk[i] = (
                cpost_idx[-1] + 1 + trough_idx[i]
            )  # first occurence of waveform lower than peak, after peak

            hw[i] = -(cross_post_pk[i] - cross_pre_pk[i]) * (
                1 / sampling_frequency
            )  # + peak_idx[i]

    if not return_idx:
        return hw
    else:
        return hw, cross_pre_pk, cross_post_pk


def repolarization_slope(waveforms, sampling_frequency, return_idx=False):
    """
    Return slope of repolarization period between trough and baseline

    After reaching its maxumum polarization, the neuron potential will
    recover. The repolarization slope is defined as the dV/dT of the action
    potential between trough and baseline.

    Optionally the function returns also the indices per waveform where the
    potential crosses baseline.

    Parameters
    ----------
    waveforms  : numpy.ndarray (num_waveforms x num_samples)
        waveforms to compute features for
    sampling_frequency  : float
        rate at which the waveforms are sampled (Hz)
    return_idx : bool
        if true, also returns index of threshold crossing before and
        index of threshold crossing after peak

    Returns
    -------

    np.ndarray or (np.ndarray, np.ndarray)
        Repolarization slope of the waveforms or (Repolarization slope of the
        waveforms, return to base index)
    """
    trough_idx, peak_idx = _get_trough_and_peak_idx(waveforms)

    rslope = np.empty(waveforms.shape[0])
    rslope[:] = np.nan
    return_to_base_idx = np.empty(waveforms.shape[0], dtype=np.int_)
    return_to_base_idx[:] = 0

    time = np.arange(0, waveforms.shape[1]) * (1 / sampling_frequency)  # in s
    for i in range(waveforms.shape[0]):
        if trough_idx[i] == 0:
            continue

        rtrn_idx = np.where(waveforms[i, trough_idx[i]:] >= 0)[0]
        if len(rtrn_idx) == 0:
            continue

        return_to_base_idx[i] = (
            rtrn_idx[0] + trough_idx[i]
        )  # first time after  trough, where waveform is at baseline

        if return_to_base_idx[i] - trough_idx[i] < 3:
            continue
        slope = _get_slope(
            time[trough_idx[i]:return_to_base_idx[i]],
            waveforms[i, trough_idx[i]:return_to_base_idx[i]]
        )
        rslope[i] = slope[0]

    if not return_idx:
        return rslope
    else:
        return rslope, return_to_base_idx


def recovery_slope(waveforms, sampling_frequency, window):
    """
    Return the recovery slope of input waveforms. After repolarization,
    the neuron hyperpolarizes until it peaks. The recovery slope is the
    slope of the action potential after the peak, returning to the baseline
    in dV/dT. The slope is computed within a user-defined window after
    the peak.

    Takes a numpy array of waveforms and returns an array with
    recovery slopes per waveform.

    Parameters
    ----------
    waveforms  : numpy.ndarray (num_waveforms x num_samples)
        waveforms to compute features for
    sampling_frequency  : float
        rate at which the waveforms are sampled (Hz)
    window : float
        length after peak wherein to compute recovery slope (ms)


    Returns
    -------
    np.ndarray
        Recovery slope of the waveforms
    """
    _, peak_idx = _get_trough_and_peak_idx(waveforms)
    rslope = np.empty(waveforms.shape[0])
    rslope[:] = np.nan

    time = np.arange(0, waveforms.shape[1]) * (1 / sampling_frequency)  # in s

    for i in range(waveforms.shape[0]):
        if peak_idx[i] in [0, waveforms.shape[1]]:
            continue
        max_idx = int(peak_idx[i] + ((window / 1000) * sampling_frequency))
        max_idx = np.min([max_idx, waveforms.shape[1]])

        if len(time[peak_idx[i]:max_idx]) < 3:
            continue
        slope = _get_slope(
            time[peak_idx[i]:max_idx], waveforms[i, peak_idx[i]:max_idx]
        )
        rslope[i] = slope[0]

    return rslope


def peak_image(waveforms, sign="negative"):
    """
    Normalized amplitude at the time of minimum or maximum peak.

    Parameters
    ----------
    waveforms  : numpy.ndarray (num_waveforms x num_samples)
        waveforms to compute features for
    sign : str
        "pos" | "neg"

    Returns
    -------
    np.ndarray
        Peak images for the waveforms

    """
    assert len(waveforms) > 1

    if sign == "negative":
        funarg = np.argmin
        fun = np.min
    else:
        funarg = np.argmax
        fun = np.max

    peak_channel, peak_time = np.unravel_index(
        funarg(waveforms), waveforms.shape
    )
    relative_peaks = waveforms[:, peak_time] / fun(waveforms[peak_channel])

    return relative_peaks


def relative_amplitude(waveforms, sign="negative"):
    """
    Normalized amplitude with respect to channel with largest amplitude.

    Parameters
    ----------
    waveforms  : numpy.ndarray (num_waveforms x num_samples)
        waveforms to compute features for
    fs : float
        Sampling rate in Hz
    sign : str
        "positive" | "negative"

    Returns
    -------
    np.ndarray
        Relative amplitudes for the waveforms

    """
    assert len(waveforms) > 1

    if sign == "negative":
        fun = np.min
    else:
        fun = np.max

    peak_amp = np.abs(fun(waveforms))
    relative_peaks = np.abs(fun(waveforms, 1)) / peak_amp

    return relative_peaks


def peak_time_diff(waveforms, fs, sign="negative"):
    """
    Peak time differences with respect to channel with largest amplitude.

    Parameters
    ----------
    waveforms  : numpy.ndarray (num_waveforms x num_samples)
        waveforms to compute features for
    fs : float
        Sampling rate in Hz
    sign : str
        "positive" | "negative"

    Returns
    -------
    np.ndarray
        Peak time differences for the waveforms

    """
    assert len(waveforms) > 1

    if sign == "negative":
        argfun = np.argmin
    else:
        argfun = np.argmax

    peak_chan = np.unravel_index(argfun(waveforms), waveforms.shape)[0]
    peak_time = argfun(waveforms[peak_chan])
    relative_peak_times = (argfun(waveforms, 1) - peak_time) / fs

    return relative_peak_times


def _get_slope(x, y):
    """
    Retrun the slope of x and y data, using scipy.signal.linregress
    """
    from scipy.stats import linregress

    slope = linregress(x, y)
    return slope


def _get_trough_and_peak_idx(waveform, after_max_trough=False):
    """
    Return the indices into the input waveforms of the detected troughs
    (minimum of waveform) and peaks (maximum of waveform, after trough).

    Assumes negative troughs and positive peaks

    Returns 0 if not detected
    """
    if after_max_trough:
        max_through_idx = np.unravel_index(
            np.argmin(waveform),
            waveform.shape)[1]
        trough_idx = (
            np.argmin(waveform[:, max_through_idx:], axis=1) + max_through_idx
        )
        peak_idx = (
            np.argmax(waveform[:, max_through_idx:], axis=1) + max_through_idx
        )
    else:
        trough_idx = np.argmin(waveform, axis=1)
        peak_idx = np.argmax(waveform, axis=1)

    return trough_idx, peak_idx


def _upsample_wf(waveforms, upsample):
    from scipy.signal import resample_poly

    ndim = len(waveforms.shape)
    waveforms_up = resample_poly(waveforms, up=upsample, down=1, axis=ndim - 1)

    return waveforms_up
