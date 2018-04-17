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

from . import base
from . import serializer

logger = logging.getLogger(__name__)

# TODO: use Location class to specify location


class Mechanism(base.BaseEPhys):

    """Base parameter class"""
    pass


class NrnMODMechanism(Mechanism, serializer.DictMixin):

    """Neuron mechanism"""

    SERIALIZED_FIELDS = (
        'name',
        'comment',
        'mod_path',
        'suffix',
        'locations',
        'preloaded',
    )

    def __init__(
            self,
            name,
            mod_path=None,
            suffix=None,
            locations=None,
            preloaded=True,
            deterministic=True,
            prefix=None,
            comment=''):
        """Constructor

        Args:
            name (str): name of this object
            mod_path (str): path to the MOD file (not used for the moment)
            suffix (str): suffix of this mechanism in the MOD file
            locations (list of Locations): a list of Location objects pointing
                to where this mechanism should be added to.
            preloaded (bool): should this mechanism be side-loaded by
                BluePyOpt, or was it already loaded and compiled by the user ?
                (not used for the moment)
            prefix (str): Deprecated. Use suffix instead.
        """

        super(NrnMODMechanism, self).__init__(name, comment)
        self.mod_path = mod_path
        self.suffix = suffix
        self.locations = locations
        self.preloaded = preloaded
        self.cell_model = None
        self.deterministic = deterministic

        if prefix is not None and suffix is not None:
            raise TypeError('NrnMODMechanism: it is not allowed to set both '
                            'prefix and suffix in constructor: %s %s' %
                            (self.prefix, self.suffix))
        elif prefix is not None:
            self.suffix = prefix

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""

        for location in self.locations:
            isec_list = location.instantiate(sim=sim, icell=icell)
            for isec in isec_list:
                try:
                    isec.insert(self.suffix)
                except ValueError as e:
                    raise ValueError(str(e) + ': ' + self.suffix)
                self.instantiate_determinism(
                    self.deterministic,
                    icell,
                    isec,
                    sim)

        logger.debug(
            'Inserted %s in %s', self.suffix, [
                str(location) for location in self.locations])

    def instantiate_determinism(self, deterministic, icell, isec, sim):
        """Instantiate enable/disable determinism"""

        if 'Stoch' in self.suffix:
            setattr(
                isec,
                'deterministic_%s' %
                (self.suffix),
                1 if deterministic else 0)

            if not deterministic:
                # Set the seeds
                short_secname = sim.neuron.h.secname(sec=isec).split('.')[-1]
                for iseg in isec:
                    seg_name = '%s.%.19g' % (short_secname, iseg.x)
                    getattr(sim.neuron.h,
                            "setdata_%s" % self.suffix)(iseg.x, sec=isec)
                    seed_id1 = icell.gid
                    seed_id2 = self.hash_py(seg_name)
                    getattr(
                        sim.neuron.h,
                        "setRNG_%s" % self.suffix)(seed_id1, seed_id2)
        else:
            if not deterministic:
                # can't do this for non-Stoch channels
                raise TypeError(
                    'Deterministic can only be set to False for '
                    'Stoch channel, not %s' %
                    self.suffix)

    def destroy(self, sim=None):
        """Destroy mechanism instantiation"""

        pass

    def __str__(self):
        """String representation"""

        return "%s: %s at %s" % (
            self.name, self.suffix,
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
            hash_value = (hash_value * 31.0 + ord(char)) % (2.0 ** 31.0 - 1.0)

        return hash_value

    def generate_reinitrng_hoc_block(self):
        """"Create re_init_rng code blocks for this channel"""

        reinitrng_hoc_block = ''

        if 'Stoch' in self.suffix:
            # TODO this is dangerous, implicitely assumes type of location
            for location in self.locations:
                if self.deterministic:
                    reinitrng_hoc_block += \
                        '    forsec %(seclist_name)s { ' \
                        'deterministic_%(suffix)s = 1 }\n' % {
                            'seclist_name': location.seclist_name,
                            'suffix': self.suffix}
                else:
                    reinitrng_hoc_block += \
                        '    forsec %(seclist_name)s {%(mech_reinitrng)s' \
                        '    }\n' % {
                            'seclist_name': location.seclist_name,
                            'mech_reinitrng':
                            self.mech_reinitrng_block_template % {
                                'suffix': self.suffix}}

        return reinitrng_hoc_block

    @property
    def prefix(self):
        """Deprecated, prefix is now replaced by suffix"""

        return self.suffix

    @prefix.setter
    def prefix(self, value):
        """Deprecated, prefix is now replaced by suffix"""

        self.suffix = value

    hash_hoc_string = \
        """
func hash_str() {localobj sf strdef right
  sf = new StringFunctions()

  right = $s1

  n_of_c = sf.len(right)

  hash = 0
  char_int = 0
  for i = 0, n_of_c - 1 {
     sscanf(right, "%c", & char_int)
     hash = (hash * 31 + char_int) % (2 ^ 31 - 1)
     sf.right(right, 1)
  }

  return hash
}
"""

    reinitrng_hoc_string = """
proc re_init_rng() {localobj sf
    strdef full_str, name

    sf = new StringFunctions()

    if(numarg() == 1) {
        // We received a third seed
        channel_seed = $1
        channel_seed_set = 1
    } else {
        channel_seed_set = 0
    }

%(reinitrng_hoc_blocks)s
}
"""

    mech_reinitrng_block_template = """
        for (x, 0) {
            setdata_%(suffix)s(x)
            sf.tail(secname(), "\\\\.", name)
            sprint(full_str, "%%s.%%.19g", name, x)
            if (channel_seed_set) {
                setRNG_%(suffix)s(gid, hash_str(full_str), channel_seed)
            } else {
                setRNG_%(suffix)s(gid, hash_str(full_str))
            }
        }
"""


class NrnMODPointProcessMechanism(Mechanism):

    """Neuron mechanism"""

    def __init__(
            self,
            name,
            mod_path=None,
            suffix=None,
            locations=None,
            preloaded=True,
            comment=''):
        """Constructor

        Args:
            name (str): name of this object
            mod_path (str): path to the MOD file (not used for the moment)
            suffix (str): suffix of this mechanism in the MOD file
            locations (list of Locations): a list of Location objects pointing
                to compartments where this mechanism should be added to.
            preloaded (bool): should this mechanism be side-loaded by
                BluePyOpt, or was it already loaded and compiled by the user ?
                (not used for the moment)
        """

        super(NrnMODPointProcessMechanism, self).__init__(name, comment)
        self.mod_path = mod_path
        self.suffix = suffix
        self.locations = locations
        self.preloaded = preloaded
        self.cell_model = None
        self.pprocesses = None

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""

        self.pprocesses = []
        for location in self.locations:
            icomp = location.instantiate(sim=sim, icell=icell)
            try:
                iclass = getattr(sim.neuron.h, self.suffix)
                self.pprocesses.append(iclass(icomp.x, sec=icomp.sec))
            except AttributeError as e:
                raise AttributeError(str(e) + ': ' + self.suffix)

        logger.debug(
            'Inserted %s at %s ', self.suffix, [
                str(location) for location in self.locations])

    def destroy(self, sim=None):
        """Destroy mechanism instantiation"""

        self.pprocesses = None

    def __str__(self):
        """String representation"""

        return "%s: %s at %s" % (
            self.name, self.suffix,
            [str(location) for location in self.locations])
