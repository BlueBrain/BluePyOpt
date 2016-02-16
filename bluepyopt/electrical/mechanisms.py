"""
Mechanism classes

Theses classes represent mechanisms in the model
"""

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


import logging

logger = logging.getLogger(__name__)

# TODO: use Location class to specify location


class Mechanism(object):
    """Base parameter class"""

    def __init__(self, name):
        """Constructor"""
        self.name = name

    def destroy(self):
        """Destroy mechanism instantiation"""
        pass


class NrnMODMechanism(Mechanism):

    """Neuron mechanism"""

    def __init__(
            self,
            name,
            mod_path=None,
            prefix=None,
            locations=None,
            preloaded=True):
        """Constructor"""

        Mechanism.__init__(self, name)
        self.mod_path = mod_path
        self.prefix = prefix
        self.locations = locations
        self.preloaded = True

    def instantiate(self, cell):
        """Instantiate"""

        for location in self.locations:
            isec_list = location.instantiate(cell)
            for isec in isec_list:
                isec.insert(self.prefix)
            logger.debug('Inserted %s in %s',
                         self.prefix, self.locations)

    def __str__(self):
        """String representation"""

        return "%s: %s %s" % (self.name, self.locations, self.prefix)
