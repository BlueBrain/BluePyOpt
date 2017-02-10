"""Parameter scaler classes"""

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

# pylint: disable=W0511

from bluepyopt.ephys.base import BaseEPhys
from bluepyopt.ephys.serializer import DictMixin


FLOAT_FORMAT = '%.17g'


def format_float(value):
    """Return formatted float string"""
    return FLOAT_FORMAT % value


class ParameterScaler(BaseEPhys):

    """Parameter scalers"""
    pass

# TODO get rid of the 'segment' here


class NrnSegmentLinearScaler(ParameterScaler, DictMixin):

    """Linear scaler"""
    SERIALIZED_FIELDS = ('name', 'comment', 'multiplier', 'offset', )

    def __init__(
            self,
            name=None,
            multiplier=1.0,
            offset=0.0,
            comment=''):
        """Constructor

        Args:
            name (str): name of this object
            multiplier (float): slope of the linear scaler
            offset (float): intercept of the linear scaler
        """

        super(NrnSegmentLinearScaler, self).__init__(name, comment)
        self.multiplier = multiplier
        self.offset = offset

    def scale(self, value, segment=None, sim=None):  # pylint: disable=W0613
        """Scale a value based on a segment"""

        return self.multiplier * value + self.offset

    def __str__(self):
        """String representation"""

        return '%s * value + %s' % (self.multiplier, self.offset)


class NrnSegmentSomaDistanceScaler(ParameterScaler, DictMixin):

    """Scaler based on distance from soma"""
    SERIALIZED_FIELDS = ('name', 'comment', 'distribution', )

    def __init__(
            self,
            name=None,
            distribution=None,
            comment='',
            dist_param_names=None):
        """Constructor

        Args:
            name (str): name of this object
            distribution (str): distribution of parameter dependent on distance
                from soma. string can contain `distance` and/or `value` as
                placeholders for the distance to the soma and parameter value
                respectivily
            dist_params (list): list of names of parameters that parametrise the
                distribution. These names will become attributes of this object.
                The distribution string should contain these names, and they
                will be replaced by values of the corresponding attributes
        """

        super(NrnSegmentSomaDistanceScaler, self).__init__(name, comment)
        self.distribution = distribution

        self.dist_param_names = dist_param_names

        if self.dist_param_names is not None:
            for dist_param_name in self.dist_param_names:
                if dist_param_name not in self.distribution:
                    raise ValueError(
                        'NrnSegmentSomaDistanceScaler: "{%s}" '
                        'missing from distribution string "%s"' %
                        (dist_param_name, distribution))
                setattr(self, dist_param_name, None)

    def create_dist(self, value, distance):
        """Create the final dist string"""

        dist_dict = {}
        dist_dict['distance'] = format_float(distance)
        dist_dict['value'] = format_float(value)

        if self.dist_param_names is not None:
            for dist_param_name in self.dist_param_names:
                dist_param_value = getattr(self, dist_param_name)
                if dist_param_value is None:
                    raise ValueError('NrnSegmentSomaDistanceScaler: %s '
                                     'was uninitialised' % dist_param_name)
                dist_dict[dist_param_name] = dist_param_value

        return self.distribution.format(**dist_dict)

    def scale(self, value, segment, sim=None):
        """Scale a value based on a segment"""

        # TODO soma needs other addressing scheme

        soma = segment.sec.cell().soma[0]

        # Initialise origin
        sim.neuron.h.distance(0, 0.5, sec=soma)

        distance = sim.neuron.h.distance(1, segment.x, sec=segment.sec)

        # Find something to generalise this
        import math  # pylint:disable=W0611 #NOQA

        # This eval is unsafe (but is it ever dangerous ?)
        # pylint: disable=W0123
        return eval(self.create_dist(value, distance))

    def __str__(self):
        """String representation"""

        return self.distribution
