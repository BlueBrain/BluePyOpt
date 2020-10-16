"""Parameter classes"""

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

import logging

import bluepyopt
from bluepyopt.ephys.serializer import DictMixin
from . import parameterscalers

logger = logging.getLogger(__name__)

# TODO location and stimulus parameters should also be optimisable


class NrnParameter(bluepyopt.parameters.Parameter):

    """Abstract Parameter class for Neuron object parameters"""

    def __init__(
            self,
            name,
            value=None,
            frozen=False,
            bounds=None):
        """Contructor"""

        super(NrnParameter, self).__init__(
            name,
            value=value,
            frozen=frozen,
            bounds=bounds)

    def instantiate(self, sim=None, icell=None):
        """Instantiate the parameter in the simulator"""
        pass

    def destroy(self, sim=None):
        """Remove parameter from the simulator"""
        pass


class MetaParameter(NrnParameter):

    """Parameter class that controls attributes of other objects"""

    def __init__(
            self,
            name,
            obj=None,
            attr_name=None,
            value=None,
            frozen=False,
            bounds=None):
        """Constructor"""

        super(MetaParameter, self).__init__(
            name,
            value=value,
            frozen=frozen,
            bounds=bounds)

        self.obj = obj
        self.attr_name = attr_name
        setattr(self.obj, self.attr_name, value)

    @bluepyopt.parameters.Parameter.value.setter
    def value(self, _value):
        """Setter for value"""
        # Call setter of superclass
        super(MetaParameter, self.__class__).value.fset(self, _value)
        setattr(self.obj, self.attr_name, _value)

    def __str__(self):
        """String representation"""
        return '%s: %s.%s = %s' % (self.name,
                                   self.obj.name,
                                   self.attr_name,
                                   self.value)


class NrnMetaListEqualParameter(bluepyopt.parameters.MetaListEqualParameter):
    """Nrn version of MetaListEqualParameter, implements instantiate"""

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""

        for sub_parameter in self.sub_parameters:
            sub_parameter.instantiate(sim=sim, icell=icell)

        logger.debug('Set %s to %s', self.name, str(self.value))

    def destroy(self, sim=None):
        """Remove parameter from the simulator"""
        for sub_parameter in self.sub_parameters:
            sub_parameter.destroy(sim=sim)


class NrnGlobalParameter(NrnParameter, DictMixin):

    """Parameter set in the global namespace of neuron"""
    SERIALIZED_FIELDS = ('name', 'value', 'frozen', 'bounds', 'param_name',)

    def __init__(
            self,
            name,
            value=None,
            frozen=False,
            bounds=None,
            param_name=None):
        """Contructor

        Args:
            name (str): name of this object
            value (float): Value for the parameter, required if Frozen=True
            frozen (bool): Whether the parameter can be varied, or its values
            is permently set
            bounds (indexable): two elements;
                the lower and upper bounds (Optional)
            param_name (str): name used within NEURON
        """

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


class NrnSectionParameter(NrnParameter, DictMixin):

    """Parameter of a section"""
    SERIALIZED_FIELDS = ('name', 'value', 'frozen', 'bounds', 'param_name',
                         'value_scaler', 'locations', )

    def __init__(
            self,
            name,
            value=None,
            frozen=False,
            bounds=None,
            param_name=None,
            value_scaler=None,
            locations=None):
        """Contructor

        Args:
            name (str): name of the Parameter
            value (float): Value for the parameter, required if Frozen=True
            frozen (bool): Whether the parameter can be varied, or its values
            is permently set
            bounds (indexable): two elements; the lower and upper bounds
                (Optional)
            param_name (str): name used within NEURON
            value_scaler (float): value used to scale the parameter value
            locations (list of ephys.locations.Location): locations on which
                to instantiate the parameter
        """

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
        if self.value is None:
            raise Exception(
                'NrnSectionParameter: impossible to instantiate parameter "%s"'
                ' without value' %
                self.name)

        for location in self.locations:
            iseclist = location.instantiate(sim=sim, icell=icell)
            for section in iseclist:
                setattr(section, self.param_name,
                        self.value_scale_func(self.value, section, sim=sim))
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


class NrnPointProcessParameter(NrnParameter, DictMixin):

    """Parameter of a section"""
    SERIALIZED_FIELDS = ('name', 'value', 'frozen', 'bounds', 'param_name',
                         'value_scaler', 'locations', )

    def __init__(
            self,
            name,
            value=None,
            frozen=False,
            bounds=None,
            locations=None,
            param_name=None):
        """Constructor

        Args:
            name (str): name of the Parameter
            value (float): Value for the parameter, required if Frozen=True
            frozen (bool): Whether the parameter can be varied, or its values
            is permently set
            bounds (indexable): two elements; the lower and upper bounds
                (Optional)
            locations: an iterator of the point process locations you want to
                       set the parameters of
            param_name (str): name of parameter used within the point process
        """

        super(NrnPointProcessParameter, self).__init__(
            name,
            value=value,
            frozen=frozen,
            bounds=bounds)

        self.locations = locations
        self.param_name = param_name

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""
        if self.value is None:
            raise Exception(
                'NrnSectionParameter: impossible to instantiate parameter "%s"'
                ' without value' %
                self.name)

        for location in self.locations:
            for pprocess in location.instantiate(sim=sim, icell=icell):
                setattr(pprocess, self.param_name, self.value)
                logger.debug(
                    'Set %s to %s for point process',
                    self.param_name,
                    self.value)

    def __str__(self):
        """String representation"""
        return '%s: %s = %s' % (self.name,
                                self.param_name,
                                self.value if self.frozen else self.bounds)

# TODO change mech_suffix and mech_param to param_name, and maybe add
# NrnRangeMechParameter


class NrnRangeParameter(NrnParameter, DictMixin):

    """Parameter that has a range over a section"""
    SERIALIZED_FIELDS = ('name', 'value', 'frozen', 'bounds', 'param_name',
                         'value_scaler', 'locations', )

    def __init__(
            self,
            name,
            value=None,
            frozen=False,
            bounds=None,
            param_name=None,
            value_scaler=None,
            locations=None):
        """Contructor

        Args:
            name (str): name of the Parameter
            value (float): Value for the parameter, required if Frozen=True
            frozen (bool): Whether the parameter can be varied, or its values
            is permently set
            bounds (indexable): two elements; the lower and upper bounds
                (Optional)
            param_name (str): name used within NEURON
            value_scaler (float): value used to scale the parameter value
            locations (list of ephys.locations.Location): locations on which
                to instantiate the parameter
        """

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
        if self.value is None:
            raise Exception(
                'NrnRangeParameter: impossible to instantiate parameter "%s" '
                'without value' % self.name)

        for location in self.locations:
            for isection in location.instantiate(sim=sim, icell=icell):
                for seg in isection:
                    setattr(seg, '%s' % self.param_name,
                            self.value_scale_func(self.value, seg, sim=sim))
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
