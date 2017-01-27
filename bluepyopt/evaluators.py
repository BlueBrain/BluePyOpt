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

from abc import abstractmethod


class Evaluator(object):

    """Evaluator class

    An Evaluator maps a set of parameter values to objective values
        Args:
            objectives (Objectives):
                The objectives that will be the output of the evaluator.
            params (Parameters):
                The parameters that will be evaluated.

        Attributes:
            objectives (Objectives):
                Objective objects.
            params (Objectives):
                Parameter objects.
    """

    def __init__(self, objectives=None, params=None):
        self.objectives = objectives
        self.params = params

    # TODO add evaluate_with_dicts
    @abstractmethod
    def evaluate_with_dicts(self, param_dict):
        """Evaluate parameter a parameter set (abstract).

        Args:
            params (dict with values Parameters, and keys parameter names):
                The parameter values to be evaluated.

        Returns:
            objectives (dict with values Parameters, and keys objective names):
                Dict of Objective with values calculated by the Evaluator.

        """

    @abstractmethod
    def evaluate_with_lists(self, params):
        """Evaluate parameter a parameter set (abstract).

        Args:
            params (list of Parameters):
                The parameter values to be evaluated.

        Returns:
            objectives (list of Objectives):
                List of Objectives with values calculated by the Evaluator.

        """
