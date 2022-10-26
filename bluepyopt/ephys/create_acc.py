'''create JSON/ACC files for Arbor from a set of BluePyOpt.ephys parameters'''

# pylint: disable=R0914

import io
import logging
import pathlib
from collections import namedtuple, OrderedDict
import re

import jinja2
import json
import shutil

from bluepyopt.ephys.acc_utils import arbor
from bluepyopt.ephys.morphologies import ArbFileMorphology
from bluepyopt.ephys.create_hoc import \
    Location, RangeExpr, PointExpr, \
    _get_template_params, format_float

logger = logging.getLogger(__name__)

# Define Neuron to Arbor variable conversions
ArbVar = namedtuple('ArbVar', 'name, conv')  # turn into a class


# Inhomogeneous expression for scaled parameter in Arbor
RangeIExpr = namedtuple('RangeIExpr', 'name, value, scale')


# A mechanism's GLOBAL and RANGE variables in Arbor
MechMetaData = namedtuple('MechMetaData', 'globals, ranges')


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
    """Neuron to Arbor parameter renaming

    Args:
        name (str): Neuron parameter name
    """
    return _nrn2arb_var[name].name if name in _nrn2arb_var else name


def _nrn2arb_var_value(param):
    """Neuron to Arbor units conversion for parameter values

    Args:
        param (): A Neuron parameter with a value in Neuron units
    """

    if param.name in _nrn2arb_var and \
       _nrn2arb_var[param.name].conv is not None:
        return format_float(_nrn2arb_var[param.name].conv(float(param.value)))
    else:
        return param.value


def _nrn2arb_param(param, name):
    """Convert a Neuron parameter to Arbor format (name and units)

    Args:
        param (): A Neuron parameter
    """

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
        raise CreateAccException('Invalid parameter expression type.')


def _nrn2arb_mech_name(name):
    """Neuron to Arbor mechanism name conversion

    Args:
        name (): A Neuron mechanism name
    """
    if name in ['Exp2Syn', 'ExpSyn']:
        return name.lower()
    else:
        return name


def _arb_is_global_property(loc, param):
    """Returns if a label-specific variable is a global property in Arbor

    Args:
        loc (): An Arbor label describing the location
        param (): A parameter in Arbor format (name and units)
    """

    return loc == ArbFileMorphology.region_labels['all'] and (
        param.name in ['membrane-potential',
                       'temperature-kelvin',
                       'axial-resistivity',
                       'membrane-capacitance'] or
        param.name.split(' ')[0] in ['ion-internal-concentration',
                                     'ion-external-concentration',
                                     'ion-reversal-potential'])


def _arb_pop_global_properties(loc, mechs):
    """Pops global properties from a label-specific dict of mechanisms

    Args:
        loc (): An Arbor label describing the location
        mechs (): A mapping of mechanism name to list of parameters in
        Arbor format (None for non-mechanism parameters) from which
        Arbor global properties will be removed.

    Returns:
        A list of Arbor global properties
    """

    global_properties = []
    local_properties = []
    if None in mechs:
        for param in mechs[None]:
            if _arb_is_global_property(loc, param):
                global_properties.append(param)
            else:
                local_properties.append(param)
        mechs[None] = local_properties
    return global_properties


def _arb_filter_point_proc_locs(pprocess_mechs):
    """Filter locations from point process parameters

    Args:
        pprocess_mechs (): Point process mechanisms with parameters in
        Arbor format
    """

    result = {loc: dict() for loc in pprocess_mechs}

    for loc, mechs in pprocess_mechs.items():
        for mech, point_exprs in mechs.items():
            result[loc][mech.name] = dict(
                mech=mech.suffix,
                params=[Location(point_expr.name, point_expr.value)
                        for point_expr in point_exprs])

    return result


