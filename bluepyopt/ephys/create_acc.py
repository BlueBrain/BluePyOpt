'''create JSON/ACC files for Arbor from a set of BluePyOpt.ephys parameters'''

# pylint: disable=R0914

import os
import logging
import pathlib
from collections import namedtuple
from glob import glob

import numpy
import jinja2
import json
import shutil
import ast

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

from .create_hoc import Location, RangeExpr, \
    _get_template_params, format_float, DEFAULT_LOCATION_ORDER
from .morphologies import ArbFileMorphology


# Define Neuron to Arbor variable conversions
ArbVar = namedtuple('ArbVar', 'name, conv')


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
                         inst_distribution=param.inst_distribution)
    else:
        raise ValueError('Invalid parameter expression type.')


def _arb_is_global_property(loc, param):
    """Returns if region-specific variable is a global property in Arbor."""
    return loc == 'all' and (
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


# Define BluePyOpt to Arbor region mapping
# (relabeling locations to SWC convention)
# Remarks:
#  - using SWC convetion: 'dend' for basal dendrite, 'apic' for apical dendrite
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
    somatic=_make_tagged_region('soma', ArbFileMorphology.tags['soma']),
    axonal=_make_tagged_region('axon', ArbFileMorphology.tags['axon']),
    basal=_make_tagged_region('dend', ArbFileMorphology.tags['dend']),
    apical=_make_tagged_region('apic', ArbFileMorphology.tags['apic']),
    myelinated=_make_tagged_region('myelin', ArbFileMorphology.tags['myelin']),
)


def _arb_load_mech_catalogues():
    """Load Arbor's built-in mechanism catalogues"""

    # # Generated with NMODL in arbor/mechanisms
    # import os, re
    #
    # nmodl_pattern = '^\s*%s\s+((?:\w+\,\s*)*?\w+)\s*?$'
    # suffix_pattern = nmodl_pattern % 'SUFFIX'
    # globals_pattern = nmodl_pattern % 'GLOBAL'
    # ranges_pattern = nmodl_pattern % 'RANGE'
    #
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
    #
    # mechs = dict()
    # for cat in ['allen', 'BBP', 'default']:
    #     mechs[cat] = dict()
    #     cat_dir = 'arbor/mechanisms/' + cat
    #     for f in os.listdir(cat_dir):
    #         with open(os.path.join(cat_dir,f)) as fd:
    #             print(f"Processing {f}", flush=True)
    #             mechs[cat][f[:-4]] = process_nmodl(fd.read())
    # print(json.dumps(mechs, indent=4))

    catalogues = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            'static/arbor_mechanisms.json'))
    with open(catalogues) as f:
        arb_cats = json.load(f)

    return arb_cats


def _find_mech_and_convert_param_name(param, mechs):
    """Find a parameter's mechanism and convert name to Arbor convention"""
    mech_suffix_matches = numpy.where([param.name.endswith("_" + mech)
                                       for mech in mechs])[0]
    if mech_suffix_matches.size == 0:
        return None, _nrn2arb_param(param, name=param.name)
    elif mech_suffix_matches.size == 1:
        mech = mechs[mech_suffix_matches[0]]
        name = param.name[:-(len(mech) + 1)]
        return mech, _nrn2arb_param(param, name=name)
    else:
        raise RuntimeError("Parameter name %s matches multiple mechanisms %s "
                           % (param.name, repr(mechs[mech_suffix_matches])))


def _arb_convert_params_and_group_by_mech(params, channels):
    mech_params = [_find_mech_and_convert_param_name(
                   param, channels) for param in params]
    mechs = {mech: [] for mech, _ in mech_params}
    for mech, param in mech_params:
        mechs[mech].append(param)
    return mechs


def _arb_convert_params_and_group_by_mech_global(params, channels):
    """Group global params by mechanism, rename them to Arbor convention"""
    return _arb_convert_params_and_group_by_mech(
        [Location(name=name, value=value) for name, value in params.items()],
        channels['all']
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
                scale=_arb_generate_iexpr(p)) for p in scaled_params]


