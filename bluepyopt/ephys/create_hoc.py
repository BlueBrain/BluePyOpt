'''create a hoc file from a set of BluePyOpt.ephys parameters'''

# pylint: disable=R0914

import os
import re

from collections import defaultdict, namedtuple, OrderedDict
from datetime import datetime

import jinja2
import bluepyopt
from bluepyopt.ephys.locations import (NrnSeclistCompLocation,
                                       NrnSeclistLocation,
                                       NrnSectionCompLocation,
                                       NrnSomaDistanceCompLocation,
                                       NrnSecSomaDistanceCompLocation,
                                       NrnTrunkSomaDistanceCompLocation,
                                       ArbLocation)

from bluepyopt.ephys.mechanisms import (Mechanism,
                                        NrnMODMechanism,
                                        NrnMODPointProcessMechanism)

from bluepyopt.ephys.parameters import (NrnGlobalParameter,
                                        NrnSectionParameter,
                                        NrnRangeParameter,
                                        NrnPointProcessParameter,
                                        MetaParameter)

from bluepyopt.ephys.parameterscalers import (NrnSegmentSomaDistanceScaler,
                                              NrnSegmentLinearScaler,
                                              FLOAT_FORMAT,
                                              format_float)

PointExpr = namedtuple('PointExpr', 'name, point_loc, value')
RangeExpr = namedtuple('RangeExpr', 'location, name, value, value_scaler')

# Consider renaming Location as name already used in locations module
Location = namedtuple('Location', 'name, value')
Range = namedtuple('Range', 'location, param_name, value')

DEFAULT_LOCATION_ORDER = [
    'all',
    'apical',
    'axonal',
    'basal',
    'somatic',
    'myelinated']


def generate_channels_by_location(mechs, location_order):
    """Create a OrderedDictionary of all channel mechs for hoc template.

    Args:
        mechs (list of bluepyopt.ephys.mechanisms.Mechanism): mechanisms
        location_order (list of str): order of locations

    Returns: tuple of channels, point_channels and location order
    """
    loc_desc = _loc_desc
    return _generate_channels_by_location(mechs, location_order, loc_desc)


def _generate_channels_by_location(mechs, location_order, loc_desc):
    """Create a OrderedDictionary of all channel mechs for hoc template."""
    channels = OrderedDict((location, []) for location in location_order)
    point_channels = OrderedDict((location, []) for location in location_order)
    for mech in mechs:
        name = mech.suffix
        for location in mech.locations:
            if isinstance(mech, NrnMODPointProcessMechanism):
                point_channels[loc_desc(location, mech)].append(mech)
            else:
                channels[loc_desc(location, mech)].append(name)
    return channels, point_channels


def generate_reinitrng(mechs) -> str:
    """Create re_init_rng function"""

    for mech in mechs:
        if isinstance(mech, NrnMODPointProcessMechanism):
            raise NotImplementedError(
                'HOC generation for models with point process mechanisms'
                ' is not yet supported.')

    reinitrng_hoc_blocks = ''

    for mech in mechs:
        reinitrng_hoc_blocks += mech.generate_reinitrng_hoc_block()

    reinitrng_content = NrnMODMechanism.hash_hoc_string

    reinitrng_content += NrnMODMechanism.reinitrng_hoc_string % {
        'reinitrng_hoc_blocks': reinitrng_hoc_blocks}

    return reinitrng_content


def range_exprs_to_hoc(range_params):
    """Process raw range parameters to hoc strings"""

    ret = []
    for param in range_params:
        value = param.value_scaler.inst_distribution
        value = re.sub(r'math\.', '', value)
        value = re.sub(r'\&', '&&', value)
        value = re.sub('{distance}', FLOAT_FORMAT, value)
        value = re.sub('{value}', format_float(param.value), value)
        if hasattr(param.value_scaler, "step_begin"):
            value = re.sub(
                '{step_begin}',
                format_float(param.value_scaler.step_begin),
                value
            )
            value = re.sub(
                '{step_end}', format_float(param.value_scaler.step_end), value
            )
        ret.append(Range(param.location, param.name, value))
    return ret


