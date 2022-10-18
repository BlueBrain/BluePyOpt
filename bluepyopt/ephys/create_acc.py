'''create JSON/ACC files for Arbor from a set of BluePyOpt.ephys parameters'''

# pylint: disable=R0914

import os
import io
import logging
import pathlib
from collections import namedtuple, OrderedDict
import re
from glob import glob

import jinja2
import json
import shutil

try:
    import arbor
except ImportError as e:
    class arbor:
        def __getattribute__(self, _):
            raise ImportError("Loading an ACC/JSON-exported cell model into an"
                              " Arbor morphology and cable cell components"
                              " requires missing dependency arbor."
                              " To install BluePyOpt with arbor,"
                              " run 'pip install bluepyopt[arbor]'.")

logger = logging.getLogger(__name__)

from .create_hoc import Location, RangeExpr, PointExpr, \
    _get_template_params, format_float
from .morphologies import ArbFileMorphology

# Define Neuron to Arbor variable conversions
ArbVar = namedtuple('ArbVar', 'name, conv')  # turn into a class


# Inhomogeneous expression for soma-distance-scaled parameter in Arbor
RangeIExpr = namedtuple('RangeIExpr', 'name, value, scale')


def _make_var(name, conv=None):  # conv defaults to identity
    return ArbVar(name=name, conv=conv)


_nrn2arb_var = dict(
    v_init=_make_var(name='membrane-potential'),
    celsius=_make_var(name='temperature-kelvin',
                      conv=lambda celsius: celsius + 273.15),
    Ra=_make_var(name='axial-resistivity'),
    cm=_make_var(name='membrane-capacitance',
                 conv=lambda cm: cm / 100.),  # NEURON: uF/cm^2, Arbor: F/m^2
    **{species + loc[0]:
       _make_var(name='ion-%sternal-concentration \"%s\"' % (loc, species))
       for species in ['na', 'k', 'ca'] for loc in ['in', 'ex']},
    **{'e' + species:
       _make_var(name='ion-reversal-potential \"%s\"' % species)
       for species in ['na', 'k', 'ca']}
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


def _nrn2arb_param(param, name):
    if isinstance(param, Location):
        return Location(name=_nrn2arb_var_name(name),
                        value=_nrn2arb_var_value(param))
    elif isinstance(param, RangeExpr):
        return RangeExpr(location=param.location,
                         name=_nrn2arb_var_name(name),
                         value=_nrn2arb_var_value(param),
                         value_scaler=param.value_scaler)
    elif isinstance(param, PointExpr):
        return PointExpr(name=_nrn2arb_var_name(name),
                         point_loc=param.point_loc,
                         value=_nrn2arb_var_value(param))
    else:
        raise ValueError('Invalid parameter expression type.')


def _nrn2arb_mech_name(name):
    """Neuron to Arbor mechanism name conversion."""
    if name in ['Exp2Syn', 'ExpSyn']:
        return name.lower()
    else:
        return name


def _arb_is_global_property(loc, param):
    """Returns if region-specific variable is a global property in Arbor."""
    return loc == ArbFileMorphology.region_labels['all'] and (
        param.name in ['membrane-potential',
                       'temperature-kelvin',
                       'axial-resistivity',
                       'membrane-capacitance'] or
        param.name.split(' ')[0] in ['ion-internal-concentration',
                                     'ion-external-concentration',
                                     'ion-reversal-potential'])


def _arb_pop_global_properties(loc, mechs):
    global_properties = []
    local_properties = []
    if None in mechs:
        for param in mechs[None]:
            if _arb_is_global_property(loc, param):
                global_properties.append(param)
            else:
                local_properties.append(param)
        mechs[None] = local_properties
    return [(None, global_properties)]  # list of (mech, params) tuples


def _arb_eval_point_proc_locs(pprocess_mechs):
    """Evaluate point process locations"""

    result = {loc: dict() for loc in pprocess_mechs}

    for loc, mechs in pprocess_mechs.items():
        for mech, point_exprs in mechs.items():
            result[loc][mech.name] = dict(
                mech=mech.suffix,
                params=[Location(point_expr.name, point_expr.value)
                        for point_expr in point_exprs],
                point_locs=[loc.acc_label()
                            for loc in mech.locations])

    return result


def _arb_load_catalogue_desc(cat_dir):
    """Load mechanism catalogue description from NMODL files"""
    # used to generate arbor_mechanisms.json on NMODL from arbor/mechanisms

    nmodl_pattern = '^\s*%s\s+((?:\w+\,\s*)*?\w+)\s*?$'  # NOQA
    suffix_pattern = nmodl_pattern % 'SUFFIX'
    globals_pattern = nmodl_pattern % 'GLOBAL'
    ranges_pattern = nmodl_pattern % 'RANGE'

    def process_nmodl(nmodl_str):
        """Inspect NMODL for global and range parameters"""
        try:
            nrn = re.search(r'NEURON\s+{([^}]+)}', nmodl_str,
                            flags=re.MULTILINE).group(1)
            suffix = re.search(suffix_pattern, nrn,
                               flags=re.MULTILINE)
            suffix = suffix if suffix is None else suffix.group(1)
            globals = re.search(globals_pattern, nrn,
                                flags=re.MULTILINE)
            globals = globals if globals is None \
                else re.findall(r'\w+', globals.group(1))
            ranges = re.search(ranges_pattern, nrn,
                               flags=re.MULTILINE)
            ranges = ranges if ranges is None \
                else re.findall(r'\w+', ranges.group(1))
        except Exception as e:
            raise ValueError('create_acc: NMODL-inspection for'
                             ' %s failed.' % nmodl_file) from e

        return dict(globals=globals, ranges=ranges)  # suffix skipped

    mechs = dict()
    for nmodl_file in glob(str(cat_dir / '*.mod')):
        with open(os.path.join(cat_dir, nmodl_file)) as f:
            mechs[pathlib.Path(nmodl_file).stem] = process_nmodl(f.read())

    return mechs


def _arb_load_mech_catalogues(ext_catalogues):
    """Load Arbor's built-in mechanism catalogues"""

    arb_cats = OrderedDict()

    if ext_catalogues is not None:
        for cat, cat_nmodl in ext_catalogues.items():
            arb_cats[cat] = _arb_load_catalogue_desc(
                pathlib.Path(cat_nmodl).resolve())

    builtin_catalogues = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            'static/arbor_mechanisms.json'))
    with open(builtin_catalogues) as f:
        builtin_arb_cats = json.load(f)

    for cat in ['BBP', 'default', 'allen']:
        if cat not in arb_cats:
            arb_cats[cat] = builtin_arb_cats[cat]

    return arb_cats