def _arb_load_catalogue_meta(cat_dir):
    """Load mechanism catalogue metadata from NMODL files

    Args:
        cat_dir (): Path to directory with NMODL files of catalogue

    Returns:
        Mapping of name to meta data for each mechanism in the directory
    """
    # used to generate arbor_mechanisms.json on NMODL from arbor/mechanisms

    nmodl_pattern = '^\s*%s\s+((?:\w+\,\s*)*?\w+)\s*?$'  # NOQA
    suffix_pattern = nmodl_pattern % 'SUFFIX'
    globals_pattern = nmodl_pattern % 'GLOBAL'
    ranges_pattern = nmodl_pattern % 'RANGE'

    def process_nmodl(nmodl_str):
        """Extract global and range parameters from Arbor-conforming NMODL"""
        try:
            nrn = re.search(r'NEURON\s+{([^}]+)}', nmodl_str,
                            flags=re.MULTILINE).group(1)
            suffix_ = re.search(suffix_pattern, nrn,
                                flags=re.MULTILINE)
            suffix_ = suffix_ if suffix_ is None else suffix_.group(1)
            globals_ = re.search(globals_pattern, nrn,
                                 flags=re.MULTILINE)
            globals_ = globals_ if globals_ is None \
                else re.findall(r'\w+', globals_.group(1))
            ranges_ = re.search(ranges_pattern, nrn,
                                flags=re.MULTILINE)
            ranges_ = ranges_ if ranges_ is None \
                else re.findall(r'\w+', ranges_.group(1))
        except Exception as e:
            raise CreateAccException(
                'NMODL-inspection for %s failed.' % nmodl_file) from e

        # skipping suffix_
        return MechMetaData(globals=globals_, ranges=ranges_)

    mechs = dict()
    cat_dir = pathlib.Path(cat_dir)
    for nmodl_file in cat_dir.glob('*.mod'):
        with open(cat_dir.joinpath(nmodl_file)) as f:
            mechs[nmodl_file.stem] = process_nmodl(f.read())

    return mechs


def _arb_load_mech_catalogue_meta(ext_catalogues):
    """Load metadata of external and Arbor's built-in mechanism catalogues

    Args:
        ext_catalogues (): Mapping of catalogue name to directory
        with NMODL files defining the mechanisms

    Returns:
        Ordered mapping of catalogue name -> mechanism name -> meta data
        for external and built-in catalogues (external ones taking precedence)
    """

    arb_cats = OrderedDict()

    if ext_catalogues is not None:
        for cat, cat_nmodl in ext_catalogues.items():
            arb_cats[cat] = _arb_load_catalogue_meta(
                pathlib.Path(cat_nmodl).resolve())

    builtin_catalogues = pathlib.Path(__file__).parent.joinpath(
        'static/arbor_mechanisms.json').resolve()
    with open(builtin_catalogues) as f:
        builtin_arb_cats = json.load(f)

    for cat in ['BBP', 'default', 'allen']:
        if cat not in arb_cats:
            arb_cats[cat] = {mech: MechMetaData(**meta)
                             for mech, meta in builtin_arb_cats[cat].items()}

    return arb_cats


def _find_mech_and_convert_param_name(param, mechs):
    """Find a parameter's mechanism and convert name to Arbor format

    Args:
        param (): A parameter in Neuron format
        mechs (): List of co-located NMODL mechanisms

    Returns:
        A tuple of mechanism name (None for a non-mechanism parameter) and
        parameter in Arbor format
    """
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
        raise CreateAccException("Parameter name %s matches" % param.name +
                                 " multiple mechanisms %s" %
                                 [repr(mechs[i]) for i in mech_matches])


def _arb_convert_params_and_group_by_mech(params, channels):
    """Turn list of Neuron parameters to Arbor format and group by mechanism

    Args:
        params (): List of parameters in Neuron format
        channels (): List of co-located NMODL mechanisms

    Returns:
        Mapping of Arbor mechanism name to list of parameters in Arbor format
    """
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
    """Group global params by mechanism, convert them to Arbor format"""
    return _arb_convert_params_and_group_by_mech(
        [Location(name=name, value=value) for name, value in params.items()],
        []  # no default mechanisms
    )


def _arb_convert_params_and_group_by_mech_local(params, channels):
    """Group local params by mechanism, convert them to Arbor format

    Args:
        params (): List of Arbor label/local parameters pairs in Neuron format
        channels (): Mapping of Arbor label to co-located NMODL mechanisms

    Returns:
        Mapping of Arbor label to mechanisms with their parameters in Arbor
        format (mechanism name is None for non-mechanism parameters) in the
        first component, global properties found in the second
    """
    local_mechs = dict()
    for loc, params in params:
        mechs = _arb_convert_params_and_group_by_mech(params, channels[loc])

        # move Arbor global properties to global_params
        global_properties = _arb_pop_global_properties(loc, mechs)
        local_mechs[loc] = mechs
    return local_mechs, global_properties

