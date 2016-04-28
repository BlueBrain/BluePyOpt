"""Objective classes"""

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


class Objective(object):

    """EPhys feature"""

    def __init__(self, name, features=None):
        """Constructor"""

        self.name = name
        self.features = features

    def calculate_feature_scores(self, responses):
        """Calculate the scores for the individual features"""

        scores = []
        for feature in self.features:
            scores.append(feature.calculate_score(responses))

        return scores


class SingletonObjective(Objective):

    """Single eFEL feature"""

    def __init__(self, name, feature):
        """Constructor"""

        super(SingletonObjective, self).__init__(name, [feature])

    def calculate_score(self, responses):
        """Objective score"""

        return self.calculate_feature_scores(responses)[0]

    def __str__(self):
        """String representation"""

        return '( %s )' % self.features[0]


class MaxObjective(Objective):

    """Max of list of eFEL feature"""

    def __init__(self, name, features):
        """Constructor"""

        Objective.__init__(self, name, features)

    @property
    def calculate_score(self, responses):
        """Objective score"""

        return max(self.calculate_feature_scores(responses))


class WeightedSumObjective(Objective):

    """Weighted sum of list of eFEL features"""

    def __init__(self, name, features, weights):
        """Constructor"""

        Objective.__init__(self, name, features)
        if len(weights) != len(features):
            raise Exception(
                'WeightedSumObjective: number of weights must be equal to '
                'number of features')
        self.weights = weights

    @property
    def calculate_score(self, responses):
        """Objective score"""

        score = 0.0
        feature_scores = self.calculate_feature_scores(responses)

        for feature_score, weight in zip(feature_scores, self.weights):
            score += weight * feature_score

        return score