def _find_mech_and_convert_param_name(param, mechs):
    """Find a parameter's mechanism and convert name to Arbor convention"""
    if not isinstance(param, PointExpr):
        mech_matches = [i for i, mech in enumerate(mechs)
                        if param.name.endswith("_" + mech)]
    else:
        param_pprocesses = [loc.pprocess_mech for loc in param.point_loc]
        mech_matches = [i for i, mech in enumerate(mechs)
                        if mech in param_pprocesses]

    if len(mech_matches) == 0:
        return None, _nrn2arb_param(param, name=param.name)

    elif len(mech_matches) == 1:
        mech = mechs[mech_matches[0]]
        if not isinstance(param, PointExpr):
            name = param.name[:-(len(mech) + 1)]
        else:
            name = param.name
        return mech, _nrn2arb_param(param, name=name)

    else:
        raise RuntimeError("Parameter name %s matches multiple mechanisms %s "
                           % (param.name,
                              [repr(mechs[i]) for i in mech_matches]))


def _arb_convert_params_and_group_by_mech(params, channels):
    mech_params = [_find_mech_and_convert_param_name(
                   param, channels) for param in params]
    mechs = {mech: [] for mech, _ in mech_params}
    for mech in channels:
        if mech not in mechs:
            mechs[mech] = []
    for mech, param in mech_params:
        mechs[mech].append(param)
    return mechs


def _arb_convert_params_and_group_by_mech_global(params):
    """Group global params by mechanism, rename them to Arbor convention"""
    return _arb_convert_params_and_group_by_mech(
        [Location(name=name, value=value) for name, value in params.items()],
        []  # no default mechanisms
    )


def _arb_convert_params_and_group_by_mech_local(params, channels):
    """Group section params by mechanism, rename them to Arbor convention"""
    local_mechs = dict()
    global_properties = dict()
    for loc, params in params:
        mechs = _arb_convert_params_and_group_by_mech(params, channels[loc])

        # move Arbor global properties to global_params
        for mech, props in _arb_pop_global_properties(loc, mechs):
            global_properties[mech] = global_properties.get(mech, []) + props
        local_mechs[loc] = mechs
    return local_mechs, global_properties


