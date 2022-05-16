'''create JSON/ACC files for Arbor from a set of BluePyOpt.ephys parameters'''

# pylint: disable=R0914

import os

from collections import namedtuple
from glob import glob

import numpy
import jinja2

from .create_hoc import Location, Range, _get_template_params, format_float


# Define Neuron to Arbor variable conversions
ArbVar = namedtuple('ArbVar', 'name, conv')


def _make_var(name, conv=None):  # conv defaults to identity
    return ArbVar(name=name, conv=conv)


_nrn2arb_var = dict(
    cm=_make_var(name='membrane-capacitance',
                 conv=lambda cm: cm / 100.),  # NEURON: uF/cm^2, Arbor: F/m^2
    ena=_make_var(name='ion-reversal-potential \"na\"'),
    ek=_make_var(name='ion-reversal-potential \"k\"'),
    v_init=_make_var(name='membrane-potential'),
    celsius=_make_var(name='temperature-kelvin',
                      conv=lambda celsius: celsius + 273.15),
    Ra=_make_var(name='axial-resistivity')
)


def _nrn2arb_var_name(name):
    """Neuron to Arbor variable renaming."""
    return _nrn2arb_var[name].name if name in _nrn2arb_var else name


def _nrn2arb_var_value(param):
    """Neuron to Arbor variable value conversion."""
    if param.name in _nrn2arb_var and \
       _nrn2arb_var[param.name].conv is not None:
        return format_float(_nrn2arb_var[param.name].conv(float(param.value)))
    else:
        return param.value


def _arb_is_global_param(loc, param):
    """Returns if location-specific variable is a global one in Arbor."""
    return loc == 'all' and param.name in ['membrane-capacitance']


# Define BluePyOpt to Arbor region mapping
# (relabeling locations to SWC convention)
# Remarks:
#  - using SWC convetion: 'dend' for basal dendrite, 'apic' for apical dendrite
#  - myelinated is unsupported in Arbor
ArbRegion = namedtuple('ArbRegion', 'ref, defn')


def _make_region(region, expr=None):
    """Create Arbor region with region name and defining expression
    (name for decor, defined in label_dict) or region expression only
    (for decor, no defined label in label_dict)."""
    if expr is not None:
        return ArbRegion(ref='(region \"%s\")' % region,
                         defn='(region-def \"%s\" %s)' % (region, expr))
    else:
        return ArbRegion(ref=region, defn=expr)


def _make_tagged_region(region, tag):
    return _make_region(region, '(tag %i)' % tag)


_loc2arb_region = dict(
    # defining "all" region for convenience here, else use
    # all=_arb_defined_region('(all)') to omit "all" in label_dict
    all=_make_region('all', '(all)'),
    somatic=_make_tagged_region('soma', 1),
    axonal=_make_tagged_region('axon', 2),
    basal=_make_tagged_region('dend', 3),
    apical=_make_tagged_region('apic', 4),
    myelinated=_make_region(None),
)

# # Generated with NMODL in arbor/mechanisms
# import os, re, pprint

# nmodl_pattern = '^\s*%s\s+((?:\w+\,\s*)*?\w+)\s*?$'
# suffix_pattern = nmodl_pattern % 'SUFFIX'
# globals_pattern = nmodl_pattern % 'GLOBAL'
# ranges_pattern = nmodl_pattern % 'RANGE'

# def process_nmodl(nmodl_str):
#     nrn = re.search(r'NEURON\s+{([^}]+)}', nmodl_str,
#                     flags=re.MULTILINE).group(1)
#     suffix = re.search(suffix_pattern, nrn,
#                        flags=re.MULTILINE)
#     suffix = suffix if suffix is None else suffix.group(1)
#     globals = re.search(globals_pattern, nrn,
#                         flags=re.MULTILINE)
#     globals = globals if globals is None \
#               else re.findall(r'\w+', globals.group(1))
#     ranges = re.search(ranges_pattern, nrn,
#                        flags=re.MULTILINE)
#     ranges = ranges if ranges is None \
#              else re.findall(r'\w+', ranges.group(1))
#     return dict(globals=globals, ranges=ranges)  # suffix skipped

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
                          'ranges': ['decay', 'gamma', 'minCai',
                                     'depth', 'initCai']},
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
                        'ranges': ['tau', 'taupre', 'taupost', 'e',
                                   'Apost', 'Apre', 'max_weight']},
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


def _find_mech_and_convert_param_name(param, mechs):
    """Find a parameter's mechanism and convert name to Arbor convention"""
    mech_suffix_matches = numpy.where([param.name.endswith("_" + mech)
                                       for mech in mechs])[0]
    if mech_suffix_matches.size == 0:
        return None, Location(name=_nrn2arb_var_name(param.name),
                              value=_nrn2arb_var_value(param))  # TODO: Range
    elif mech_suffix_matches.size == 1:
        mech = mechs[mech_suffix_matches[0]]
        name = param.name[:-(len(mech) + 1)]
        return mech, Location(name=_nrn2arb_var_name(name),
                              value=_nrn2arb_var_value(param))  # TODO: Range
    else:
        raise RuntimeError("Parameter name %s matches multiple mechanisms %s "
                           % (param.name, repr(mechs[mech_suffix_matches])))


