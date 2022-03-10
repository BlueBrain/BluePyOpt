'''create a hoc file from a set of BluePyOpt.ephys parameters'''

# pylint: disable=R0914

import os
import re

from collections import defaultdict, namedtuple, OrderedDict
from datetime import datetime

import numpy
import jinja2
import bluepyopt
from . import mechanisms

from bluepyopt.ephys.parameters import (NrnGlobalParameter,
                                        NrnSectionParameter,
                                        NrnRangeParameter,
                                        MetaParameter)

from bluepyopt.ephys.parameterscalers import (NrnSegmentSomaDistanceScaler,
                                              NrnSegmentLinearScaler,
                                              FLOAT_FORMAT,
                                              format_float)

Location = namedtuple('Location', 'name, value')
MechLocation = namedtuple('MechLocation', 'name, mech, value')
Range = namedtuple('Range', 'location, param_name, value')
DEFAULT_LOCATION_ORDER = [
    'all',
    'apical',
    'axonal',
    'basal',
    'somatic',
    'myelinated']

# location -> mechanism_name
def _generate_channels_by_location(mechs, location_order):
    """Create a OrderedDictionary of all channel mechs for hoc template."""
    channels = OrderedDict((location, []) for location in location_order)
    for mech in mechs:
        name = mech.suffix
        for location in mech.locations:
            # TODO this is dangerous, implicitely assumes type of location
            channels[location.seclist_name].append(name)
    return channels


def _generate_reinitrng(mechs):
    """Create re_init_rng function"""

    reinitrng_hoc_blocks = ''

    for mech in mechs:
        reinitrng_hoc_blocks += mech.generate_reinitrng_hoc_block()

    reinitrng_content = mechanisms.NrnMODMechanism.hash_hoc_string

    reinitrng_content += mechanisms.NrnMODMechanism.reinitrng_hoc_string % {
        'reinitrng_hoc_blocks': reinitrng_hoc_blocks}

    return reinitrng_content

# "list" of parameters -> global_params, ordered_section_params, range_params, location_order (loc -> [(param_name_mechanism, value),...]) - needs post-processing
def _generate_parameters(parameters):
    """Create a list of parameters that need to be added to the hoc template"""
    param_locations = defaultdict(list)
    global_params = {}
    for param in parameters:
        if isinstance(param, NrnGlobalParameter):
            global_params[param.name] = param.value
        elif isinstance(param, MetaParameter):
            pass
        else:
            assert isinstance(
                param.locations, (tuple, list)), 'Must have locations list'
            for location in param.locations:
                param_locations[location.seclist_name].append(param)

    section_params = defaultdict(list)
    range_params = []

    location_order = DEFAULT_LOCATION_ORDER

    for loc in param_locations:
        if loc not in location_order:
            location_order.append(loc)

    for loc in location_order:
        if loc not in param_locations:
            continue
        for param in param_locations[loc]:
            if isinstance(param, NrnRangeParameter):
                if isinstance(
                        param.value_scaler,
                        NrnSegmentSomaDistanceScaler):
                    value = param.value_scaler.inst_distribution
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
                              for loc in location_order]

    return global_params, ordered_section_params, range_params, location_order


_nrn2arb = dict(
    cm='membrane-capacitance',
    ena='ion-reversal-potential-method \"na\"',
    ek='ion-reversal-potential-method \"k\"',
    v_init='membrane-potential',
    celsius='temperature-kelvin'
    # TODO: Ra=?
)


def _nrn2arb_name(name):
    return _nrn2arb.get(name, name)


_nrn2arb_convert = dict(
    celsius=lambda celsius: celsius + 273.15
)


def _nrn2arb_value(param):
    if param.name in _nrn2arb_convert:
        return _nrn2arb_convert[param.name](param.value)
    else:
        return param.value


def _find_mech_and_split_param_name(param, mechs):
    mech_suffix_matches = numpy.where([param.name.endswith("_" + mech)
                                       for mech in mechs])[0]
    if len(mech_suffix_matches) == 0:
        return Location(name=_nrn2arb_name(param.name),
                        value=_nrn2arb_value(param)) # TODO: adapt for Range
    elif len(mech_suffix_matches) == 1:
        mech = mechs[mech_suffix_matches[0]]
        name = param.name.rstrip("_" + mech).replace(mech, '')
        return MechLocation(name=_nrn2arb_name(name),
                            mech=mech, value=_nrn2arb_value(param)) # TODO: adapt for Range
    else:
        raise RuntimeError("Parameter name %s matches multiple mechanisms %s " %
                            (param.name, repr(mechs[mech_suffix_matches])))


def _split_mech_from_non_mech_params_global(params, channels):
    ret = [ _find_mech_and_split_param_name(Location(name=name, value=value), channels['all'])
            for name, value in params.items() ]
    return { param.name : param for param in ret }


def _split_mech_from_non_mech_params_local(params, channels):
    ret = []
    for loc, params in params:
        ret.append((loc, [_find_mech_and_split_param_name(param, channels[loc])
                          for param in params]))
    return ret


def create_hoc(
        mechs,
        parameters,
        morphology=None,
        ignored_globals=(),
        replace_axon=None,
        template_name='CCell',
        template_filename='cell_template.jinja2',
        disable_banner=None,
        template_dir=None,
        custom_jinja_params=None,):
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
        template (str): file name of the jinja2 template
        template_dir (str): dir name of the jinja2 template
        custom_jinja_params (dict): dict of additional jinja2 params in case
        of a custom template
    '''

    if template_dir is None:
        template_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                'templates'))

    template_path = os.path.join(template_dir, template_filename)
    with open(template_path) as template_file:
        template = template_file.read()
        template = jinja2.Template(template)

    global_params, section_params, range_params, location_order = \
        _generate_parameters(parameters)
    channels = _generate_channels_by_location(mechs, location_order)

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

    re_init_rng = _generate_reinitrng(mechs)

    if custom_jinja_params is None:
        custom_jinja_params = {}

    if template_filename == 'acc_template.jinja2':
        global_params = _split_mech_from_non_mech_params_global(global_params, channels)
        section_params = _split_mech_from_non_mech_params_local(section_params, channels)
        # TODO: range_params = _split_mech_from_non_mech_params_local(range_params, channels)

    return template.render(template_name=template_name,
                           banner=banner,
                           channels=channels,
                           morphology=morphology,
                           section_params=section_params,
                           range_params=range_params,
                           global_params=global_params,
                           re_init_rng=re_init_rng,
                           replace_axon=replace_axon,
                           ignored_global_params=ignored_global_params,
                           **custom_jinja_params)