def _arb_nmodl_global_translate_mech(mech_name, mech_params, arb_cats):
    """Integrate NMODL GLOBAL parameters of Arbor-built-in mechanisms
     into mechanism name and add catalogue prefix"""
    arb_mech = None
    for cat in ['BBP', 'default', 'allen']:  # in order of precedence
        if mech_name in arb_cats[cat]:
            arb_mech = arb_cats[cat][mech_name]
            mech_name = cat + '::' + mech_name
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
            mech_name += '/' + ','.join(mech_name_suffix)
            return (mech_name, remaining_mech_params)


def _arb_nmodl_global_translate(mechs, arb_cats):
    """Translate all mechanisms in a region"""
    return dict([_arb_nmodl_global_translate_mech(mech, params, arb_cats)
                 for mech, params in mechs.items()])


def _arb_filter_scaled_mechs(mechs):
    """Returns all mechanisms with scaled parameters in Arbor"""
    scaled_mechs = dict()
    for mech, params in mechs.items():
        range_iexprs = [p for p in params if isinstance(p, RangeIExpr)]
        if len(range_iexprs) > 0:
            scaled_mechs[mech] = range_iexprs
    return scaled_mechs


class ArbIExprValueEliminator(ast.NodeTransformer):
    """Divide expression (symbolically) by value and replace
        non-linear occurrences by numeric value"""
    def __init__(self, value):
        self._stack = []
        self._nodes_to_remove = []
        self._remove_count = 0
        self._value = value

    def generic_visit(self, node):
        self._stack.append(node)  # keep track of visitor stack

        node = super(ArbIExprValueEliminator, self).generic_visit(node)

        nodes_removed = []
        for node_to_remove in self._nodes_to_remove:
            if node_to_remove in ast.iter_child_nodes(node):
                # replace this node and remove child
                node = node.left if node.right == node_to_remove \
                    else node.right
                nodes_removed.append(node_to_remove)
                self._remove_count += 1
                if self._remove_count > 1:
                    raise ValueError(
                        'Unsupported inhomogeneous expression in Arbor'
                        ' - must be linear in the parameter value.')
        self._nodes_to_remove = [n for n in self._nodes_to_remove
                                 if n not in nodes_removed]

        self._stack.pop()

        # top-level expression node that is non-linear in the value
        if len(self._stack) == 2 and self._remove_count == 0:
            return ast.BinOp(left=node, op=ast.Div(),
                             right=ast.Constant(value=self._value))
        else:
            return node

    def _is_linear(self, node):
        """Check if expression is linear in this node"""
        prev_frame = node
        for next_frame in reversed(self._stack[2:]):
            if not isinstance(next_frame, ast.BinOp) or \
                not (isinstance(next_frame.op, ast.Mult) or
                     isinstance(next_frame.op, ast.Div) and
                     next_frame.left == prev_frame):
                return False
            prev_frame = next_frame
        return True

    def visit_Name(self, node):
        if node.id == '_arb_parse_iexpr_value':
            # remove if expression is linear in value, else replace by constant
            if self._is_linear(node) and \
                    self._remove_count + len(self._nodes_to_remove) == 0:
                self._nodes_to_remove.append(node)
                return node
            else:
                return ast.Constant(value=self._value)
        else:
            return node


