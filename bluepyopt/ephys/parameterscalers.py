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


class ParameterScaler(object):

    """Parameter scalers"""

    def __init__(self, name):
        """Constructor

        Args:
            name (str): name of this object
        """

        self.name = name

# TODO get rid of the 'segment' here


class NrnSegmentLinearScaler(ParameterScaler):

    """Linear scaler"""

    def __init__(
            self,
            name=None,
            multiplier=1.0,
            offset=0.0):
        """Constructor

        Args:
            name (str): name of this object
            multiplier (float): slope of the linear scaler
            offset (float): intercept of the linear scaler
        """

        super(NrnSegmentLinearScaler, self).__init__(name)
        self.multiplier = multiplier
        self.offset = offset

    def scale(self, value, _, sim=None):
        """Scale a value based on a segment"""

        return self.multiplier * value + self.offset

    def __str__(self):
        """String representation"""

        return '%s * value + %s' % (self.multiplier, self.offset)


class NrnSegmentSomaDistanceScaler(ParameterScaler):

    """Scaler based on distance from soma"""

    def __init__(
            self,
            name=None,
            distribution=None):
        """Constructor

        Args:
            name (str): name of this object
            distribution (str): distribution of parameter dependent on distance
                from soma. string should contain `distance` and `value` as
                placeholders for the distance to the soma and parameter value
                respectivily
        """

        super(NrnSegmentSomaDistanceScaler, self).__init__(name)
        self.distribution = distribution

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

        return eval(self.distribution.format(distance=distance, value=value))

    def __str__(self):
        """String representation"""

        return self.distribution