def _arb_convert_params_and_group_by_mech_global(params, channels):
    """Group global params by mechanism, rename them to Arbor convention"""
    mech_params = [_find_mech_and_convert_param_name(
                   Location(name=name, value=value), channels['all'])
                   for name, value in params.items()]
    mechs = {mech: [] for mech, _ in mech_params}
    for mech, param in mech_params:
        mechs[mech].append(param)
    if len(mechs) > 0:
        assert list(mechs.keys()) == [None]
        return {param.name: param for param in mechs[None]}
    else:
        return {}


def _arb_convert_params_and_group_by_mech_local(params, channels):
    """Group section params by mechanism, rename them to Arbor convention"""
    local_params = []
    global_params = {}
    for loc, params in params:
        mech_params = [_find_mech_and_convert_param_name(
                       param, channels[loc]) for param in params]
        mechs = {mech: [] for mech, _ in mech_params}
        for mech, param in mech_params:
            mechs[mech].append(param)
        for i, param in enumerate(mechs.get(None, [])):
            if _arb_is_global_param(loc, param):
                global_params[param.name] = param
                del mechs[None][i]
        local_params.append((loc, list(mechs.items())))
    return local_params, global_params


def _arb_nmodl_global_translate(mech_name, mech_params):
    """Integrate NMODL GLOBAL parameters of Arbor-built-in mechanisms
     into mechanism name"""
    arb_mech = None
    for cat in ['bbp', 'default', 'allen']:  # in order of precedence
        if mech_name in _arb_mechs[cat]:
            arb_mech = _arb_mechs[cat][mech_name]
            break
    if arb_mech is None:  # not Arbor built-in mech
        return (mech_name, mech_params)
    else:
        if arb_mech['globals'] is None:  # only Arbor range params
            for param in mech_params:
                assert param.name in arb_mech['ranges']
            return (mech_name, mech_params)
        else:
            for param in mech_params:
                assert param.name in arb_mech['globals'] or \
                       param.name in arb_mech['ranges']
            mech_params_dict = dict(mech_params)
            arb_mech_name = mech_name + '/' + ','.join(
                [p + '=' + mech_params_dict[p] for p in arb_mech['globals']])
            arb_mech_params = [mech_param for mech_param in mech_params
                               if mech_param.name not in arb_mech['globals']]
            return (arb_mech_name, arb_mech_params)


def _arb_nmodl_global_translate_local(params):
    ret = []
    for loc, mechs in params:
        ret.append((loc, [_arb_nmodl_global_translate(*mech)
                          for mech in mechs]))
    return ret


def _read_templates(template_dir, template_filename):
    """Expand Jinja2 template filepath with glob and
     return dict of target filename -> parsed template"""
    if template_dir is None:
        template_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                'templates'))

    template_paths = glob(os.path.join(template_dir,
                                       template_filename))

    templates = dict()
    for template_path in template_paths:
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
    return templates


def create_acc(mechs,
               parameters,
               morphology=None,
               ignored_globals=(),
               replace_axon=None,
               template_name='CCell',
               template_filename='acc/*_template.jinja2',
               disable_banner=None,
               template_dir=None,
               custom_jinja_params=None):
    '''return a dict with strings containing the rendered JSON/ACC templates

    Args:
        mechs (): All the mechs for the decor template
        parameters (): All the parameters in the decor/label-dict template
        morpholgy (str): Name of morphology
        ignored_globals (iterable str): Skipped NrnGlobalParameter in decor
        replace_axon (str): String replacement for the 'replace_axon' command.
        Only False is supported at the moment.
        template_filename (str): file path of the cell.json , decor.acc and
        label_dict.acc jinja2 templates (with wildcards expanded by glob)
        template_dir (str): dir name of the jinja2 templates
        custom_jinja_params (dict): dict of additional jinja2 params in case
        of a custom template
    '''

    if morphology[-4:] not in ['.swc', '.asc']:
        raise RuntimeError("Morphology file %s not supported in Arbor "
                           " (only supported types are .swc and .asc)."
                           % morphology)

    if replace_axon is True:
        raise RuntimeError("Axon replacement (replace_axon is True) is not "
                           "supported in Arbor.")

    templates = _read_templates(template_dir, template_filename)

    template_params = _get_template_params(mechs,
                                           parameters,
                                           ignored_globals,
                                           disable_banner)

    if custom_jinja_params is None:
        custom_jinja_params = {}

    filenames = {
        name: template_name + (name if name.startswith('.') else "_" + name)
        for name in templates.keys()}

    # postprocess template parameters for Arbor
    global_params = template_params['global_params']
    section_params = template_params['section_params']
    channels = template_params['channels']
    range_params = template_params['range_params']

    global_params = \
        _arb_convert_params_and_group_by_mech_global(global_params, channels)
    section_params, additional_global_params = \
        _arb_convert_params_and_group_by_mech_local(section_params, channels)
    global_params.update(additional_global_params)
    # no nmodl translate on global_params as no mechs
    section_params = _arb_nmodl_global_translate_local(section_params)
    # TODO: range_params = _arb_convert_params_and_group_by_mech_local(
    #                          range_params, channels)

    template_params['global_params'] = global_params
    template_params['section_params'] = section_params
    template_params['channels'] = channels
    template_params['range_params'] = range_params

    return {filenames[name]:
            template.render(template_name=template_name,
                            morphology=morphology,
                            filenames=filenames,
                            regions=_loc2arb_region,
                            **template_params,
                            **custom_jinja_params)
            for name, template in templates.items()}
