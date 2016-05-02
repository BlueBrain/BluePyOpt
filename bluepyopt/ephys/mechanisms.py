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
        """Constructor

        Args:
            name (str): name of this object
        """

        self.name = name


class NrnMODMechanism(Mechanism):

    """Neuron mechanism"""

    def __init__(
            self,
            name,
            mod_path=None,
            prefix=None,
            locations=None,
            preloaded=True):
        """Constructor

        Args:
            name (str): name of this object
            mod_path (str): path to the MOD file (not used for the moment)
            prefix (str): prefix of this mechanism in the MOD file
            locations (list of Locations): a list of Location objects pointing
                to where this mechanism should be added to.
            preloaded (bool): should this mechanism be side-loaded by BluePyOpt,
                or was it already loaded and compiled by the user ?
                (not used for the moment)
        """

        super(NrnMODMechanism, self).__init__(name)
        self.mod_path = mod_path
        self.prefix = prefix
        self.locations = locations
        self.preloaded = True
        self.cell_model = None

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""

        for location in self.locations:
            isec_list = location.instantiate(sim=sim, icell=icell)
            for isec in isec_list:
                try:
                    isec.insert(self.prefix)
                except ValueError as e:
                    raise ValueError(str(e) + ': ' + self.prefix)
            logger.debug(
                'Inserted %s in %s', self.prefix, [
                    str(location) for location in self.locations])

    def destroy(self):
        """Destroy mechanism instantiation"""

        pass

    def __str__(self):
        """String representation"""

        return "%s: %s %s" % (
            self.name, [str(location) for location in self.locations],
            self.prefix)
