"""Cell evaluator class"""

"""
Copyright (c) 2016, EPFL/Blue Brain Project

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

# Not sure code below should go in module or class
import copy_reg
import types


class CellEvaluator(object):

    """Simple cell class"""

    def __init__(
            self,
            cell_template=None,
            param_names=None,
            fitness_protocols=None,
            fitness_calculator=None,
            isolate_protocols=True):
        """Constructor"""

        self.cell_template = cell_template
        self.param_names = param_names
        # Stimuli used for fitness calculation
        self.fitness_protocols = fitness_protocols
        # Fitness value calculator
        self.fitness_calculator = fitness_calculator

        self.isolate_protocols = isolate_protocols

    @property
    def objectives(self):
        """Return objectives"""

        return self.fitness_calculator.objectives

    @property
    def params(self):
        """Return params of this evaluation"""
        params = [self.cell_template.params[param_name])
                  for param_name in self.param_names]
        return params

    def param_dict(self, param_array):
        """Convert param_array in param_dict"""
        param_dict = dict(
            (name, array) for name, array in zip(self.param_names,
                                                 param_array))
        return param_dict

    def objective_dict(self, objective_array):
        """Convert objective_array in objective_dict"""
        objective_names = [objective.name
                           for objective in self.fitness_calculator.objectives]

        objective_dict = dict(
            (name, array) for name, array in zip(objective_names,
                                                 objective_array))

        return objective_dict

    def evaluate_with_dicts(self, param_dict=None):
        """Run evaluation with dict as input and output"""

        if self.fitness_calculator is None:
            raise Exception('CellTemplate: need fitness_calculator to evaluate')

        responses = {}

        # TODO clean this up

        for protocol_name, protocol in self.fitness_protocols.iteritems():
            if self.isolate_protocols:
                import multiprocessing

                # TODO this should only be executed once

                def _reduce_method(meth):
                    """Overwrite reduce"""
                    return (getattr, (meth.__self__, meth.__func__.__name__))

                copy_reg.pickle(types.MethodType, _reduce_method)

                # This multiprocessing makes sure that Neuron starts in a clean
                # state every time we run a protocol
                pool = multiprocessing.Pool(1, maxtasksperchild=1)
                responses.update(
                    pool.apply(self.cell_template.run_protocols,
                               args=[{protocol_name: protocol}],
                               kwds={'param_values': param_dict}))

                # THis might help with garbage collecting the pool workers
                pool.terminate()
                pool.join()
            else:
                responses.update(self.cell_template.run_protocols(
                    {protocol_name: protocol},
                    param_values=param_dict))

        return self.fitness_calculator.calculate_scores(responses)

    def evaluate_with_lists(self, param_list=None):
        """Run evaluation with lists as input and outputs"""

        param_dict = self.param_dict(param_list)

        obj_dict = self.evaluate_with_dicts(param_dict=param_dict)

        return obj_dict.values()
