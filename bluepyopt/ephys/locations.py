"""Location classes"""

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

# pylint: disable=W0511

import itertools

from bluepyopt.ephys.base import BaseEPhys
from bluepyopt.ephys.serializer import DictMixin
from bluepyopt.ephys.parameterscalers import format_float
from bluepyopt.ephys.acc import ArbLabel
from bluepyopt.ephys.morphologies import ArbFileMorphology
import numpy as np

import logging
logger = logging.getLogger(__name__)


class Location(BaseEPhys):

    """Location"""
    pass

# TODO make all these locations accept a cell name
# TODO instantiate should get the entire simulation environment
# TODO find better/more general name for this
# TODO specify in document abrevation comp=compartment, sec=section, ...


def _nth_isectionlist(isectionlist, index):
    """Get nth element of isectionlist

    Sectionlists don't support direct indexing
    """
    isection = next(
        itertools.islice(
            isectionlist,
            index,
            index + 1))
    return isection


class NrnSeclistCompLocation(Location, DictMixin):

    """Compartment in a sectionlist"""

    SERIALIZED_FIELDS = (
        'name',
        'comment',
        'seclist_name',
        'sec_index',
        'comp_x',
    )

    def __init__(
            self,
            name,
            seclist_name=None,
            sec_index=None,
            comp_x=None,
            comment=''):
        """Constructor

        Args:
            name (str): name of the object
            seclist_name (str): name of Neuron section list (ex: 'somatic')
            sec_index (int): index of the section in the section list
            comp_x (float): segx (0..1) of segment inside section
        """

        super(NrnSeclistCompLocation, self).__init__(name, comment)
        self.seclist_name = seclist_name
        self.sec_index = sec_index
        self.comp_x = comp_x

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiate compartment"""
        iseclist = getattr(icell, self.seclist_name)

        iseclist_size = len([x for x in iseclist])
        if self.sec_index >= iseclist_size:
            raise Exception(
                'NrnSeclistCompLocation: section index %d falls out of '
                'SectionList size of %d' %
                (self.sec_index, iseclist_size))
        isection = _nth_isectionlist(iseclist, self.sec_index)
        icomp = isection(self.comp_x)

        # The code above seems to add put a section on the stack
        # TODO remove line below once we figure out where the section is pushed
        sim.neuron.h.pop_section()

        return icomp

    def acc_label(self):
        """Arbor label"""
        raise EPhysLocAccException(
            '%s not supported in Arbor' % type(self).__name__ +
            ' (uses branches instead of NEURON sections).'
            ' Use ArbBranchRelLocation/ArbSegmentRelLocation/'
            'ArbLocsetLocation instead (consider using the'
            ' Arbor GUI to identify the precise branch/segment index'
            ' and relative position).')

    def __str__(self):
        """String representation"""

        return '%s[%s](%s)' % (self.seclist_name, self.sec_index, self.comp_x)


class NrnSectionCompLocation(Location, DictMixin):

    """Compartment in a section"""

    SERIALIZED_FIELDS = (
        'name',
        'comment',
        'seclist_name',
        'sec_index',
        'comp_x',
    )

    def __init__(
            self,
            name,
            sec_name=None,
            comp_x=None,
            comment=''):
        """Constructor

        Args:
            name (str): name of the object
            sec_name (str): name of Neuron section (ex: 'soma[0]')
            comp_x (float): segx (0..1) of segment inside section
        """

        super(NrnSectionCompLocation, self).__init__(name, comment)
        self.sec_name = sec_name
        self.comp_x = comp_x

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiate compartment"""

        # Dont see any other way but to use eval, apart from parsing the
        # sec_name string which can be complicated
        isection = eval('icell.%s' % self.sec_name)  # pylint: disable=W0123

        icomp = isection(self.comp_x)
        return icomp

    def acc_label(self):
        """Arbor label"""
        raise EPhysLocAccException(
            '%s not supported in Arbor' % type(self).__name__ +
            ' (uses branches instead of NEURON sections).'
            ' Use ArbBranchRelLocation/ArbSegmentRelLocation/'
            'ArbLocsetLocation instead (consider using the'
            ' Arbor GUI to identify the precise branch/segment index'
            ' and relative position).')

    def __str__(self):
        return '%s(%s)' % (self.sec_name, self.comp_x)


