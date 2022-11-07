"""Protocol classes"""

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

# pylint: disable=W0511

import os
import collections
import tempfile

# TODO: maybe find a better name ? -> sweep ?
import logging
logger = logging.getLogger(__name__)

from . import locations
from . import simulators
from . import stimuli
from .responses import TimeVoltageResponse
from .acc import arbor
from . import create_acc


class Protocol(object):

    """Class representing a protocol (stimulus and recording)."""

    def __init__(self, name=None):
        """Constructor

        Args:
            name (str): name of the feature
        """

        self.name = name


class SequenceProtocol(Protocol):

    """A protocol consisting of a sequence of other protocols"""

    def __init__(self, name=None, protocols=None):
        """Constructor

        Args:
            name (str): name of this object
            protocols (list of Protocols): subprotocols this protocol
                consists of
        """
        super(SequenceProtocol, self).__init__(name)
        self.protocols = protocols

    def run(
            self,
            cell_model,
            param_values,
            sim=None,
            isolate=None,
            timeout=None):
        """Instantiate protocol"""

        responses = collections.OrderedDict({})

        for protocol in self.protocols:

            # Try/except added for backward compatibility
            try:
                response = protocol.run(
                    cell_model=cell_model,
                    param_values=param_values,
                    sim=sim,
                    isolate=isolate,
                    timeout=timeout)
            except TypeError as e:
                if "unexpected keyword" in str(e):
                    response = protocol.run(
                        cell_model=cell_model,
                        param_values=param_values,
                        sim=sim,
                        isolate=isolate)
                else:
                    raise

            key_intersect = set(
                response.keys()).intersection(set(responses.keys()))
            if len(key_intersect) != 0:
                raise Exception(
                    'SequenceProtocol: one of the protocols (%s) is trying to '
                    'add already existing keys to the response: %s' %
                    (protocol.name, key_intersect))

            responses.update(response)

        return responses

    def subprotocols(self):
        """Return subprotocols"""

        subprotocols = collections.OrderedDict({self.name: self})

        for protocol in self.protocols:
            subprotocols.update(protocol.subprotocols())

        return subprotocols

    def __str__(self):
        """String representation"""

        content = 'Sequence protocol %s:\n' % self.name

        content += '%d subprotocols:\n' % len(self.protocols)
        for protocol in self.protocols:
            content += '%s\n' % str(protocol)

        return content


