"""Parameter scaler classes"""

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

import string

from bluepyopt.ephys.base import BaseEPhys
from bluepyopt.ephys.parameterscalers.acc_iexpr import generate_acc_scale_iexpr
from bluepyopt.ephys.serializer import DictMixin
from bluepyopt.ephys.morphologies import ArbFileMorphology

FLOAT_FORMAT = '%.17g'


def format_float(value):
    """Return formatted float string"""
    return FLOAT_FORMAT % value


class MissingFormatDict(dict):

    """Extend dict for string formatting with missing values"""

    def __missing__(self, key):  # pylint: disable=R0201
        """Return string with format key for missing keys"""
        return '{' + key + '}'


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

    def scale(self, values, segment=None, sim=None):  # pylint: disable=W0613
        """Scale a value based on a segment"""
        if isinstance(values, dict):
            value = values["value"]
        else:
            value = values
        return self.multiplier * value + self.offset

    def __str__(self):
        """String representation"""

        return '%s * value + %s' % (self.multiplier, self.offset)


class NrnSegmentSectionDistanceScaler(ParameterScaler, DictMixin):

    """Scaler based on distance from soma"""
    SERIALIZED_FIELDS = ('name', 'comment', 'distribution',
                         "distribution", "dist_param_names",
                         "ref_sec", "ref_location",)

    def __init__(
            self,
            name=None,
            distribution=None,
            comment='',
            dist_param_names=None,
            ref_section='soma[0]',
            ref_location=0,):
        """Constructor

        Args:
            name (str): name of this object
            distribution (str): distribution of parameter dependent on distance
                from soma. string can contain `distance` and/or `value` as
                placeholders for the distance to the soma and parameter value
                respectivily
            dist_param_names (list): list of names of parameters that
                parametrise the distribution. These names will become
                attributes of this object.
                The distribution string should contain these names, and they
                will be replaced by values of the corresponding attributes
            ref_section (str): string with name of reference section to
                compute distance (e.g. "soma[0]", "dend[2]")
            ref_location (float): location along the soma used as origin
                from which to compute the distances. Expressed as a fraction
                (between 0.0 and 1.0).
        """

        super(NrnSegmentSectionDistanceScaler, self).__init__(name, comment)
        self.distribution = distribution

        self.dist_param_names = dist_param_names
        self.ref_location = ref_location
        self.ref_section = ref_section

        if not (0.0 <= self.ref_location <= 1.0):
            raise ValueError("ref_location must be between 0 and 1.")

        if self.dist_param_names is not None:
            for dist_param_name in self.dist_param_names:
                if dist_param_name not in self.distribution:
                    raise ValueError(
                        'NrnSegmentSectionDistanceScaler: "{%s}" '
                        'missing from distribution string "%s"' %
                        (dist_param_name, distribution))
                setattr(self, dist_param_name, None)

    @property
    def inst_distribution(self):
        """The instantiated distribution"""

        dist_dict = MissingFormatDict()

        if self.dist_param_names is not None:
            for dist_param_name in self.dist_param_names:
                dist_param_value = getattr(self, dist_param_name)
                if dist_param_value is None:
                    raise ValueError("NrnSegmentSomaDistanceScaler: %s "
                                     "was uninitialised" % dist_param_name)
                dist_dict[dist_param_name] = dist_param_value

        # Use this special formatting to bypass missing keys
        return string.Formatter().vformat(self.distribution, (), dist_dict)

    def scale_dict(self, values, distance):
        """Create scale dictionary"""
        scale_dict = {}
        if isinstance(values, dict):
            for k, v in values.items():
                scale_dict[k] = format_float(v)
        else:
            scale_dict["value"] = format_float(values)
        scale_dict["distance"] = format_float(distance)

        return scale_dict

    def eval_dist(self, values, distance):
        """Create the final dist string"""
        scale_dict = self.scale_dict(values, distance)

        return self.inst_distribution.format(**scale_dict)

    def scale(self, values, segment, sim=None):
        """Scale a value based on a segment"""

        # find section
        target_sec = None
        for sec in segment.sec.wholetree():
            if "." in sec.name():  # deal with templates
                sec_name = sec.name().split(".")[1]
            else:
                sec_name = sec.name()
            if self.ref_section in sec_name:
                target_sec = sec
                break

        if target_sec is None:
            raise Exception(f"Could not find section {self.ref_section} "
                            f"in section list")

        # Initialise origin
        sim.neuron.h.distance(0, self.ref_location, sec=target_sec)

        distance = sim.neuron.h.distance(1, segment.x, sec=segment.sec)

        # Find something to generalise this
        import math  # pylint:disable=W0611 #NOQA

        # This eval is unsafe (but is it ever dangerous ?)
        # pylint: disable=W0123
        return eval(self.eval_dist(values, distance))

    def acc_scale_iexpr(self, value, constant_formatter=format_float):
        """Generate Arbor scale iexpr for a given value"""
        raise ValueError(
            "Parameter scaling based on general Neuron segment/section"
            " distances not supported in Arbor.")

    def __str__(self):
        """String representation"""

        return self.distribution


