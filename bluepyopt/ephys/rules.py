"""Rules classes"""

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
import logging

import bluepyopt
import math

logger = logging.getLogger(__name__)


def sigmoid(x):
    """Sigmoid function"""
    return 1 / (1 + math.exp(-x))


class Rule():

    """Abstract Rule class"""

    name = ""

    def __init__(
        self,
        name=None,
        force_max_score=False,
        max_score=250
    ):
        """Constructor
        Args:
            name (str): name of the eFELFeature object
            force_max_score (bool): should the max_score limit be applied to
                the score
            max_score (float): upper bound for the score
        """

        if name:
            self.name = name

        self.force_max_score = force_max_score
        self.max_score = max_score

    def _rule(self, cell_model):
        return None

    def _loss_function(self, value):
        return None

    def calculate_value(self, cell_model):
        """Calculate rule value"""

        if cell_model is None:
            rule_value = None
        else:
            rule_value = self._rule(cell_model)

        logger.debug(
            'Calculated value for %s: %s',
            self.name,
            str(rule_value)
        )

        return rule_value

    def calculate_score(self, cell_model):
        """Calculate the score"""

        if cell_model is None:
            score = self.max_score
        else:
            score = self._loss_function(self._rule(cell_model))

        if self.force_max_score:
            score = min(score, self.max_score)

        logger.debug('Calculated score for %s: %f', self.name, score)

        return score

    def __str__(self):
        """String representation"""

        return "Rule %s " % (self.name)


class SumConductivityRule(Rule):

    """SumConductivityRule class

       Punish high sum of conductivity based on a sigmoid loss function
    """

    name = "SumConductivity"

    def __init__(
        self,
        name=None,
        force_max_score=False,
        max_score=250,
        conductivity_target=2.
    ):
        """Constructor
        Args:
            name (str): name of the eFELFeature object
            force_max_score (bool): should the max_score limit be applied to
                the score
            max_score (float): upper bound for the score
        """

        super(SumConductivityRule, self).__init__(
            name=name,
            force_max_score=force_max_score,
            max_score=max_score
        )

        self.conductivity_target = conductivity_target

    def _rule(self, cell_model):

        sum_g = 0
        for param in cell_model.params.values():
            if param.name[0] == "g":
                sum_g += param.value

        return sum_g

    def _loss_function(self, value):

        # Center on conductivity_target
        _ = (value / self.conductivity_target) - 1.

        # Take the sigmoid
        return self.max_score * sigmoid(_)