class SweepProtocol(Protocol):

    """Sweep protocol"""

    def __init__(
            self,
            name=None,
            stimuli=None,
            recordings=None,
            cvode_active=None,
            deterministic=False):
        """Constructor

        Args:
            name (str): name of this object
            stimuli (list of Stimuli): Stimulus objects used in the protocol
            recordings (list of Recordings): Recording objects used in the
                protocol
            cvode_active (bool): whether to use variable time step
            deterministic (bool): whether to force all mechanism
                to be deterministic
        """

        super(SweepProtocol, self).__init__(name)
        self.stimuli = stimuli
        self.recordings = recordings
        self.cvode_active = cvode_active
        self.deterministic = deterministic

    @property
    def total_duration(self):
        """Total duration"""

        return max([stimulus.total_duration for stimulus in self.stimuli])

    def subprotocols(self):
        """Return subprotocols"""

        return collections.OrderedDict({self.name: self})

    def adjust_stochasticity(func):
        """Decorator method to adjust the stochasticity of the mechanisms"""
        def inner(self, cell_model, param_values, **kwargs):
            """Inner function"""
            previous_stoch_state = []
            if self.deterministic:
                for mech in cell_model.mechanisms:
                    previous_stoch_state.append(mech.deterministic)
                    mech.deterministic = True

            responses = func(self, cell_model, param_values, **kwargs)

            if self.deterministic:
                for i, mech in enumerate(cell_model.mechanisms):
                    mech.deterministic = previous_stoch_state[i]

            return responses

        return inner

    def _run_func(self, cell_model, param_values, sim=None):
        """Run protocols"""

        try:
            cell_model.freeze(param_values)
            cell_model.instantiate(sim=sim)

            self.instantiate(sim=sim, icell=cell_model.icell)

            try:
                sim.run(self.total_duration, cvode_active=self.cvode_active)
            except (RuntimeError, simulators.NrnSimulatorException):
                logger.debug(
                    'SweepProtocol: Running of parameter set {%s} generated '
                    'an exception, returning None in responses',
                    str(param_values))
                responses = {recording.name:
                             None for recording in self.recordings}
            else:
                responses = {
                    recording.name: recording.response
                    for recording in self.recordings}

            self.destroy(sim=sim)

            cell_model.destroy(sim=sim)

            cell_model.unfreeze(param_values.keys())

            return responses
        except BaseException as e:
            raise SweepProtocolException(
                'Failed to run Neuron Sweep Protocol') from e

    @adjust_stochasticity
    def run(
            self,
            cell_model,
            param_values,
            sim=None,
            isolate=None,
            timeout=None):
        """Instantiate protocol"""

        if isolate is None:
            isolate = True

        if isolate:
            def _reduce_method(meth):
                """Overwrite reduce"""
                return (getattr, (meth.__self__, meth.__func__.__name__))

            import copyreg
            import types
            copyreg.pickle(types.MethodType, _reduce_method)
            import pebble
            from concurrent.futures import TimeoutError

            if timeout is not None:
                if timeout < 0:
                    raise ValueError("timeout should be > 0")

            with pebble.ProcessPool(max_workers=1, max_tasks=1) as pool:
                tasks = pool.schedule(self._run_func, kwargs={
                    'cell_model': cell_model,
                    'param_values': param_values,
                    'sim': sim},
                    timeout=timeout)
                try:
                    responses = tasks.result()
                except TimeoutError:
                    logger.debug('SweepProtocol: task took longer than '
                                 'timeout, will return empty response '
                                 'for this recording')
                    responses = {recording.name:
                                 None for recording in self.recordings}
        else:
            responses = self._run_func(cell_model=cell_model,
                                       param_values=param_values,
                                       sim=sim)
        return responses

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""

        for stimulus in self.stimuli:
            stimulus.instantiate(sim=sim, icell=icell)

        for recording in self.recordings:
            try:
                recording.instantiate(sim=sim, icell=icell)
            except locations.EPhysLocInstantiateException:
                logger.debug(
                    'SweepProtocol: Instantiating recording generated '
                    'location exception, will return empty response for '
                    'this recording')

    def destroy(self, sim=None):
        """Destroy protocol"""

        for stimulus in self.stimuli:
            stimulus.destroy(sim=sim)

        for recording in self.recordings:
            recording.destroy(sim=sim)

    def __str__(self):
        """String representation"""

        content = '%s:\n' % self.name

        content += '  stimuli:\n'
        for stimulus in self.stimuli:
            content += '    %s\n' % str(stimulus)

        content += '  recordings:\n'
        for recording in self.recordings:
            content += '    %s\n' % str(recording)

        return content


class StepProtocol(SweepProtocol):

    """Protocol consisting of step and holding current"""

    def __init__(
            self,
            name=None,
            step_stimulus=None,
            holding_stimulus=None,
            recordings=None,
            cvode_active=None,
            deterministic=False):
        """Constructor

        Args:
            name (str): name of this object
            step_stimulus (list of Stimuli): Stimulus objects used in protocol
            recordings (list of Recordings): Recording objects used in the
                protocol
            cvode_active (bool): whether to use variable time step
            deterministic (bool): whether to force all mechanism
                to be deterministic
        """

        super(StepProtocol, self).__init__(
            name,
            stimuli=[
                step_stimulus,
                holding_stimulus]
            if holding_stimulus is not None else [step_stimulus],
            recordings=recordings,
            cvode_active=cvode_active)

        self.step_stimulus = step_stimulus
        self.holding_stimulus = holding_stimulus

    @property
    def step_delay(self):
        """Time stimulus starts"""
        return self.step_stimulus.step_delay

    @property
    def step_duration(self):
        """Time stimulus starts"""
        return self.step_stimulus.step_duration