def _arb_append_scaled_mechs(mechs, scaled_mechs):
    """Append scaled mechanism parameters to constant ones"""
    for mech, scaled_params in scaled_mechs.items():
        if mech is None and len(scaled_params) > 0:
            raise ValueError('Non-mechanism parameters cannot have'
                             ' inhomogeneous expressions in Arbor',
                             scaled_params)
        mechs[mech] = mechs.get(mech, []) + \
            [RangeIExpr(
                name=p.name,
                value=format_float(p.value),
                scale=p.value_scaler.acc_scale_iexpr(p.value))
                for p in scaled_params]


def _arb_nmodl_global_translate_mech(mech_name, mech_params, arb_cats):
    """Integrate NMODL GLOBAL parameters of Arbor-built-in mechanisms
     into mechanism name and add catalogue prefix"""

    arb_mech = None
    arb_mech_name = _nrn2arb_mech_name(mech_name)

    for cat in arb_cats:  # in order of precedence
        if arb_mech_name in arb_cats[cat]:
            arb_mech = arb_cats[cat][arb_mech_name]
            mech_name = cat + '::' + arb_mech_name
            break

    if arb_mech is None:  # not Arbor built-in mech, no qualifier added
        if mech_name is not None:
            logger.warn('create_acc: Could not find Arbor mech for %s (%s).'
                        % (mech_name, mech_params))
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
            mech_name_suffix = []
            remaining_mech_params = []
            for mech_param in mech_params:
                if mech_param.name in arb_mech['globals']:
                    mech_name_suffix.append(mech_param.name + '=' +
                                            mech_param.value)
                    if isinstance(mech_param, RangeIExpr):
                        remaining_mech_params.append(
                            RangeIExpr(name=mech_param.name,
                                       value=None,
                                       scale=mech_param.scale))
                else:
                    remaining_mech_params.append(mech_param)
            if len(mech_name_suffix) > 0:
                mech_name += '/' + ','.join(mech_name_suffix)
            return (mech_name, remaining_mech_params)


def _arb_nmodl_global_translate_density(mechs, arb_cats):
    """Translate all density mechanisms in a region"""
    return dict([_arb_nmodl_global_translate_mech(mech, params, arb_cats)
                 for mech, params in mechs.items()])


def _arb_nmodl_global_translate_points(mechs, arb_cats):
    """Translate all point mechanisms in a region"""
    result = dict()

    for synapse_name, mech_desc in mechs.items():
        mech, params = _arb_nmodl_global_translate_mech(
            mech_desc['mech'], mech_desc['params'], arb_cats)
        result[synapse_name] = dict(mech=mech,
                                    params=params,
                                    point_locs=mech_desc['point_locs'])

    return result


def _arb_project_scaled_mechs(mechs):
    """Returns all mechanisms with scaled parameters in Arbor"""
    scaled_mechs = dict()
    for mech, params in mechs.items():
        range_iexprs = [p for p in params if isinstance(p, RangeIExpr)]
        if len(range_iexprs) > 0:
            scaled_mechs[mech] = range_iexprs
    return scaled_mechs


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


def _arb_loc_desc(location, param_or_mech):
    """Generate Arbor location description for label dict and decor"""
    return location.acc_label()