def _loc_desc(location, param_or_mech):
    """Generate Neuron location description for HOC template"""

    if isinstance(param_or_mech, Mechanism):
        if isinstance(param_or_mech, NrnMODMechanism):
            if isinstance(location, NrnSeclistLocation):
                return location.seclist_name
            else:
                raise CreateHocException(
                    "%s is currently not supported for mechs." %
                    type(location).__name__)
        elif isinstance(param_or_mech, NrnMODPointProcessMechanism):
            raise CreateHocException("%s is currently not supported." %
                                     type(param_or_mech).__name__)
    elif not isinstance(location, (NrnSeclistCompLocation,
                                   NrnSectionCompLocation,
                                   NrnSomaDistanceCompLocation,
                                   NrnSecSomaDistanceCompLocation,
                                   NrnTrunkSomaDistanceCompLocation,
                                   ArbLocation)) and \
            not isinstance(param_or_mech, NrnPointProcessParameter):
        return location.seclist_name
    else:
        raise CreateHocException("%s is currently not supported." %
                                 type(param_or_mech).__name__)


def generate_parameters(parameters):
    """Create a list of parameters that need to be added to the hoc template

    Args:
        parameters (list of bluepyopt.Parameters): parameters in hoc template

    Returns: tuple of global, section, range, pprocess and location order
    """
    location_order = DEFAULT_LOCATION_ORDER
    loc_desc = _loc_desc
    return _generate_parameters(parameters, location_order, loc_desc)


def _generate_parameters(parameters, location_order, loc_desc):
    """Create a list of parameters that need to be added to the hoc template"""
    param_locations = defaultdict(list)
    global_params = {}
    for param in parameters:
        if isinstance(param, NrnGlobalParameter):
            global_params[param.param_name] = param.value
        elif isinstance(param, MetaParameter):
            pass
        else:
            assert isinstance(
                param.locations, (tuple, list)), 'Must have locations list'
            for location in param.locations:
                locs = loc_desc(location, param)
                if not isinstance(locs, list):
                    param_locations[locs].append(param)
                else:
                    for loc in locs:
                        param_locations[loc].append(param)

    section_params = defaultdict(list)
    pprocess_params = defaultdict(list)
    range_params = []

    for loc in param_locations:
        if loc not in location_order:
            location_order.append(loc)

    for loc in location_order:
        if loc not in param_locations:
            continue
        for param in param_locations[loc]:
            if not isinstance(param.param_dependencies, list) or \
                    len(param.param_dependencies) > 0:
                raise CreateHocException(  # also an ACC exception
                    'Exporting models with parameters that have'
                    ' param_dependencies is not yet supported.')
            if isinstance(param, NrnRangeParameter):
                if isinstance(
                        param.value_scaler,
                        NrnSegmentSomaDistanceScaler):
                    range_params.append(
                        RangeExpr(loc,
                                  param.param_name,
                                  param.value,
                                  param.value_scaler))
                elif isinstance(param.value_scaler, NrnSegmentLinearScaler):
                    value = param.value_scale_func(param.value)
                    section_params[loc].append(
                        Location(param.param_name, format_float(value)))
            elif isinstance(param, NrnSectionParameter):
                value = param.value_scale_func(param.value)
                section_params[loc].append(
                    Location(param.param_name, format_float(value)))
            elif isinstance(param, NrnPointProcessParameter):
                value = param.value
                pprocess_params[loc].append(
                    PointExpr(param.param_name, param.locations,
                              format_float(value)))

    ordered_section_params = [(loc, section_params[loc])
                              for loc in location_order]

    ordered_pprocess_params = [(loc, pprocess_params[loc])
                               for loc in location_order]

    return global_params, ordered_section_params, range_params, \
        ordered_pprocess_params, location_order