def _arb_add_global_scaled_mechs(mechs, global_scaled_mechs):
    """Add the global scaled mechs to mechs."""
    for scaled_params in global_scaled_mechs:
        mechs[None] = mechs.get(None, []) + \
            [RangeIExpr(
                name=p.name,
                value=format_float(p.value),
                scale=p.value_scaler.acc_scale_iexpr(p.value))
                for p in scaled_params]

def _arb_append_scaled_mechs(mechs, scaled_mechs):
    """Append scaled mechanism parameters to constant ones"""
    for mech, scaled_params in scaled_mechs.items():
        if mech is None and len(scaled_params) > 0:
            raise CreateAccException(
                'Non-mechanism parameters cannot have inhomogeneous'
                ' expressions in Arbor %s' % scaled_params)
        mechs[mech] = mechs.get(mech, []) + \
            [RangeIExpr(
                name=p.name,
                value=format_float(p.value),
                scale=p.value_scaler.acc_scale_iexpr(p.value))
                for p in scaled_params]


def _arb_nmodl_translate_mech(mech_name, mech_params, arb_cats):
    """Translate NMODL mechanism to Arbor ACC format

    Args:
        mech_name (): NMODL mechanism name (suffix)
        mech_params (): Mechanism parameters in Arbor format
        arb_cats (): Mapping of catalogue names to mechanisms
        with theirmeta data

    Returns:
        Tuple of mechanism name with NMODL GLOBAL parameters integrated and
        catalogue prefix added as well as the remaining RANGE parameters
    """

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
        if arb_mech.globals is None:  # only Arbor range params
            for param in mech_params:
                if param.name not in arb_mech.ranges:
                    raise CreateAccException(
                        '%s not a GLOBAL or RANGE parameter of %s' %
                        (param.name, mech_name))
            return (mech_name, mech_params)
        else:
            for param in mech_params:
                if param.name not in arb_mech.globals and \
                        param.name not in arb_mech.ranges:
                    raise CreateAccException(
                        '%s not a GLOBAL or RANGE parameter of %s' %
                        (param.name, mech_name))
            mech_name_suffix = []
            remaining_mech_params = []
            for mech_param in mech_params:
                if mech_param.name in arb_mech.globals:
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


def _arb_nmodl_translate_density(mechs, arb_cats):
    """Translate all density mechanisms in a specific region"""
    return dict([_arb_nmodl_translate_mech(mech, params, arb_cats)
                 for mech, params in mechs.items()])


def _arb_nmodl_translate_points(mechs, arb_cats):
    """Translate all point mechanisms for a specific locset"""
    result = dict()

    for synapse_name, mech_desc in mechs.items():
        mech, params = _arb_nmodl_translate_mech(
            mech_desc['mech'], mech_desc['params'], arb_cats)
        result[synapse_name] = dict(mech=mech,
                                    params=params)

    return result


