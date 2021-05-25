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

<<<<<<< HEAD
from . import objectives
=======
>>>>>>> 923c7e5 (Rebase CMA on master)

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

    def calculate_scores(self, responses):
        """Calculator the score for every objective"""
<<<<<<< HEAD
        
        scores = {}
        
        if param_dict and cell_model:
            cell_model.freeze(param_dict)
        
        for objective in self.objectives:
            
            if issubclass(type(objective), objectives.EFeatureObjective):
                scores[objective.name] = objective.calculate_score(responses)
            elif issubclass(type(objective), objectives.RuleObjective):
                if param_dict and cell_model:
                    scores[objective.name] = objective.calculate_score(cell_model)
            else:
                raise Exception('Unknown objective class: {}'.format(type(objective)))
        
        if param_dict and cell_model:
            cell_model.unfreeze(param_dict.keys())
        
        return scores
=======

        return {objective.name: objective.calculate_score(responses)
                for objective in self.objectives}
>>>>>>> 923c7e5 (Rebase CMA on master)

    def calculate_values(self, responses):
        """Calculator the value of each objective"""

        return {objective.name: objective.calculate_value(responses)
                for objective in self.objectives}

    def __str__(self):
<<<<<<< HEAD
        
=======
>>>>>>> 923c7e5 (Rebase CMA on master)
        return 'objectives:\n  %s' % '\n  '.join(
            [str(obj) for obj in self.objectives]) \
            if self.objectives is not None else 'objectives:\n'