def create_acc(mechs,
               parameters,
               morphology=None,
               morphology_dir=None,
               ext_catalogues=None,
               ignored_globals=(),
               replace_axon=None,
               create_mod_morph=False,
               template_name='CCell',
               template_filename='acc/*_template.jinja2',
               disable_banner=None,
               template_dir=None,
               custom_jinja_params=None):
    '''return a dict with strings containing the rendered JSON/ACC templates

    Args:
        mechs (): All the mechs for the decor template
        parameters (): All the parameters in the decor/label-dict template
        morphology (str): Name of morphology
        morphology_dir (str): Directory of morphology
        ext_catalogues (): Name to path mapping of non-Arbor built-in
        NMODL mechanism catalogues compiled with modcc
        ignored_globals (iterable str): Skipped NrnGlobalParameter in decor
        replace_axon (): Axon replacement morphology
        create_mod_morph (): Create ACC morphology with axon replacement
        template_filename (str): file path of the cell.json , decor.acc and
        label_dict.acc jinja2 templates (with wildcards expanded by glob)
        template_dir (str): dir name of the jinja2 templates
        custom_jinja_params (dict): dict of additional jinja2 params in case
        of a custom template
    '''

    if pathlib.Path(morphology).suffix.lower() not in ['.swc', '.asc']:
        raise RuntimeError("Morphology file %s not supported in Arbor "
                           " (only supported types are .swc and .asc)."
                           % morphology)

    if replace_axon is not None:
        if not hasattr(arbor.segment_tree, 'tag_roots'):
            raise NotImplementedError("Need a newer version of Arbor"
                                      " for axon replacement.")
        logger.debug("Obtain axon replacement by applying "
                     "ArbFileMorphology.replace_axon after loading "
                     "morphology in Arbor.")
        replace_axon_path = \
            pathlib.Path(morphology).stem + '_axon_replacement.acc'
        replace_axon_acc = io.StringIO()
        arbor.write_component(replace_axon, replace_axon_acc)
        replace_axon_acc.seek(0)

        if create_mod_morph:
            modified_morphology_path = \
                pathlib.Path(morphology).stem + '_modified.acc'
            modified_morpho = ArbFileMorphology.load(
                os.path.join(morphology_dir, morphology), replace_axon_acc)
            replace_axon_acc.seek(0)
            modified_morphology_acc = io.StringIO()
            arbor.write_component(
                modified_morpho, modified_morphology_acc)
            modified_morphology_acc.seek(0)
            modified_morphology_acc = modified_morphology_acc.read()
        else:
            modified_morphology_path = None
            modified_morphology_acc = None

        replace_axon_acc = replace_axon_acc.read()
    else:
        replace_axon_path = None
        modified_morphology_path = None

    templates = _read_templates(template_dir, template_filename)

    default_location_order = list(ArbFileMorphology.region_labels.values())

    template_params = _get_template_params(mechs,
                                           parameters,
                                           ignored_globals,
                                           disable_banner,
                                           default_location_order,
                                           _arb_loc_desc)

    if custom_jinja_params is None:
        custom_jinja_params = {}

    filenames = {
        name: template_name + (name if name.startswith('.') else "_" + name)
        for name in templates.keys()}

    # postprocess template parameters for Arbor
    channels = template_params['channels']
    point_channels = template_params['point_channels']
    banner = template_params['banner']

    # global_mechs refer to default mechanisms/params in Arbor
    # [mech -> param]
    global_mechs = \
        _arb_convert_params_and_group_by_mech_global(
            template_params['global_params'])

    # section_mechs refer to locally painted mechanisms/params in Arbor
    # [loc -> mech -> param.name/.value]
    section_mechs, additional_global_mechs = \
        _arb_convert_params_and_group_by_mech_local(
            template_params['section_params'], channels)
    for mech, params in additional_global_mechs.items():
        global_mechs[mech] = \
            global_mechs.get(mech, []) + params

    # scaled_mechs refer to params with iexprs in Arbor
    # [loc -> mech -> param.location/.name/.value/.value_scaler]
    range_params = {loc: [] for loc in default_location_order}
    for param in template_params['range_params']:
        range_params[param.location].append(param)
    range_params = list(range_params.items())

    section_scaled_mechs, global_scaled_mechs = \
        _arb_convert_params_and_group_by_mech_local(
            range_params, channels)

    # join mechs constant params with inhomogeneous ones on mechanisms
    _arb_append_scaled_mechs(global_mechs, global_scaled_mechs)
    for loc in section_scaled_mechs:
        _arb_append_scaled_mechs(section_mechs[loc], section_scaled_mechs[loc])

    # section_pprocess_mechs refer to locally placed mechanisms/params in Arbor
    # [loc -> mech -> param.name/.value]
    pprocess_mechs, global_pprocess_mechs = \
        _arb_convert_params_and_group_by_mech_local(
            template_params['pprocess_params'], point_channels)
    if any(len(params) > 0 for params in global_pprocess_mechs.values()):
        raise ValueError('Point process mechanisms cannot be'
                         ' placed globally in Arbor.')

    # Evaluate synapse locations
    # (no new labels introduced, but locations explicitly defined)
    pprocess_mechs = _arb_eval_point_proc_locs(pprocess_mechs)

    # translate mechs to Arbor's convention
    arb_cats = _arb_load_mech_catalogues(ext_catalogues)

    global_mechs = _arb_nmodl_global_translate_density(global_mechs, arb_cats)
    section_mechs = {
        loc: _arb_nmodl_global_translate_density(mechs, arb_cats)
        for loc, mechs in section_mechs.items()}
    pprocess_mechs = {
        loc: _arb_nmodl_global_translate_points(mechs, arb_cats)
        for loc, mechs in pprocess_mechs.items()}

    global_scaled_mechs = _arb_project_scaled_mechs(global_mechs)
    section_scaled_mechs = {loc: _arb_project_scaled_mechs(mechs)
                            for loc, mechs in section_mechs.items()}

    # populate label dict
    label_dict = dict()

    for acc_labels in [section_mechs.keys(),
                       section_scaled_mechs.keys(),
                       pprocess_mechs.keys()]:
        for acc_label in acc_labels:
            if acc_label.name in label_dict and \
                    acc_label != label_dict[acc_label.name]:
                raise ValueError(
                    'Label %s already exists in' % acc_label.name +
                    ' label_dict with different definition: '
                    ' %s != %s.' % (label_dict[acc_label.name].defn,
                                    acc_label.defn))
            elif acc_label.name not in label_dict:
                label_dict[acc_label.name] = acc_label

    ret = {filenames[name]:
           template.render(template_name=template_name,
                           banner=banner,
                           morphology=morphology,
                           replace_axon=replace_axon_path,
                           modified_morphology=modified_morphology_path,
                           filenames=filenames,
                           label_dict=label_dict,
                           global_mechs=global_mechs,
                           global_scaled_mechs=global_scaled_mechs,
                           section_mechs=section_mechs,
                           section_scaled_mechs=section_scaled_mechs,
                           pprocess_mechs=pprocess_mechs,
                           **custom_jinja_params)
           for name, template in templates.items()}

    if replace_axon is not None:
        ret[replace_axon_path] = replace_axon_acc
        if modified_morphology_path is not None:
            ret[modified_morphology_path] = modified_morphology_acc

    return ret


