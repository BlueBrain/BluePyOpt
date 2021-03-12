"""Score calculator classes"""

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

from . import objectives


class ObjectivesCalculator(object):

    """Score calculator"""

    def __init__(
            self,
            objectives=None):
        """Constructor

        Args:
            objectives (list of Objective): objectives over which to calculate
        """

        self.objectives = objectives

    def calculate_scores(self, responses, cell_model=None, param_dict=None):
        """Calculator the score for every objective"""

        scores = {}

        if param_dict and cell_model:
            cell_model.freeze(param_dict)

        for objective in self.objectives:

            if issubclass(type(objective), objectives.EFeatureObjective):
                scores[objective.name] = objective.calculate_score(responses)
            elif issubclass(type(objective), objectives.RuleObjective):
                if param_dict and cell_model:
                    scores[objective.name] = objective.calculate_score(
                        cell_model
                    )
            else:
                raise Exception('Unknown objective class: {}'.format(type(
                    objective))
                )

        if param_dict and cell_model:
            cell_model.unfreeze(param_dict.keys())

        return scores

    def calculate_values(self, responses, cell_model=None, param_dict=None):
        """Calculator the value of each objective"""

        values = {}

        if param_dict and cell_model:
            cell_model.freeze(param_dict)

        for objective in self.objectives:

            if issubclass(type(objective), objectives.EFeatureObjective):
                values[objective.name] = objective.calculate_value(responses)
            elif issubclass(type(objective), objectives.RuleObjective):
                if param_dict and cell_model:
                    values[objective.name] = objective.calculate_value(
                        cell_model
                    )
            else:
                raise Exception('Unknown objective class: {}'.format(
                    type(objective))
                )

        if param_dict and cell_model:
            cell_model.unfreeze(param_dict.keys())

        return values

    def __str__(self):

        return 'objectives:\n  %s' % '\n  '.join(
            [str(obj) for obj in self.objectives]) \
            if self.objectives is not None else 'objectives:\n'
