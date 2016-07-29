'''create a hoc file from a set of BluePyOpt.ephys parameters'''
import os
import re

from collections import defaultdict, namedtuple, OrderedDict

import jinja2
from bluepyopt.ephys.parameters import (NrnGlobalParameter,
                                        NrnSectionParameter,
                                        NrnRangeParameter,
                                        )
from bluepyopt.ephys.parameterscalers import (NrnSegmentSomaDistanceScaler,
                                              NrnSegmentLinearScaler,
                                              )

Location = namedtuple('Location', 'name, value')
Range = namedtuple('Range', 'location, param_name, value')
LOCATION_ORDER = ('all', 'apical', 'axonal', 'basal', 'somatic',
                  )


def _generate_channels_by_location(mechanisms):
    '''create a OrderedDictionary of all channel mechanisms for the hoc template'''
    channels = OrderedDict((location, []) for location in LOCATION_ORDER)
    for mech in mechanisms:
        name = mech.prefix
        for location in mech.locations:
            channels[location.seclist_name].append(name)
    return channels


def _generate_parameters(parameters):
    '''create a list of parameters that need to be added to the hoc template'''
    param_locations = defaultdict(list)
    for param in parameters:
        if isinstance(param, NrnGlobalParameter):
            continue
        assert isinstance(param.locations, (tuple, list)), 'Must have locations list'
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
                    value = re.sub('{distance}', '%g', value)
                    range_params.append(Range(loc, param.param_name, value))
                elif isinstance(param.value_scaler, NrnSegmentLinearScaler):
                    section_params[loc].append(
                        Location(param.param_name, param.value))
            elif isinstance(param, NrnSectionParameter):
                section_params[loc].append(
                    Location(param.param_name, param.value))

    ordered_section_params = [(loc, section_params[loc])
                              for loc in LOCATION_ORDER]

    return ordered_section_params, range_params


def create_hoc(mechanisms, parameters, morphology=None,
               template_name='CCell', template='cell_template.jinja2'):
    '''return a string containing the hoc template

    Args:
        mechanisms(): All the mechanisms for the hoc template
        parameters(): All the parameters in the hoc template
        template(str): name of the template to use 'cell_template.jinja2',
    '''
    templates_basepath = os.path.abspath(os.path.dirname(__file__))
    template = os.path.join(templates_basepath, 'templates', template)
    with open(template) as fd:
        template = fd.read()
        template = jinja2.Template(template)

    channels = _generate_channels_by_location(mechanisms)
    section_params, range_params = _generate_parameters(parameters)

    return template.render(template_name=template_name,
                           channels=channels,
                           morphology=morphology,
                           section_params=section_params,
                           range_params=range_params)
