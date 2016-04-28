"""Parameter classes"""

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

from . import parameterscalers

logger = logging.getLogger(__name__)

# TODO location and stimulus parameters should also be optimisable


class Parameter(object):

    """Base parameter class"""

    def __init__(self, name, value=None, frozen=False, bounds=None):
        """Constructor"""

        if frozen and value is None:
            raise Exception('Must provide a value for frozen parameters')

        self.name = name
        self.prefix = None
        self.bounds = bounds
        self._value = value
        self.check_bounds()
        self.frozen = frozen

    @property
    def lower_bound(self):
        """Lower bound"""
        if self.bounds is not None:
            return self.bounds[0]
        else:
            return None

    @property
    def upper_bound(self):
        """Lower bound"""
        if self.bounds is not None:
            return self.bounds[1]
        else:
            return None

    @property
    def value(self):
        """Parameter value"""
        return self._value

    def freeze(self, value):
        """Freeze parameter to certain value"""
        self.value = value
        self.frozen = True

    def unfreeze(self, value=None):
        """Unfreeze parameter, if desired, set it to a certain value"""
        self._value = value
        self.frozen = False

    @value.setter
    def value(self, value):
        """Set parameter value"""
        if self.frozen:
            raise Exception(
                'Parameter: parameter %s is frozen, unable to change value' %
                self.name)
        else:
            self._value = value
            self.check_bounds()

    def check_bounds(self):
        """Check if parameter is within bounds"""
        if self.bounds and self._value is not None:
            if not self.lower_bound <= self._value <= self.upper_bound:
                raise Exception(
                    'Parameter %s has value %s outside of bounds [%s, %s]' %
                    (self.name, self._value, str(self.lower_bound),
                     str(self.upper_bound)))

    def destroy(self):
        """Destroy parameter instantation"""
        pass

    def raise_if_no_value(self):
        """Raise exception if Value is None"""
        if self._value is None:
            raise Exception('Parameter currently does not have a value')


class NrnGlobalParameter(Parameter):

    """Parameter set in the global namespace of neuron"""

    def __init__(
            self,
            name,
            value=None,
            frozen=False,
            bounds=None,
            param_name=None):
        """Contructor"""

        super(NrnGlobalParameter, self).__init__(
            name,
            value=value,
            frozen=frozen,
            bounds=bounds)

        self.param_name = param_name

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""

        setattr(sim.neuron.h, self.param_name, self.value)

        logger.debug('Set %s to %s', self.param_name, str(self.value))

    def __str__(self):
        """String representation"""
        return '%s: %s = %s' % (self.name,
                                self.param_name,
                                self.value if self.frozen else self.bounds)


class NrnSectionParameter(Parameter):

    """Parameter of a section"""

    def __init__(
            self,
            name,
            value=None,
            frozen=False,
            bounds=None,
            param_name=None,
            value_scaler=None,
            locations=None):
        """Contructor"""

        super(NrnSectionParameter, self).__init__(
            name,
            value=value,
            frozen=frozen,
            bounds=bounds)

        self.locations = locations
        self.param_name = param_name
        # TODO value_scaler has to be made more general
        self.value_scaler = value_scaler
        # TODO add a default value for a scaler that is picklable
        if self.value_scaler is None:
            self.value_scaler = parameterscalers.NrnSegmentLinearScaler()
        self.value_scale_func = self.value_scaler.scale

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""
        self.raise_if_no_value()

        for location in self.locations:
            iseclist = location.instantiate(sim=sim, icell=icell)
            for section in iseclist:
                setattr(section, self.param_name,
                        self.value_scale_func(self.value, section))
            logger.debug(
                'Set %s in %s to %s',
                self.param_name,
                location,
                self.value)

    def __str__(self):
        """String representation"""
        return '%s: %s %s = %s' % (self.name,
                                   [str(location)
                                    for location in self.locations],
                                   self.param_name,
                                   self.value if self.frozen else self.bounds)

# TODO change mech_prefix and mech_param to param_name, and maybe add
# NrnRangeMechParameter


class NrnRangeParameter(Parameter):

    """Parameter that has a range over a section"""

    def __init__(
            self,
            name,
            value=None,
            frozen=False,
            bounds=None,
            param_name=None,
            value_scaler=None,
            locations=None):
        """Contructor"""

        super(NrnRangeParameter, self).__init__(
            name,
            value=value,
            frozen=frozen,
            bounds=bounds)

        self.locations = locations
        self.param_name = param_name
        # TODO value_scaler has to be made more general
        self.value_scaler = value_scaler
        if self.value_scaler is None:
            self.value_scaler = parameterscalers.NrnSegmentLinearScaler()
        self.value_scale_func = self.value_scaler.scale

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""
        self.raise_if_no_value()

        for location in self.locations:
            for isection in location.instantiate(sim=sim, icell=icell):
                for seg in isection:
                    setattr(seg, '%s' % self.param_name,
                            self.value_scale_func(self.value, seg))
        logger.debug(
            'Set %s in %s to %s with scaler %s', self.param_name,
            [str(location)
             for location in self.locations],
            self.value,
            self.value_scaler)

    def __str__(self):
        """String representation"""
        return '%s: %s %s = %s' % (self.name,
                                   [str(location)
                                    for location in self.locations],
                                   self.param_name,
                                   self.value if self.frozen else self.bounds)