class ArbIExprEmitter(ast.NodeVisitor):
    """Emit Arbor S-expression from parse tree"""

    _iexpr_symbols = {
        ast.Constant: 'scalar',
        ast.Num: 'scalar',
        ast.Add: 'add',
        ast.Sub: 'sub',
        ast.Mult: 'mul',
        ast.Div: 'div',
        'math.pi': 'pi',
        'math.exp': 'exp',
        'math.log': 'log',
    }

    def __init__(self, constant_formatter):
        self._base_stack = []
        self._emitted = []
        self._constant_formatter = constant_formatter

    def emit(self):
        return ' '.join(self._emitted)

    def _emit(self, expr):
        return self._emitted.append(expr)

    def generic_visit(self, node):
        self._base_stack.append(node)

        # fail if more than base stack
        if len(self._base_stack) > 2:
            raise ValueError('Arbor inhomogeneous expression generation'
                             ' failed: Unsupported node %s' % repr(node))

        ret = super(ArbIExprEmitter, self).generic_visit(node)
        self._base_stack.pop()
        return ret

    def visit_Constant(self, node):
        self._emit(
            '(%s %s)' % (self._iexpr_symbols[type(node)],
                         self._constant_formatter(node.value))
        )

    def visit_Num(self, node):
        self._emit(
            '(%s %s)' % (self._iexpr_symbols[type(node)],
                         self._constant_formatter(node.n))
        )

    def visit_Attribute(self, node):
        if node.value.id == 'math' and node.attr == 'pi':
            self._emit(
                '(%s)' % self._iexpr_symbols['math.pi']
            )
        else:
            raise ValueError('Unsupported attribute %s in Arbor'
                             % node)

    def visit_UnaryOp(self, node):
        if isinstance(node.op, ast.UAdd):
            self.visit(node.value)
        elif isinstance(node.op, ast.USub):
            if isinstance(node.operand, ast.Constant):
                self.visit(ast.Constant(-node.operand.value))
            else:
                self.visit(ast.BinOp(left=ast.Constant(-1),
                                     op=ast.Mult(),
                                     right=node.operand))
        else:
            raise ValueError('Unsupported unary operation %s in Arbor'
                             % node.op)

    def visit_BinOp(self, node):
        op_type = type(node.op)
        if op_type not in self._iexpr_symbols:
            raise ValueError('Unsupported binary operation %s in Arbor'
                             % op_type)
        self._emit(
            '(' + self._iexpr_symbols[type(node.op)]
        )
        self.visit(node.left),
        self.visit(node.right)
        self._emit(
            ')'
        )

    def visit_Call(self, node):
        func = node.func
        if func.value.id == 'math':
            if len(node.args) > 1:
                raise ValueError('Arbor iexpr generation failed:'
                                 ' math functions can only have a'
                                 ' single argument.')
            func_symbol = func.value.id + '.' + func.attr
            if func_symbol not in self._iexpr_symbols:
                raise ValueError('Arbor iexpr generation failed - '
                                 ' Unknown symbol %s.' % func_symbol)
            self._emit(
                '(' + self._iexpr_symbols[func_symbol]
            )
            self.visit(node.args[0])
            self._emit(
                ')'
            )

    def visit_Name(self, node):
        if node.id == '_arb_parse_iexpr_distance':
            self._emit(
                '(distance (region "soma"))'
            )


def _arb_generate_iexpr(range_expr, constant_formatter=format_float):
    """Generate Arbor iexpr from instantiated distribution
     of NrnSegmentSomaDistanceScaler"""
    scaler_expr = range_expr.inst_distribution.format(
        value='_arb_parse_iexpr_value',
        distance='_arb_parse_iexpr_distance')

    # Parse expression
    scaler_ast = ast.parse(scaler_expr)

    # Turn into scaling expression, replacing non-linear occurrences of value
    value_eliminator = ArbIExprValueEliminator(range_expr.value)
    scaler_ast = value_eliminator.visit(scaler_ast)

    # Generate S-expression
    iexpr_emitter = ArbIExprEmitter(constant_formatter=constant_formatter)
    iexpr_emitter.visit(scaler_ast)
    return iexpr_emitter.emit()


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
        morphology (str): Name of morphology
        ignored_globals (iterable str): Skipped NrnGlobalParameter in decor
        replace_axon (str): String replacement for the 'replace_axon' command.
        Only False is supported at the moment.
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
        logger.debug("Obtain axon replacement by applying "
                     "ArbFileMorphology.replace_axon after loading "
                     "morphology in Arbor.")
        replace_axon_json = json.dumps(replace_axon)
    else:
        replace_axon_json = None

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
    channels = template_params['channels']
    banner = template_params['banner']

    # global_mechs refer to default mechanisms/params in Arbor
    # [mech -> param]
    global_mechs = \
        _arb_convert_params_and_group_by_mech_global(
            template_params['global_params'], channels)

    # section_mechs refer to locally painted mechanisms/params in Arbor
    # [loc -> mech -> param.name/.value]
    section_mechs, additional_global_mechs = \
        _arb_convert_params_and_group_by_mech_local(
            template_params['section_params'], channels)
    for mech, params in additional_global_mechs.items():
        global_mechs[mech] = \
            global_mechs.get(mech, []) + params

    # scaled_mechs refer to params with iexprs in Arbor
    # [loc -> mech -> param.location/.name/.value/.inst_distribution]
    range_params = {loc: [] for loc in DEFAULT_LOCATION_ORDER}
    for param in template_params['range_params']:
        range_params[param.location].append(param)
    range_params = list(range_params.items())

    section_scaled_mechs, global_scaled_mechs = \
        _arb_convert_params_and_group_by_mech_local(
            range_params, channels)

    # join mechs constant params with inhomogeneous ones on mechanisms
    _arb_append_scaled_mechs(global_mechs, global_scaled_mechs)
    for loc, mechs in section_scaled_mechs.items():
        _arb_append_scaled_mechs(section_mechs[loc], section_scaled_mechs[loc])

    # translate mechs to Arbor's convention
    arb_cats = _arb_load_mech_catalogues()
    global_mechs = _arb_nmodl_global_translate(global_mechs, arb_cats)
    global_scaled_mechs = _arb_filter_scaled_mechs(global_mechs)
    section_mechs = {loc: _arb_nmodl_global_translate(mechs, arb_cats)
                     for loc, mechs in section_mechs.items()}
    section_scaled_mechs = {loc: _arb_filter_scaled_mechs(mechs)
                            for loc, mechs in section_mechs.items()}

    return {filenames[name]:
            template.render(template_name=template_name,
                            banner=banner,
                            morphology=morphology,
                            replace_axon=replace_axon_json,
                            filenames=filenames,
                            regions=_loc2arb_region,
                            global_mechs=global_mechs,
                            global_scaled_mechs=global_scaled_mechs,
                            section_mechs=section_mechs,
                            section_scaled_mechs=section_scaled_mechs,
                            **custom_jinja_params)
            for name, template in templates.items()}