class NrnPointProcessLocation(Location):

    """Point process location"""

    def __init__(
            self,
            name,
            pprocess_mech,
            comment=''):
        """Constructor

        Args:
            name (str): name of the object
            pprocess_mech (str): point process mechanism
        """

        super(NrnPointProcessLocation, self).__init__(name, comment)
        self.pprocess_mech = pprocess_mech

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiated point processes"""

        return self.pprocess_mech.pprocesses

    def acc_label(self):
        """Arbor label"""
        return [loc.acc_label() for loc in self.pprocess_mech.locations]

    def __str__(self):
        """String representation"""

        return '%s' % (self.pprocess_mech.name)


class NrnSeclistLocation(Location, DictMixin):

    """Section in a sectionlist"""

    SERIALIZED_FIELDS = ('name', 'comment', 'seclist_name', )

    def __init__(
            self,
            name,
            seclist_name=None,
            comment=''):
        """Constructor

        Args:
            name (str): name of the object
            seclist_name (str): name of NEURON section list (ex: 'somatic')
        """

        super(NrnSeclistLocation, self).__init__(name, comment)
        self.seclist_name = seclist_name

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiate compartment"""

        isectionlist = getattr(icell, self.seclist_name)

        return (isection for isection in isectionlist)

    def acc_label(self):
        """Arbor label"""
        return ArbFileMorphology.region_labels[self.seclist_name]

    def __str__(self):
        """String representation"""

        return '%s' % (self.seclist_name)