class NrnSegmentSomaDistanceScaler(NrnSegmentSectionDistanceScaler,
                                   ParameterScaler, DictMixin):

    """Scaler based on distance from soma"""
    SERIALIZED_FIELDS = ('name', 'comment', 'distribution', )

    def __init__(
            self,
            name=None,
            distribution=None,
            comment='',
            dist_param_names=None,
            soma_ref_location=0.5):
        """Constructor
        Args:
            name (str): name of this object
            distribution (str): distribution of parameter dependent on distance
                from soma. string can contain `distance` and/or `value` as
                placeholders for the distance to the soma and parameter value
                respectivily
            dist_param_names (list): list of names of parameters that
                parametrise the distribution. These names will become
                attributes of this object.
                The distribution string should contain these names, and they
                will be replaced by values of the corresponding attributes
            soma_ref_location (float): location along the soma used as origin
                from which to compute the distances. Expressed as a fraction
                (between 0.0 and 1.0).
        """

        super(NrnSegmentSomaDistanceScaler, self).__init__(
            name, distribution, comment, dist_param_names,
            ref_section='soma[0]', ref_location=soma_ref_location)

    def acc_scale_iexpr(self, value, constant_formatter=format_float):
        """Generate Arbor scale iexpr for a given value"""

        iexpr = self.inst_distribution

        variables = dict(
            value=value,
            distance='(distance %s)' %  # could be a ctor param if required
            ArbFileMorphology.region_labels['somatic'].ref
        )
        return generate_acc_scale_iexpr(iexpr, variables, constant_formatter)


class NrnSegmentSomaDistanceStepScaler(NrnSegmentSomaDistanceScaler,
                                       ParameterScaler, DictMixin):

    """Scaler based on distance from soma with a step function"""
    SERIALIZED_FIELDS = ('name', 'comment', 'distribution', )

    def __init__(
            self,
            name=None,
            distribution=None,
            comment='',
            dist_param_names=None,
            soma_ref_location=0.5,
            step_begin=None,
            step_end=None):
        """Constructor
        Args:
            name (str): name of this object
            distribution (str): distribution of parameter dependent on distance
                from soma. string can contain `distance` and/or `value` as
                placeholders for the distance to the soma and parameter value
                respectively. It can also contain step_begin and step_end.
            dist_param_names (list): list of names of parameters that
                parametrise the distribution. These names will become
                attributes of this object.
                The distribution string should contain these names, and they
                will be replaced by values of the corresponding attributes
            soma_ref_location (float): location along the soma used as origin
                from which to compute the distances. Expressed as a fraction
                (between 0.0 and 1.0).
            step_begin (float): distance at which the step begins
            step_end (float): distance at which the step ends
        """

        super(NrnSegmentSomaDistanceStepScaler, self).__init__(
            name, distribution, comment, dist_param_names,
            soma_ref_location=soma_ref_location)
        self.step_begin = step_begin
        self.step_end = step_end

    def scale_dict(self, values, distance):
        scale_dict = super().scale_dict(values, distance)
        scale_dict["step_begin"] = self.step_begin
        scale_dict["step_end"] = self.step_end

        return scale_dict
