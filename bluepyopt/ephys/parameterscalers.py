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

from .importer import neuron


class ParameterScaler(object):

    """Parameter scalers"""

    def __init__(self, name):
        """Constructor"""

        self.name = name

# TODO get rid of the 'segment' here


class NrnSegmentLinearScaler(ParameterScaler):

    """eFEL feature"""

    def __init__(
            self,
            name=None,
            multiplier=1.0,
            offset=0.0):
        """Constructor"""

        super(NrnSegmentLinearScaler, self).__init__(name)
        self.multiplier = multiplier
        self.offset = offset

    def scale(self, value, _):
        """Scale a value based on a segment"""

        return self.multiplier * value + self.offset

    def __str__(self):
        """String representation"""

        return '%s * value + %s' % (self.multiplier, self.offset)


class NrnSegmentSomaDistanceScaler(ParameterScaler):

    """eFEL feature"""

    def __init__(
            self,
            name=None,
            distribution=None):
        """Constructor"""

        super(NrnSegmentSomaDistanceScaler, self).__init__(name)
        self.distribution = distribution

    def scale(self, value, segment):
        """Scale a value based on a segment"""

        # TODO soma needs other addressing scheme

        soma = segment.sec.cell().soma[0]

        # Initialise origin
        neuron.h.distance(0, 0.5, sec=soma)

        distance = neuron.h.distance(1, segment.x, sec=segment.sec)

        # Find something to generalise this
        import math  # pylint:disable=W0611 #NOQA

        # This eval is unsafe (but is it ever dangerous ?)
        # pylint: disable=W0123

        return eval(self.distribution.format(distance=distance, value=value))

    def __str__(self):
        """String representation"""

        return self.distribution