class NrnSeclistSecLocation(Location, DictMixin):

    """Section in a sectionlist"""

    SERIALIZED_FIELDS = ('name', 'comment', 'seclist_name', 'sec_index', )

    def __init__(
            self,
            name,
            seclist_name=None,
            sec_index=None,
            comment=''):
        """Constructor

        Args:
            name (str): name of this object
            seclist_name (str): name of Neuron section list (ex: 'somatic')
            sec_index (int): index of the section
        """

        super(NrnSeclistSecLocation, self).__init__(name, comment)
        self.seclist_name = seclist_name
        self.sec_index = sec_index

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiate compartment"""

        isectionlist = getattr(icell, self.seclist_name)
        isection = _nth_isectionlist(isectionlist, self.sec_index)
        return isection

    def acc_label(self):
        """Arbor label"""
        raise EPhysLocAccException(
            '%s not supported in Arbor' % type(self).__name__ +
            ' (uses branches instead of NEURON sections).'
            ' Use ArbBranchLocation/ArbSegmentLocation/ArbRegionLocation'
            ' instead (consider using the Arbor GUI to identify the'
            ' precise branch/segment index).')

    def __str__(self):
        """String representation"""

        return '%s[%s]' % (self.seclist_name, self.sec_index)


class NrnSomaDistanceCompLocation(Location, DictMixin):

    """Compartment at distance from soma"""

    SERIALIZED_FIELDS = ('name', 'comment', 'soma_distance', 'seclist_name', )

    def __init__(
            self,
            name,
            soma_distance=None,
            seclist_name=None,
            comment=''):
        """Constructor

        Args:
            name (str): name of this object
            soma_distance (float): distance from soma to this compartment
            seclist_name (str): name of Neuron section list (ex: 'apical')
        """

        super(NrnSomaDistanceCompLocation, self).__init__(name, comment)
        self.soma_distance = soma_distance
        self.seclist_name = seclist_name

    # TODO this definitely has to be unit-tested
    # TODO add ability to specify origin
    def find_icomp(self, sim, iseclist):
        """Find the index of the compartment based on a list of isec
           and a distance"""
        icomp = None

        for isec in iseclist:
            start_distance = sim.neuron.h.distance(1, 0.0, sec=isec)
            end_distance = sim.neuron.h.distance(1, 1.0, sec=isec)

            min_distance = min(start_distance, end_distance)
            max_distance = max(start_distance, end_distance)

            if min_distance <= self.soma_distance <= max_distance:
                comp_x = float(self.soma_distance - min_distance) / \
                    (max_distance - min_distance)

                comp_diam = isec(comp_x).diam

                if comp_diam > 0.0:
                    icomp = isec(comp_x)

        if icomp is None:
            raise EPhysLocInstantiateException(
                'No comp found at %s distance from soma' %
                self.soma_distance)

        return icomp

    def instantiate(self, sim=None, icell=None):
        """Find the instantiate compartment"""

        soma = icell.soma[0]

        sim.neuron.h.distance(0, 0.5, sec=soma)

        iseclist = getattr(icell, self.seclist_name)

        return self.find_icomp(sim, iseclist)

    def acc_label(self):
        """Arbor label"""
        # Potentially non-unique location - in that case to be refined in the
        # Arbor GUI (create ArbLocsetLocation directly).
        # Alternatives to (on-components 0.5 (region "soma")) are
        #  - '(segment <id>)'
        #  - '(proximal (region %s)))' % self.seclist_name
        # If outer restrict results in non-unique location (cf. GUI) use
        # specific branch or similar instead of seclist_name, e.g.
        #  - (proximal-interval (distal (branch <id>)))
        # for a branch distally from the desired location
        acc_label = ArbLabel(
            'locset', self.name,
            '(restrict (distal-translate (on-components 0.5 %s) %s) %s)' %
            (ArbFileMorphology.region_labels['somatic'].ref,
             format_float(self.soma_distance),
             ArbFileMorphology.region_labels[self.seclist_name].ref))
        logger.warning(
            'Make sure that ACC label %s' % acc_label.loc +
            ' for NrnSomaDistanceCompLocation (%s) ' % str(self) +
            ' instantiates to a unique location on the morphology.'
            ' Use the Arbor GUI to validate/refine the location expression.')
        return acc_label

    def __str__(self):
        """String representation"""

        return '%f micron from soma in %s' % (
            self.soma_distance, self.seclist_name)


class NrnSecSomaDistanceCompLocation(NrnSomaDistanceCompLocation):

    """Compartment on a section defined both by a section index and distance
       from the soma """

    SERIALIZED_FIELDS = ('name', 'comment', 'soma_distance', 'sec_name',
                         'sec_index', )

    def __init__(
        self,
        name,
        soma_distance=None,
        sec_index=None,
        seclist_name=None,
        comment=""
    ):
        """Constructor

        Args:
            name (str): name of this object
            soma_distance (float): distance from soma to this compartment
            sec_index (int): index of the section  to consider
            sec_name (str): name of Neuron sections (ex: 'apic')
        """
        super(NrnSecSomaDistanceCompLocation, self).__init__(
            name,
            soma_distance=soma_distance,
            seclist_name=seclist_name,
            comment=comment,
        )
        self.sec_index = sec_index

    def instantiate(self, sim=None, icell=None):
        """Find the instantiate compartment"""

        if self.sec_index is None:
            raise EPhysLocInstantiateException(
                "No apical point was given")

        sections = getattr(icell, self.seclist_name)
        section = _nth_isectionlist(sections, self.sec_index)

        branches = []
        while True:

            name = str(section.name()).split(".")[-1]
            if name == "soma[0]":
                break

            branches.append(section)

            if sim.neuron.h.SectionRef(sec=section).has_parent():
                section = sim.neuron.h.SectionRef(sec=section).parent
            else:
                raise EPhysLocInstantiateException(
                    "soma[0] was not reached from isec point "
                    "%f" % self.sec_index
                )

        soma = icell.soma[0]

        sim.neuron.h.distance(0, 0.5, sec=soma)

        return self.find_icomp(sim, branches)

    def acc_label(self):
        """Arbor label"""
        raise EPhysLocAccException('%s not supported in Arbor.' %
                                   type(self).__name__)


class NrnTrunkSomaDistanceCompLocation(NrnSecSomaDistanceCompLocation):
    """Location at a distance from soma along a main direction.

    We search for the section that is the furthest away from some along
    a direction, and pick a location at a given distance from soma along
    the path to that section.

    If direction == 'radial', the largest radial direction is used.

    This is most useful to follow the trunk of an apical dendrite
    without knowing the apical point, but only that apical trunk goes along y.
    """

    def __init__(
        self,
        name,
        soma_distance=None,
        sec_index=None,
        seclist_name=None,
        direction=None,
        comment=""
    ):
        """Constructor

        Args:
            name (str): name of this object
            soma_distance (float): distance from soma to this compartment
            sec_index (int): index of the section  to consider
            sec_name (str): name of Neuron sections (ex: 'apic')
            direction (list of 3 elements): 3d vector representing direction,
                if None, default is [0, 1, 0]
        """
        super(NrnTrunkSomaDistanceCompLocation, self).__init__(
            name,
            soma_distance=soma_distance,
            sec_index=sec_index,
            seclist_name=seclist_name,
            comment=comment
        )

        if direction is None:
            direction = [0.0, 1.0, 0.0]
        self.direction = direction

    def set_sec_index(self, icell=None):
        """Search for the point furthest away along given direction."""
        points = np.array(
            [
                [
                    section.x3d(section.n3d() - 1),
                    section.y3d(section.n3d() - 1),
                    section.z3d(section.n3d() - 1),
                ]
                for section in getattr(icell, self.seclist_name)
            ]
        )
        if self.direction == 'radial':
            self.sec_index = int(np.argmax(np.linalg.norm(points, axis=1)))
        else:
            self.sec_index = int(np.argmax(points.dot(self.direction)))

    def instantiate(self, sim=None, icell=None):
        """ """
        if self.sec_index is None:
            self.set_sec_index(icell=icell)
        return super().instantiate(sim=sim, icell=icell)

    def acc_label(self):
        """Arbor label"""
        raise EPhysLocAccException('%s not supported in Arbor.' %
                                   type(self).__name__)


class ArbLocation(Location):
    """Arbor Location"""

    pass


class ArbSegmentLocation(ArbLocation):
    """Segment in an Arbor morphology.
    """

    def __init__(self, name, segment, comment=''):
        super().__init__(name, comment)
        self.segment = segment

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiate compartment"""
        raise EPhysLocInstantiateException(
            '%s not supported in NEURON.' % type(self).__name__)

    def acc_label(self):
        """Arbor label"""
        return ArbLabel('region', self.name, '(segment %s)' % (self.segment))

    def __str__(self):
        """String representation"""
        return '%s \'%s\'' % (type(self).__name__, self.acc_label().defn)


