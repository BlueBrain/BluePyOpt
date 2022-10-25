"""Translate spatially varying parameter-scaler expressions to Arbor iexprs"""

"""
Copyright (c) 2016-2022, EPFL/Blue Brain Project

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

import ast


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
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name):
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
                                 ' unsupported attribute %s.' %
                                 func.value.attr)
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


def generate_acc_scale_iexpr(iexpr, variables, constant_formatter):
    """Translate parameter-scaler python arithmetic expression to Arbor iexpr

    Args:
        iexpr (str): Python arithmetic expression (instantiated distribution)
        variables (): Mapping of variable name (referenced in the iexpr
        argument) to Arbor iexpr representation

    Returns:
        The Arbor iexpr corresponding to the python arithmetic expression
        with the variables substituted by their value.
    """

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
