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
import ast

from bluepyopt.ephys.base import BaseEPhys
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

    def scale(self, value, segment=None, sim=None):  # pylint: disable=W0613
        """Scale a value based on a segment"""

        return self.multiplier * value + self.offset

    def __str__(self):
        """String representation"""

        return '%s * value + %s' % (self.multiplier, self.offset)


class NrnSegmentSomaDistanceScaler(ParameterScaler, DictMixin):

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
            dist_params (list): list of names of parameters that parametrise
                the distribution. These names will become attributes of this
                object.
                The distribution string should contain these names, and they
                will be replaced by values of the corresponding attributes
            soma_ref_location (float): location along the soma used as origin
                from which to compute the distances. Expressed as a fraction
                (between 0.0 and 1.0).
        """

        super(NrnSegmentSomaDistanceScaler, self).__init__(name, comment)
        self.distribution = distribution

        self.dist_param_names = dist_param_names
        self.soma_ref_location = soma_ref_location

        if not (0. <= self.soma_ref_location <= 1.):
            raise ValueError('soma_ref_location must be between 0 and 1.')

        if self.dist_param_names is not None:
            for dist_param_name in self.dist_param_names:
                if dist_param_name not in self.distribution:
                    raise ValueError(
                        'NrnSegmentSomaDistanceScaler: "{%s}" '
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
                    raise ValueError('NrnSegmentSomaDistanceScaler: %s '
                                     'was uninitialised' % dist_param_name)
                dist_dict[dist_param_name] = dist_param_value

        # Use this special formatting to bypass missing keys
        return string.Formatter().vformat(self.distribution, (), dist_dict)

    def eval_dist(self, value, distance):
        """Create the final dist string"""

        scale_dict = {}
        scale_dict['distance'] = format_float(distance)
        scale_dict['value'] = format_float(value)

        return self.inst_distribution.format(**scale_dict)

    def scale(self, value, segment, sim=None):
        """Scale a value based on a segment"""

        # TODO soma needs other addressing scheme

        soma = segment.sec.cell().soma[0]

        # Initialise origin
        sim.neuron.h.distance(0, self.soma_ref_location, sec=soma)

        distance = sim.neuron.h.distance(1, segment.x, sec=segment.sec)

        # Find something to generalise this
        import math  # pylint:disable=W0611 #NOQA

        # This eval is unsafe (but is it ever dangerous ?)
        # pylint: disable=W0123
        return eval(self.eval_dist(value, distance))

    def acc_scale_iexpr(self, value, constant_formatter=format_float):
        """Generate Arbor scale iexpr for a given value"""

        iexpr = self.inst_distribution

        variables = dict(
            value=value,
            distance='(distance %s)' %  # could be a ctor param if required
            ArbFileMorphology.region_labels['somatic'].ref
        )

        return generate_arbor_iexpr(iexpr, variables, constant_formatter)

    def __str__(self):
        """String representation"""

        return self.distribution


# Utilities to generate Arbor S-expressions for morphologically
# inhomogeneous parameter scalers
class ArbIExprValueEliminator(ast.NodeTransformer):
    """Divide expression (symbolically) by named variable and replace
    non-linear occurrences by numeric value"""
    def __init__(self, variable_name, value):
        self._stack = []
        self._nodes_to_remove = []
        self._remove_count = 0
        self._variable_name = variable_name
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
        if node.id == self._variable_name:
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
    """Emit Arbor S-expression from parse tree
    replacing named variables by specified S-expression"""

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

    def __init__(self, var_name_to_sexpr, constant_formatter):
        self._base_stack = []
        self._emitted = []
        self._var_name_to_sexpr = var_name_to_sexpr
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
        if hasattr(func, 'value'):
            if func.value.id == 'math':
                if len(node.args) > 1:
                    raise ValueError('Arbor iexpr generation failed -'
                                     ' math functions can only have a'
                                     ' single argument.')
                func_symbol = func.value.id + '.' + func.attr
                if func_symbol not in self._iexpr_symbols:
                    raise ValueError('Arbor iexpr generation failed -'
                                     ' unknown symbol %s.' % func_symbol)
                self._emit(
                    '(' + self._iexpr_symbols[func_symbol]
                )
                self.visit(node.args[0])
                self._emit(
                    ')'
                )
            else:
                raise ValueError('Arbor iexpr generation failed -'
                                 ' unsupported module %s.' % func.value.id)
        else:
            raise ValueError('Arbor iexpr generation failed -'
                             ' unsupported function %s.' % func.id)

    def visit_Name(self, node):
        if node.id in self._var_name_to_sexpr:
            self._emit(
                self._var_name_to_sexpr[node.id]
            )
        else:
            raise ValueError('Arb iexpr generation failed:'
                             ' No valid substitution for %s.' % node.id)


def generate_arbor_iexpr(iexpr, variables, constant_formatter):
    """Generate Arbor iexpr from parameter-scaler python expression"""

    if 'value' not in variables:
        raise ValueError('Arbor iexpr generation failed for %s:' % iexpr +
                         ' \'value\' not in variables dict: %s' % variables)

    emit_dict = {'_arb_parse_iexpr_' + k: v
                 for k, v in variables.items()}

    scaler_expr = iexpr.format(
        **{k: '_arb_parse_iexpr_' + k for k in variables})

    # Parse expression
    scaler_ast = ast.parse(scaler_expr)

    # Turn into scaling expression, replacing non-linear occurrences of value
    value_eliminator = ArbIExprValueEliminator(
        variable_name='_arb_parse_iexpr_value',
        value=variables['value'])
    scaler_ast = value_eliminator.visit(scaler_ast)

    # Generate S-expression
    iexpr_emitter = ArbIExprEmitter(
        var_name_to_sexpr=emit_dict,
        constant_formatter=constant_formatter)

    iexpr_emitter.visit(scaler_ast)
    return iexpr_emitter.emit()