def output_acc(output_dir, cell, parameters,
               template_filename='acc/*_template.jinja2',
               ext_catalogues=None,
               create_mod_morph=False,
               sim=None):
    '''Output mixed JSON/ACC format for Arbor cable cell to files

    Args:
        output_dir (str): Output directory. If not exists, will be created
        cell (): Cell model to output
        parameters (): Values for mechanism parameters, etc.
        template_filename (str): file path of the cell.json , decor.acc and
        label_dict.acc jinja2 templates (with wildcards expanded by glob)
        ext_catalogues (): Name to path mapping of non-Arbor built-in
        NMODL mechanism catalogues compiled with modcc
        create_mod_morph (str): Output ACC with axon replacement
        sim (): Neuron simulator instance (only used used with axon
        replacement if morphology has not yet been instantiated)
    '''
    output = cell.create_acc(parameters, template_filename,
                             ext_catalogues=ext_catalogues,
                             create_mod_morph=create_mod_morph,
                             sim=sim)

    cell_json = [comp_rendered
                 for comp, comp_rendered in output.items()
                 if pathlib.Path(comp).suffix == '.json']
    assert len(cell_json) == 1
    cell_json = json.loads(cell_json[0])

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for comp, comp_rendered in output.items():
        comp_filename = os.path.join(output_dir, comp)
        if os.path.exists(comp_filename):
            raise RuntimeError("%s already exists!" % comp_filename)
        with open(os.path.join(output_dir, comp), 'w') as f:
            f.write(comp_rendered)

    morpho_filename = os.path.join(
        output_dir, cell_json['morphology']['original'])
    if os.path.exists(morpho_filename):
        raise RuntimeError("%s already exists!" % morpho_filename)
    shutil.copy2(cell.morphology.morphology_path, morpho_filename)


# Read the mixed JSON/ACC-output, to be moved to Arbor in future release
def read_acc(cell_json_filename):
    '''Return constituents to build an Arbor cable cell from create_acc-export

    Args:
        cell_json_filename (str): The path to the JSON file containing
        meta-information on morphology, label-dict and decor of exported cell
    '''

    with open(cell_json_filename) as cell_json_file:
        cell_json = json.load(cell_json_file)

    cell_json_dir = os.path.dirname(cell_json_filename)

    morpho_filename = os.path.join(cell_json_dir,
                                   cell_json['morphology']['original'])
    replace_axon = cell_json['morphology'].get('replace_axon', None)
    if replace_axon is not None:
        replace_axon = os.path.join(cell_json_dir, replace_axon)
    morpho = ArbFileMorphology.load(morpho_filename, replace_axon)

    labels = arbor.load_component(
        os.path.join(cell_json_dir, cell_json['label_dict'])).component
    decor = arbor.load_component(
        os.path.join(cell_json_dir, cell_json['decor'])).component

    return cell_json, morpho, labels, decor
