'''create a hoc file from a set of BluePyOpt.ephys parameters'''

# pylint: disable=R0914

import os
import re

from collections import defaultdict, namedtuple, OrderedDict
from datetime import datetime
from glob import glob

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


_nrn2arb = dict( # TODO: add regions
    cm='membrane-capacitance',
    ena='ion-reversal-potential \"na\"',
    ek='ion-reversal-potential \"k\"',
    v_init='membrane-potential',
    celsius='temperature-kelvin',
    Ra='axial-resistivity'
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


def _make_arb_global_param(loc, param):
    return loc == 'all' and param.name in ['membrane-capacitance']


def _arb_defined_region(region, expr):
    return ('(region \"%s\")' % region, '(region-def \"%s\" %s)' % (region, expr))

def _arb_tagged_region(region, tag):
    return _arb_defined_region(region, '(tag %i)' % tag)


_nrn2arb_region = {
    'all': _arb_defined_region('all', '(all)'), # could use ('(all)', None) instead, then "all" undefined
    'somatic': _arb_tagged_region('soma', 1),
    'axonal': _arb_tagged_region('axon', 2),
    'basal': _arb_tagged_region('dend', 3),     # SWC convetion: dend == basal dendrite, apic == apical dendrite
    'apical': _arb_tagged_region('apic', 4),
    'myelinated': (None, None),                 # myelinated is unsupported in Arbor
}

# # Generated with NMODL in arbor/mechanisms
# import os, re, pprint

# nmodl_pattern = '^\s*%s\s+((?:\w+\,\s*)*?\w+)\s*?$'
# suffix_pattern = nmodl_pattern % 'SUFFIX'
# globals_pattern = nmodl_pattern % 'GLOBAL'
# ranges_pattern = nmodl_pattern % 'RANGE'

# def process_nmodl(fd):
#     # print(fd, flush=True)
#     nrn = re.search(r'NEURON\s+{([^}]+)}', fd, flags=re.MULTILINE).group(1)
#     suffix = re.search(suffix_pattern, nrn, flags=re.MULTILINE)
#     suffix = suffix if suffix is None else suffix.group(1)
#     globals = re.search(globals_pattern, nrn, flags=re.MULTILINE)
#     globals = globals if globals is None else re.findall(r'\w+', globals.group(1))
#     ranges = re.search(ranges_pattern, nrn, flags=re.MULTILINE)
#     ranges = ranges if ranges is None else re.findall(r'\w+', ranges.group(1))
#     return dict(globals=globals, ranges=ranges) # suffix skipped

# mechs = dict()
# for cat in ['allen', 'bbp', 'default']:
#     mechs[cat] = dict()
#     cat_dir = 'arbor/mechanisms/' + cat
#     for f in os.listdir(cat_dir):
#         with open(os.path.join(cat_dir,f)) as fd:
#             print(f"Processing {f}", flush=True)
#             mechs[cat][f[:-4]] = process_nmodl(fd.read())
# pprint.pprint(mechs)


_arb_mechs = dict(
    allen={
        'CaDynamics': {'globals': ['F'],
                       'ranges': ['decay', 'gamma', 'minCai', 'depth']},
        'Ca_HVA': {'globals': None, 'ranges': ['gbar']},
        'Ca_LVA': {'globals': None, 'ranges': ['gbar']},
        'Ih': {'globals': None, 'ranges': ['gbar']},
        'Im': {'globals': None, 'ranges': ['gbar', 'g', 'ik']},
        'Im_v2': {'globals': None, 'ranges': ['gbar', 'ik']},
        'K_P': {'globals': None, 'ranges': ['gbar', 'g', 'ik']},
        'K_T': {'globals': None, 'ranges': ['gbar']},
        'Kd': {'globals': None, 'ranges': ['gbar', 'ik']},
        'Kv2like': {'globals': None, 'ranges': ['gbar']},
        'Kv3_1': {'globals': None, 'ranges': ['gbar', 'ik']},
        'NaTa': {'globals': None, 'ranges': ['gbar', 'g', 'ina']},
        'NaTs': {'globals': None, 'ranges': ['gbar', 'g', 'ina']},
        'NaV': {'globals': None, 'ranges': ['gbar']},
        'Nap': {'globals': None, 'ranges': ['gbar', 'g', 'ina']},
        'SK': {'globals': None, 'ranges': ['gbar', 'ik']}},
    bbp={
        'CaDynamics_E2': {'globals': None,
                        'ranges': ['decay',
                                   'gamma',
                                   'minCai',
                                   'depth',
                                   'initCai']},
        'Ca_HVA': {'globals': None, 'ranges': ['gCa_HVAbar']},
        'Ca_LVAst': {'globals': None, 'ranges': ['gCa_LVAstbar']},
        'Ih': {'globals': None, 'ranges': ['gIhbar']},
        'Im': {'globals': None, 'ranges': ['gImbar']},
        'K_Pst': {'globals': None, 'ranges': ['gK_Pstbar']},
        'K_Tst': {'globals': None, 'ranges': ['gK_Tstbar']},
        'NaTa_t': {'globals': None, 'ranges': ['gNaTa_tbar']},
        'NaTs2_t': {'globals': None, 'ranges': ['gNaTs2_tbar']},
        'Nap_Et2': {'globals': None, 'ranges': ['gNap_Et2bar']},
        'SK_E2': {'globals': None, 'ranges': ['gSK_E2bar']},
        'SKv3_1': {'globals': None, 'ranges': ['gSKv3_1bar']}},
    default={
        'exp2syn': {'globals': None, 'ranges': ['tau1', 'tau2', 'e']},
        'expsyn': {'globals': None, 'ranges': ['tau', 'e']},
        'expsyn_stdp': {'globals': None,
                        'ranges': ['tau',
                                   'taupre',
                                   'taupost',
                                   'e',
                                   'Apost',
                                   'Apre',
                                   'max_weight']},
        'gj': {'globals': None, 'ranges': ['g']},
        'hh': {'globals': None,
               'ranges': ['gnabar', 'gkbar', 'gl', 'el', 'q10']},
        'kamt': {'globals': ['minf', 'mtau', 'hinf', 'htau'],
                 'ranges': ['gbar', 'q10']},
        'kdrmt': {'globals': ['minf', 'mtau'],
                  'ranges': ['gbar', 'q10', 'vhalfm']},
        'nax': {'globals': None, 'ranges': ['gbar', 'sh']},
        'nernst': {'globals': ['R', 'F'], 'ranges': ['coeff']},
        'pas': {'globals': ['e'], 'ranges': ['g']}}
)

def _find_mech_and_split_param_name(param, mechs):
    mech_suffix_matches = numpy.where([param.name.endswith("_" + mech)
                                       for mech in mechs])[0]
    if mech_suffix_matches.size == 0:
        return None, Location(name=_nrn2arb_name(param.name),
                              value=_nrn2arb_value(param)) # TODO: adapt for Range
    elif mech_suffix_matches.size == 1:
        mech = mechs[mech_suffix_matches[0]]
        name = param.name[:-(len(mech)+1)]
        return mech, Location(name=_nrn2arb_name(name),
                              value=_nrn2arb_value(param)) # TODO: adapt for Range
    else:
        raise RuntimeError("Parameter name %s matches multiple mechanisms %s " %
                            (param.name, repr(mechs[mech_suffix_matches])))


def _split_mech_from_non_mech_params_global(params, channels):
    mech_params =  [_find_mech_and_split_param_name(Location(name=name, value=value), channels['all'])
                    for name, value in params.items()]
    mechs = {mech: [] for mech, _ in mech_params}
    for mech, param in mech_params:
        mechs[mech].append(param)
    if len(mechs) > 0:
        assert list(mechs.keys()) == [None]
        return {param.name: param for param in mechs[None]} # FIXME: correct?
    else:
        return {}


def _split_mech_from_non_mech_params_local(params, channels):
    local_params = []
    global_params = {}
    for loc, params in params:
        mech_params = [_find_mech_and_split_param_name(param, channels[loc]) for param in params]
        mechs = {mech: [] for mech, _ in mech_params}
        for mech, param in mech_params:
            mechs[mech].append(param)
        for i, param in enumerate(mechs.get(None,[])):
            if _make_arb_global_param(loc, param):
                global_params[param.name] = param
                del mechs[None][i]
        local_params.append((loc, list(mechs.items())))
    return local_params, global_params


def _arb_mech_translate(mech_name, mech_params):
    arb_mech = None
    for cat in ['bbp', 'default', 'allen']: # in order of precedence
        if mech_name in _arb_mechs[cat]:
            arb_mech = _arb_mechs[cat][mech_name]
            break
    if arb_mech is None: # not Arbor built-in
        return (mech_name, mech_params)
    else:
        if arb_mech['globals'] is None:  # only Arbor range params
            for param in mech_params:
                assert param.name in arb_mech['ranges']
            return (mech_name, mech_params)
        else:
            for param in mech_params:
                assert param.name in arb_mech['globals'] or param.name in arb_mech['ranges']
            mech_params_dict = dict(mech_params)
            arb_mech_name = mech_name + '/' + ','.join([p + '=' + mech_params_dict[p] for p in arb_mech['globals']])
            arb_mech_params  = [mech_param for mech_param in mech_params if mech_param.name not in arb_mech['globals']]
            return (arb_mech_name, arb_mech_params)


def _nrn_to_arb_mechs_local(params):
    ret = []
    for loc, mechs in params:
        ret.append((loc, [_arb_mech_translate(*mech) for mech in mechs]))
    return ret


def _create_sim_desc(
        mechs,
        parameters,
        morphology=None,
        ignored_globals=(),
        replace_axon=None,
        template_name='CCell',
        template_filename='cell_template.jinja2',
        disable_banner=None,
        template_dir=None,
        custom_jinja_params=None,
        sim=None):
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
        sim (str): simulator to create description for (nrn or arb)
    '''

    assert sim in ['nrn', 'arb']

    if template_dir is None:
        template_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                'templates'))

    template_path = os.path.join(template_dir, template_filename)
    if sim == 'nrn':
        template_paths = [template_path]
    else:
        template_paths = glob(template_path)

    templates = dict()
    for template_path in  template_paths:
        with open(template_path) as template_file:
            template = template_file.read()
            name = os.path.basename(template_path)
            if name.endswith('.jinja2'):
                name = name[:-7]
            if name.endswith('_template'):
                name = name[:-9]
            if '_' in name:
                name = '.'.join(name.rsplit('_', 1))
            templates[name] = jinja2.Template(template)

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

    if sim == 'arb':
        custom_jinja_params['arb_decor'] = 'decor.acc'
        custom_jinja_params['arb_label_dict'] = 'label_dict.acc'
        global_params = _split_mech_from_non_mech_params_global(global_params, channels)
        section_params, additional_global_params = _split_mech_from_non_mech_params_local(section_params, channels)
        global_params.update(additional_global_params)
        # TODO: global translate?
        section_params =  _nrn_to_arb_mechs_local(section_params)
        # relabel locations
        custom_jinja_params['region_ref'] = { bpo_loc: arb_ref_def[0] for bpo_loc, arb_ref_def in _nrn2arb_region.items()}
        custom_jinja_params['region_def'] = { bpo_loc: arb_ref_def[1] for bpo_loc, arb_ref_def in _nrn2arb_region.items()}

        # TODO: range_params = _split_mech_from_non_mech_params_local(range_params, channels)
    
    ret = {template_name + (name if name.startswith('.') else "_" + name):
                template.render(template_name=template_name,
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
            for name, template in templates.items()}
    
    if sim == 'nrn':
        return list(ret.values())[0]
    else:
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
        template_filename (str): file name of the jinja2 template
        template_dir (str): dir name of the jinja2 template
        custom_jinja_params (dict): dict of additional jinja2 params in case
        of a custom template
    '''
    return _create_sim_desc(
        mechs,
        parameters,
        morphology,
        ignored_globals,
        replace_axon,
        template_name,
        template_filename,
        disable_banner,
        template_dir,
        custom_jinja_params,
        sim="nrn")


def create_acc( # FIXME: put into its own module (similarly tests)
        mechs,
        parameters,
        morphology=None,
        ignored_globals=(),
        replace_axon=None,
        template_name='CCell',
        template_filename='acc/*_template.jinja2',
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
        template_filename (str): file path of the cell.json , decor.acc and 
        label_dict.acc jinja2 templates (with wildcards expanded by glob)
        template_dir (str): dir name of the jinja2 template
        custom_jinja_params (dict): dict of additional jinja2 params in case
        of a custom template
    '''
    if morphology[-4:] not in ['.swc', '.asc']:
        raise RuntimeError("Morphology file %s not supported in Arbor "
                           " (only supported types are .swc and .asc)."
                           % morphology )
    
    return _create_sim_desc(
        mechs,
        parameters,
        morphology,
        ignored_globals,
        replace_axon,
        template_name,
        template_filename,
        disable_banner,
        template_dir,
        custom_jinja_params,
        sim="arb")