class ArbBranchLocation(ArbLocation):
    """Branch in an Arbor morphology.

    Arbor's counterpart of NrnSeclistSecLocation.
    """

    def __init__(self, name, branch, comment=''):
        super().__init__(name, comment)
        self.branch = branch

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiate compartment"""
        raise EPhysLocInstantiateException(
            '%s not supported in NEURON.' % type(self).__name__)

    def acc_label(self):
        """Arbor label"""
        return ArbLabel('region', self.name, '(branch %s)' % (self.branch))

    def __str__(self):
        """String representation"""
        return '%s \'%s\'' % (type(self).__name__, self.acc_label().defn)


class ArbSegmentRelLocation(ArbLocation):
    """Relative position on a segment in an Arbor morphology.
    """

    def __init__(self, name, segment, pos, comment=''):
        super().__init__(name, comment)
        self.segment = segment
        self.pos = pos

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiate compartment"""
        raise EPhysLocInstantiateException(
            '%s not supported in NEURON.' % type(self).__name__)

    def acc_label(self):
        """Arbor label"""
        return ArbLabel('locset', self.name,
                        '(on-components %s (segment %s))' %
                        (format_float(self.pos), self.segment))

    def __str__(self):
        """String representation"""
        return '%s \'%s\'' % (type(self).__name__, self.acc_label().defn)


class ArbBranchRelLocation(ArbLocation):
    """Relative position on a branch in an Arbor morphology.

    Arbor's counterpart of NrnSeclistCompLocation.
    """

    def __init__(self, name, branch, pos, comment=''):
        super().__init__(name, comment)
        self.branch = branch
        self.pos = pos

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiate compartment"""
        raise EPhysLocInstantiateException(
            '%s not supported in NEURON.' % type(self).__name__)

    def acc_label(self):
        """Arbor label"""
        return ArbLabel('locset', self.name,
                        '(location %s %s)' %
                        (self.branch, format_float(self.pos)))

    def __str__(self):
        """String representation"""
        return '%s \'%s\'' % (type(self).__name__, self.acc_label().defn)


class ArbLocsetLocation(ArbLocation):
    """Arbor location set defined by a user-supplied string (S-expression).
    """

    def __init__(self, name, locset, comment=''):
        super().__init__(name, comment)
        self.locset = locset

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiate compartment"""
        raise EPhysLocInstantiateException(
            '%s not supported in NEURON.' % type(self).__name__)

    def acc_label(self):
        """Arbor label"""
        return ArbLabel('locset', self.name, self.locset)

    def __str__(self):
        """String representation"""
        return '%s %s' % (type(self).__name__, self.acc_label().defn)


class ArbRegionLocation(ArbLocation):
    """Arbor region defined by a user-supplied string (S-expression).
    """

    def __init__(self, name, region, comment=''):
        super().__init__(name, comment)
        self.region = region

    def instantiate(self, sim=None, icell=None):  # pylint: disable=W0613
        """Find the instantiate compartment"""
        raise EPhysLocInstantiateException(
            '%s not supported in NEURON.' % type(self).__name__)

    def acc_label(self):
        """Arbor label"""
        return ArbLabel('region', self.name, self.region)

    def __str__(self):
        """String representation"""
        return '%s %s' % (type(self).__name__, self.acc_label().defn)


class EPhysLocInstantiateException(Exception):

    """All exceptions generated by location instantiation"""

    def __init__(self, message):
        """Constructor"""

        super(EPhysLocInstantiateException, self).__init__(message)


class EPhysLocAccException(Exception):

    """All exceptions generated by ACC label creation"""

    def __init__(self, message):
        """Constructor"""

        super(EPhysLocAccException, self).__init__(message)
