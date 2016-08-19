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

# pylint: disable=W0511

import logging

from bluepyopt.ephys.base import BaseEPhys
from bluepyopt.ephys.serializer import DictMixin

logger = logging.getLogger(__name__)

# TODO: use Location class to specify location


class Mechanism(BaseEPhys):

    """Base parameter class"""
    pass


class NrnMODMechanism(Mechanism, DictMixin):

    """Neuron mechanism"""

    SERIALIZED_FIELDS = (
        'name',
        'comment',
        'mod_path',
        'prefix',
        'locations',
        'preloaded',
    )

    def __init__(
            self,
            name,
            mod_path=None,
            prefix=None,
            locations=None,
            preloaded=True,
            deterministic=True,
            comment=''):
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

        super(NrnMODMechanism, self).__init__(name, comment)
        self.mod_path = mod_path
        self.prefix = prefix
        self.locations = locations
        self.preloaded = preloaded
        self.cell_model = None
        self.deterministic = deterministic

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""

        for location in self.locations:
            isec_list = location.instantiate(sim=sim, icell=icell)
            for isec in isec_list:
                try:
                    isec.insert(self.prefix)
                except ValueError as e:
                    raise ValueError(str(e) + ': ' + self.prefix)
                self.instantiate_determinism(
                    self.deterministic,
                    icell,
                    isec,
                    sim)

            logger.debug(
                'Inserted %s in %s', self.prefix, [
                    str(location) for location in self.locations])

    def instantiate_determinism(self, deterministic, icell, isec, sim):
        """Instantiate enable/disable determinism"""

        if self.prefix == 'StochKv':
            setattr(
                isec,
                'deterministic_%s' %
                (self.prefix),
                1 if deterministic else 0)

            if not deterministic:
                # Set the seeds
                short_secname = sim.neuron.h.secname(sec=isec).split('.')[-1]
                for iseg in isec:
                    seg_name = '%s.%.19g' % (short_secname, iseg.x)
                    sim.neuron.h.setdata_StochKv(iseg.x, sec=isec)
                    seed_id1 = icell.gid
                    seed_id2 = self.hash_py(seg_name)
                    sim.neuron.h.setRNG_StochKv(seed_id1, seed_id2)
        else:
            if not deterministic:
                # can't do this for non-StochKv channels
                raise TypeError(
                    'Deterministic can only be set to False for '
                    'channel StochKv, not %s' %
                    self.prefix)

    def destroy(self, sim=None):
        """Destroy mechanism instantiation"""

        pass

    def __str__(self):
        """String representation"""

        return "%s: %s at %s" % (
            self.name, self.prefix,
            [str(location) for location in self.locations])

    @staticmethod
    def hash_hoc(string, sim):
        """Calculate hash value of string in Python"""

        # Load hash function in hoc, only do this once
        if not hasattr(sim.neuron.h, 'hash_str'):
            sim.neuron.h(NrnMODMechanism.hash_hoc_string)

        return sim.neuron.h.hash_str(string)

    @staticmethod
    def hash_py(string):
        """Calculate hash value of string in Python"""

        hash_value = 0.0
        for char in string:
            # Multiplicative hash function using Mersenne prime close to 2^32
            hash_value = (hash_value * 31 + ord(char)) % (pow(2, 31) - 1)

        return hash_value

    hash_hoc_string = \
        """
            func hash_str() {localobj sf strdef right
                sf = new StringFunctions()

                right = $s1

                n_of_c = sf.len(right)

                hash = 0
                char_int = 0
                for i = 0, n_of_c-1 {
                    sscanf(right, "%c", &char_int)
                    hash = (hash*31 + char_int) % (2^31 - 1)
                    sf.right(right, 1)
                }

                return hash
            }
        """