def _arb_project_scaled_mechs(mechs):
    """Returns all (iexpr) parameters of scaled mechanisms in Arbor"""
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
        template_dir = \
            pathlib.Path(__file__).parent.joinpath('templates').resolve()

    template_paths = pathlib.Path(template_dir).glob(template_filename)

    templates = dict()
    for template_path in template_paths:
        with open(template_path) as template_file:
            template = template_file.read()
            name = template_path.name
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
        raise CreateAccException("Morphology file %s not supported in Arbor "
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
                pathlib.Path(morphology_dir).joinpath(morphology),
                replace_axon_acc)
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

    # global_mechs refer to default density mechs/params in Arbor
    # [mech -> param] (params under mech == None)
    global_mechs = \
        _arb_convert_params_and_group_by_mech_global(
            template_params['global_params'])

    # local_mechs refer to locally painted density mechs/params in Arbor
    # [label -> mech -> param.name/.value] (params under mech == None)
    local_mechs, additional_global_mechs = \
        _arb_convert_params_and_group_by_mech_local(
            template_params['section_params'], channels)
    for params in additional_global_mechs:
        global_mechs[None] = \
            global_mechs.get(None, []) + params

    # scaled_mechs refer to iexpr params of scaled density mechs in Arbor
    # [label -> mech -> param.location/.name/.value/.value_scaler]
    range_params = {loc: [] for loc in default_location_order}
    for param in template_params['range_params']:
        range_params[param.location].append(param)
    range_params = list(range_params.items())

    local_scaled_mechs, global_scaled_mechs = \
        _arb_convert_params_and_group_by_mech_local(
            range_params, channels)

    # join each mech's constant params with inhomogeneous ones on mechanisms
    _arb_add_global_scaled_mechs(global_mechs, global_scaled_mechs)
    for loc in local_scaled_mechs:
        _arb_append_scaled_mechs(local_mechs[loc], local_scaled_mechs[loc])

    # pprocess_mechs refer to locally placed mechs/params in Arbor
    # [label -> mech -> param.name/.value]
    pprocess_mechs, global_pprocess_mechs = \
        _arb_convert_params_and_group_by_mech_local(
            template_params['pprocess_params'], point_channels)
    if any(len(params) > 0 for params in global_pprocess_mechs):
        raise CreateAccException('Point process mechanisms cannot be'
                                 ' placed globally in Arbor.')

    # Evaluate synapse locations
    # (no new labels introduced, but locations explicitly defined)
    pprocess_mechs = _arb_filter_point_proc_locs(pprocess_mechs)

    # load metadata of external and Arbor's built-in mech catalogues
    arb_cats = _arb_load_mech_catalogue_meta(ext_catalogues)

    # translate mechs to Arbor's nomenclature
    global_mechs = _arb_nmodl_translate_density(global_mechs, arb_cats)
    local_mechs = {
        loc: _arb_nmodl_translate_density(mechs, arb_cats)
        for loc, mechs in local_mechs.items()}
    pprocess_mechs = {
        loc: _arb_nmodl_translate_points(mechs, arb_cats)
        for loc, mechs in pprocess_mechs.items()}

    # get iexpr parameters of scaled density mechs
    global_scaled_mechs = _arb_project_scaled_mechs(global_mechs)
    local_scaled_mechs = {loc: _arb_project_scaled_mechs(mechs)
                          for loc, mechs in local_mechs.items()}

    # populate label dict
    label_dict = dict()

    for acc_labels in [local_mechs.keys(),
                       local_scaled_mechs.keys(),
                       pprocess_mechs.keys()]:
        for acc_label in acc_labels:
            if acc_label.name in label_dict and \
                    acc_label != label_dict[acc_label.name]:
                raise CreateAccException(
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
                           local_mechs=local_mechs,
                           local_scaled_mechs=local_scaled_mechs,
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
    if len(cell_json) != 1:
        raise CreateAccException(
            'JSON file from create_acc is non-unique: %s' % cell_json)

    cell_json = json.loads(cell_json[0])

    output_dir = pathlib.Path(output_dir)
    if not output_dir.exists():
        output_dir.mkdir()
    for comp, comp_rendered in output.items():
        comp_filename = output_dir.joinpath(comp)
        if comp_filename.exists():
            raise CreateAccException("%s already exists!" % comp_filename)
        with open(output_dir.joinpath(comp), 'w') as f:
            f.write(comp_rendered)

    morpho_filename = output_dir.joinpath(cell_json['morphology']['original'])
    if morpho_filename.exists():
        raise CreateAccException("%s already exists!" % morpho_filename)
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

    cell_json_dir = pathlib.Path(cell_json_filename).parent

    morpho_filename = cell_json_dir.joinpath(
        cell_json['morphology']['original'])
    replace_axon = cell_json['morphology'].get('replace_axon', None)
    if replace_axon is not None:
        replace_axon = cell_json_dir.joinpath(replace_axon)
    morpho = ArbFileMorphology.load(morpho_filename, replace_axon)

    decor = arbor.load_component(
        cell_json_dir.joinpath(cell_json['decor'])).component
    labels = arbor.load_component(
        cell_json_dir.joinpath(cell_json['label_dict'])).component

    return cell_json, morpho, decor, labels


class CreateAccException(Exception):

    """All exceptions generated by create_acc module"""

    def __init__(self, message):
        """Constructor"""

        super(CreateAccException, self).__init__(message)