def _read_template(template_dir, template_filename):
    """Read Jinja2 hoc template to render"""
    if template_dir is None:
        template_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                'templates'))

    template_path = os.path.join(template_dir, template_filename)
    with open(template_path) as template_file:
        template = template_file.read()
        template = jinja2.Template(template)
    return template


def _get_template_params(
        mechs,
        parameters,
        ignored_globals,
        disable_banner,
        default_location_order,
        loc_desc):
    '''return parameters to render Jinja2 templates with simulator descriptions

    Args:
        mechs (): All the mechs for the hoc template
        parameters (): All the parameters in the hoc template
        ignored_globals (iterable str): HOC coded is added for each
        NrnGlobalParameter
        that exists, to test that it matches the values set in the parameters.
        This iterable contains parameter names that aren't checked
        default_location_order (): list of ordered simulator-specific locations
        to use by default
        loc_desc (): method that extracts simulator-specific location
        description from pair of locations and mechanisms/parameters
    '''

    global_params, section_params, range_params, \
        pprocess_params, location_order = \
        _generate_parameters(parameters, default_location_order, loc_desc)

    channels, point_channels = _generate_channels_by_location(
        mechs, location_order, loc_desc)

    ignored_global_params = {}
    for ignored_global in ignored_globals:
        if ignored_global in global_params:
            ignored_global_params[
                ignored_global] = global_params[ignored_global]
            del global_params[ignored_global]

    if not disable_banner:
        banner = 'Created by BluePyOpt(%s) at %s' % (
            bluepyopt.__version__, datetime.now())
    else:
        banner = None

    return dict(global_params=global_params,
                ignored_global_params=ignored_global_params,
                section_params=section_params,
                range_params=range_params,
                pprocess_params=pprocess_params,
                location_order=location_order,
                channels=channels,
                point_channels=point_channels,
                banner=banner)


def create_hoc(mechs,
               parameters,
               morphology=None,
               ignored_globals=(),
               replace_axon=None,
               template_name='CCell',
               template_filename='cell_template.jinja2',
               disable_banner=None,
               template_dir=None,
               custom_jinja_params=None):
    '''return a string containing the hoc template

    Args:
        mechs (): All the mechs for the hoc template
        parameters (): All the parameters in the hoc template
        morpholgy (str): Name of morphology
        ignored_globals (iterable str): HOC coded is added for each
        NrnGlobalParameter
        that exists, to test that it matches the values set in the parameters.
        This iterable contains parameter names that aren't checked
        replace_axon (str): String replacement for the 'replace_axon' command.
        Must include 'proc replace_axon(){ ... }
        template_filename (str): file name of the jinja2 template
        template_dir (str): dir name of the jinja2 template
        custom_jinja_params (dict): dict of additional jinja2 params in case
        of a custom template
    '''

    template = _read_template(template_dir, template_filename)

    template_params = _get_template_params(mechs,
                                           parameters,
                                           ignored_globals,
                                           disable_banner,
                                           DEFAULT_LOCATION_ORDER,
                                           _loc_desc)

    # delete empty dicts to avoid conflict with custom_jinja_params
    del template_params['pprocess_params']
    del template_params['point_channels']

    template_params['range_params'] = range_exprs_to_hoc(
        template_params['range_params']
    )
    re_init_rng = generate_reinitrng(mechs)

    if custom_jinja_params is None:
        custom_jinja_params = {}

    return template.render(template_name=template_name,
                           morphology=morphology,
                           replace_axon=replace_axon,
                           re_init_rng=re_init_rng,
                           **template_params,
                           **custom_jinja_params)


class CreateHocException(Exception):

    """All exceptions generated by create_hoc module"""

    def __init__(self, message):
        """Constructor"""

        super(CreateHocException, self).__init__(message)
