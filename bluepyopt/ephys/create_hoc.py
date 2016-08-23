'''create a hoc file from a set of BluePyOpt.ephys parameters'''
import os
import re

from collections import defaultdict, namedtuple, OrderedDict

import jinja2
from bluepyopt.ephys.parameters import (NrnGlobalParameter,
                                        NrnSectionParameter,
                                        NrnRangeParameter)

from bluepyopt.ephys.parameterscalers import (NrnSegmentSomaDistanceScaler,
                                              NrnSegmentLinearScaler,
                                              FLOAT_FORMAT,
                                              format_float)

Location = namedtuple('Location', 'name, value')
Range = namedtuple('Range', 'location, param_name, value')
LOCATION_ORDER = ('all', 'apical', 'axonal', 'basal', 'somatic', 'myelinated')


def _generate_channels_by_location(mechanisms):
    """Create a OrderedDictionary of all channel mechanisms for hoc template."""
    channels = OrderedDict((location, []) for location in LOCATION_ORDER)
    for mech in mechanisms:
        name = mech.prefix
        for location in mech.locations:
            channels[location.seclist_name].append(name)
    return channels


def _generate_parameters(parameters):
    """Create a list of parameters that need to be added to the hoc template."""
    param_locations = defaultdict(list)
    global_params = {}
    for param in parameters:
        if isinstance(param, NrnGlobalParameter):
            global_params[param.name] = param.value
        else:
            assert isinstance(
                param.locations, (tuple, list)), 'Must have locations list'
            for location in param.locations:
                param_locations[location.seclist_name].append(param)

    section_params = defaultdict(list)
    range_params = []
    for loc in LOCATION_ORDER:
        if loc not in param_locations:
            continue
        for param in param_locations[loc]:
            if isinstance(param, NrnRangeParameter):
                if isinstance(param.value_scaler, NrnSegmentSomaDistanceScaler):
                    value = param.value_scaler.distribution
                    value = re.sub(r'math\.', '', value)
                    value = re.sub('{distance}', FLOAT_FORMAT, value)
                    value = re.sub('{value}', format_float(param.value), value)
                    range_params.append(Range(loc, param.param_name, value))
                elif isinstance(param.value_scaler, NrnSegmentLinearScaler):
                    value = param.value_scale_func(param.value)
                    section_params[loc].append(
                        Location(param.param_name, format_float(value)))
            elif isinstance(param, NrnSectionParameter):
                value = param.value_scale_func(param.value)
                section_params[loc].append(
                    Location(param.param_name, format_float(value)))

    ordered_section_params = [(loc, section_params[loc])
                              for loc in LOCATION_ORDER]

    return global_params, ordered_section_params, range_params


def create_hoc(mechanisms, parameters, morphology=None, ignored_globals=(),
               template_name='CCell', template='cell_template.jinja2'):
    '''return a string containing the hoc template

    Args:
        mechanisms(): All the mechanisms for the hoc template
        parameters(): All the parameters in the hoc template
        morpholgy(str path): Path to morphology
        ignored_globals(iterable str): HOC coded is added for each
        NrnGlobalParameter that exists, to test that it matches the values
        set in the parameters.  This iterable contains parameter names that
        aren't checked
        template(str): name of the template to use 'cell_template.jinja2',
    '''
    templates_basepath = os.path.abspath(os.path.dirname(__file__))
    template = os.path.join(templates_basepath, 'templates', template)
    with open(template) as fd:
        template = fd.read()
        template = jinja2.Template(template)

    channels = _generate_channels_by_location(mechanisms)
    global_params, section_params, range_params = \
        _generate_parameters(parameters)

    ignored_global_params = {}
    for ignored_global in ignored_globals:
        if ignored_global in global_params:
            ignored_global_params[
                ignored_global] = global_params[ignored_global]
            del global_params[ignored_global]

    return template.render(template_name=template_name,
                           channels=channels,
                           morphology=morphology,
                           section_params=section_params,
                           range_params=range_params,
                           global_params=global_params,
                           ignored_global_params=ignored_global_params)