class ArbSweepProtocol(Protocol):

    """Arbor Sweep protocol"""

    def __init__(
            self,
            name=None,
            stimuli=None,
            recordings=None,
            use_labels=False):
        """Constructor

        Args:
            name (str): name of this object
            stimuli (list of Stimuli): Stimulus objects used in the protocol
            recordings (list of Recordings): Recording objects used in the
                protocol
            use_labels (bool): Add stimuli/recording locations to label dict
        """

        super(ArbSweepProtocol, self).__init__(name)
        self.stimuli = stimuli
        self.recordings = recordings
        self.use_labels = use_labels

    @property
    def total_duration(self):
        """Total duration"""

        return max([stimulus.total_duration for stimulus in self.stimuli])

    def subprotocols(self):
        """Return subprotocols"""

        return collections.OrderedDict({self.name: self})

    def _run_func(self, cell_json, param_values, sim=None):
        """Run protocols"""

        try:
            # Loading cell constituents from ACC
            cell_json, morph, decor, labels = \
                create_acc.read_acc(cell_json)

            # Locations of stimuli and recordings can be instantiated
            # as labels (useful for visualization in Arbor GUI)
            if self.use_labels:
                labels = self.instantiate_locations(labels)

            # Adding stimuli to decor (could also be written/loaded from ACC)
            decor = self.instantiate_iclamp_stimuli(
                decor,
                use_labels=self.use_labels)

            arb_cell_model = sim.instantiate(morph, decor, labels)

            # Adding synaptic stimuli to cell model (no representation in ACC)
            arb_cell_model = self.instantiate_synaptic_stimuli(
                arb_cell_model,
                use_labels=self.use_labels)

            # Adding recordings to cell model (no representation in ACC)
            arb_cell_model = self.instantiate_recordings(
                arb_cell_model,
                use_labels=self.use_labels)

            try:
                sim.run(arb_cell_model, tstop=self.total_duration)
            except (RuntimeError, simulators.ArbSimulatorException):
                logger.debug(
                    'ArbSweepProtocol: Running of parameter set {%s} '
                    'generated an exception, returning None in responses',
                    str(param_values))
                responses = {recording.name:
                             None for recording in self.recordings}
            else:
                if len(self.recordings) != len(arb_cell_model.traces):
                    raise ValueError('Number of Arbor voltage traces '
                                     '(%d) != number of recordings (%d)' %
                                     (len(self.recordings),
                                      len(arb_cell_model.traces)))
                responses = {
                    recording.name: TimeVoltageResponse(
                        recording.name, trace.time, trace.value)
                    for recording, trace in zip(self.recordings,
                                                arb_cell_model.traces)}

            return responses
        except BaseException as e:
            raise ArbSweepProtocolException(
                'Failed to run Arbor Sweep Protocol') from e

    def run(
            self,
            cell_model,
            param_values,
            sim=None,
            isolate=None,
            timeout=None):
        """Instantiate protocol"""

        # Export cell model to mixed JSON/ACC-format
        with tempfile.TemporaryDirectory() as acc_dir:
            cell_model.write_acc(acc_dir, param_values,
                                 ext_catalogues=sim.ext_catalogues)

            cell_json = os.path.join(acc_dir, cell_model.name + '.json')

            # protocols are directly instantiated on Arbor cell
            # (serialization would require representation for probes, events)

            if isolate is None:
                isolate = True

            if isolate:
                def _reduce_method(meth):
                    """Overwrite reduce"""
                    return (getattr, (meth.__self__, meth.__func__.__name__))

                import copyreg
                import types
                copyreg.pickle(types.MethodType, _reduce_method)
                import pebble
                from concurrent.futures import TimeoutError

                if timeout is not None:
                    if timeout < 0:
                        raise ValueError("timeout should be > 0")

                with pebble.ProcessPool(max_workers=1, max_tasks=1) as pool:
                    tasks = pool.schedule(self._run_func, kwargs={
                        'cell_json': cell_json,
                        'param_values': param_values,
                        'sim': sim},
                        timeout=timeout)
                    try:
                        responses = tasks.result()
                    except TimeoutError:
                        logger.debug('SweepProtocol: task took longer than '
                                     'timeout, will return empty response '
                                     'for this recording')
                        responses = {recording.name:
                                     None for recording in self.recordings}
            else:
                responses = self._run_func(cell_json=cell_json,
                                           param_values=param_values,
                                           sim=sim)
        return responses

    def instantiate_locations(self, label_dict):
        """Instantiate protocol (stimuli/recordings) locations on label_dict"""

        stim_rec_labels = []

        for stim in self.stimuli:
            if hasattr(stim, 'location'):
                arb_loc = stim.location.acc_label()
            else:
                arb_loc = [label for loc in stim.locations
                           for label in loc.acc_label()]
            for loc in (arb_loc if isinstance(arb_loc, list)
                        else [arb_loc]):
                stim_rec_labels.append((loc.name, loc.loc, stim))

        for rec in self.recordings:
            arb_loc = rec.location.acc_label()
            if isinstance(arb_loc, list) and len(arb_loc) != 1:
                raise ValueError('ArbSweepProtocol: ACC label %s' % arb_loc +
                                 ' of recording with length != 1.')
            stim_rec_labels.append((arb_loc.name, arb_loc.loc, rec))

        stim_rec_label_dict = dict()

        for label_name, label_loc, stim_rec in stim_rec_labels:
            if label_name in label_dict and \
                    label_loc != label_dict[label_name]:
                raise ValueError(
                    'Label %s already exists in' % label_name +
                    ' label_dict with different value: '
                    ' %s != %s.' % (label_dict[label_name], label_loc) +
                    ' Choose different location name for %s.' % stim_rec)
            elif label_name in stim_rec_label_dict and \
                    label_loc != stim_rec_label_dict[label_name]:
                raise ValueError(
                    'Label %s defined multiple times' % label_name +
                    '  with different values: '
                    ' %s != %s.' % (stim_rec_label_dict[label_name],
                                    label_loc) +
                    ' Choose different location name for %s.' % stim_rec)
            elif label_name not in label_dict and \
                    label_name not in stim_rec_label_dict:
                stim_rec_label_dict[label_name] = label_loc

        label_dict.append(arbor.label_dict(stim_rec_label_dict))

        return label_dict

    def instantiate_iclamp_stimuli(self, decor, use_labels=False):
        """Instantiate iclamp stimuli"""

        for i, stim in enumerate(self.stimuli):
            if not isinstance(stim, stimuli.SynapticStimulus):
                if hasattr(stim, 'envelope'):
                    arb_iclamp = arbor.iclamp(stim.envelope())
                else:
                    raise ValueError('Stimulus must provide envelope method '
                                     ' or be of type NrnNetStimStimulus to be'
                                     ' supported in Arbor.')

                arb_loc = stim.location.acc_label()
                for loc in (arb_loc if isinstance(arb_loc, list)
                            else [arb_loc]):
                    decor.place(loc.ref if use_labels else loc.loc,
                                arb_iclamp,
                                '%s.iclamp.%d.%s' % (self.name, i, loc.name))

        return decor

    def instantiate_synaptic_stimuli(self, cell_model, use_labels=False):
        """Instantiate synaptic stimuli"""

        for i, stim in enumerate(self.stimuli):
            if isinstance(stim, stimuli.SynapticStimulus):
                for acc_events in stim.acc_events():
                    cell_model.event_generator(acc_events)

        return cell_model

    def instantiate_recordings(self, cell_model, use_labels=False):
        """Instantiate recordings"""

        # Attach voltage probe sampling at 10 kHz (every 0.1 ms)
        for i, rec in enumerate(self.recordings):
            # alternatively arbor.cable_probe_membrane_voltage
            arb_loc = rec.location.acc_label()
            if isinstance(arb_loc, list) and len(arb_loc) != 1:
                raise ValueError('ArbSweepProtocol: ACC label %s' % arb_loc +
                                 ' of recording with length != 1.')

            if hasattr(cell_model, 'cable_cell'):
                rec_locations = cell_model.cable_cell.locations(arb_loc.loc)
                if len(rec_locations) != 1:
                    raise ValueError(
                        'Recording %s\'s' % rec.name +
                        ' location "%s"' % arb_loc.loc +
                        ' is non-unique in Arbor: %s.' % rec_locations)

            cell_model.probe('voltage',
                             arb_loc.ref if use_labels else arb_loc.loc,
                             frequency=10)  # could be a parameter

        return cell_model

    def __str__(self):
        """String representation"""

        content = '%s:\n' % self.name

        content += '  stimuli:\n'
        for stimulus in self.stimuli:
            content += '    %s\n' % str(stimulus)

        content += '  recordings:\n'
        for recording in self.recordings:
            content += '    %s\n' % str(recording)

        return content


class SweepProtocolException(Exception):

    """All exceptions generated by SweepProtocol"""

    def __init__(self, message):
        """Constructor"""

        super(SweepProtocolException, self).__init__(message)


class ArbSweepProtocolException(Exception):

    """All exceptions generated by ArbSweepProtocol"""

    def __init__(self, message):
        """Constructor"""

        super(ArbSweepProtocolException, self).__init__(message)