def output_acc(output_dir, cell, parameters,
               template_filename='acc/*_template.jinja2',
               sim=None):
    '''Output mixed JSON/ACC format for Arbor cable cell to files

    Args:
        output_dir (str): Output directory. If not exists, will be created
        cell (): Cell model to output
        parameters (): Values for mechanism parameters, etc.
        template_filename (str): file path of the cell.json , decor.acc and
        label_dict.acc jinja2 templates (with wildcards expanded by glob)
        sim (): Neuron simulator instance (only used used with axon
        replacement if morphology has not yet been instantiated)
    '''
    output = cell.create_acc(parameters, template_filename, sim=sim)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for comp, comp_rendered in output.items():
        comp_filename = os.path.join(output_dir, comp)
        if os.path.exists(comp_filename):
            raise RuntimeError("%s already exists!" % comp_filename)
        with open(os.path.join(output_dir, comp), 'w') as f:
            f.write(comp_rendered)

    morpho_filename = os.path.join(
        output_dir, os.path.basename(cell.morphology.morphology_path))
    if os.path.exists(morpho_filename):
        raise RuntimeError("%s already exists!" % morpho_filename)
    shutil.copy2(cell.morphology.morphology_path, output_dir)


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

    morphology_filename = os.path.join(cell_json_dir,
                                       cell_json['morphology']['path'])
    if 'replace_axon' in cell_json['morphology']:
        replace_axon = cell_json['morphology']['replace_axon']
    else:
        replace_axon = None

    if morphology_filename.endswith('.swc'):
        morpho = arbor.load_swc_arbor(morphology_filename)
        if replace_axon is not None:
            morpho = ArbFileMorphology.replace_axon(morpho, replace_axon)
    elif morphology_filename.endswith('.asc'):
        morpho = arbor.load_asc(morphology_filename)
        if replace_axon is not None:
            morpho = \
                ArbFileMorphology.replace_axon(morpho.morphology, replace_axon)
        else:
            morpho = morpho.morphology
    else:
        raise RuntimeError(
            'Unsupported morphology {} (only .swc and .asc supported)'.format(
                morphology_filename))

    labels = arbor.load_component(
        os.path.join(cell_json_dir, cell_json['label_dict'])).component
    decor = arbor.load_component(
        os.path.join(cell_json_dir, cell_json['decor'])).component

    return cell_json, morpho, labels, decor
