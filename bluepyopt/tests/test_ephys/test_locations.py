"""bluepyopt.ephys.simulators tests"""

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

# pylint:disable=W0612, W0201
import json

import nose.tools as nt
from nose.plugins.attrib import attr

from bluepyopt import ephys
from bluepyopt.ephys.serializer import instantiator


@attr('unit')
def test_location_init():
    """ephys.locations: test if Location works"""

    loc = ephys.locations.Location('test')
    nt.assert_is_instance(loc, ephys.locations.Location)
    nt.assert_equal(loc.name, 'test')


@attr('unit')
class TestNrnSectionCompLocation(object):

    """Test class for NrnSectionCompLocation"""

    def __init__(self):
        """Constructor"""
        self.loc = None
        self.sim = None

    def setup(self):
        """Setup"""
        self.loc = ephys.locations.NrnSectionCompLocation(
            name='test',
            sec_name='soma[0]',
            comp_x=0.5)
        self.loc_dend = ephys.locations.NrnSectionCompLocation(
            name='test',
            sec_name='dend[1]',
            comp_x=0.5)
        nt.assert_equal(self.loc.name, 'test')
        self.sim = ephys.simulators.NrnSimulator()

    def test_instantiate(self):
        """ephys.locations.NrnSomaDistanceCompLocation: test instantiate"""

        # Create a little test class with a soma and two dendritic sections
        class Cell(object):

            """Cell class"""
            pass
        cell = Cell()
        soma = self.sim.neuron.h.Section()
        dend1 = self.sim.neuron.h.Section(name='dend1')
        dend2 = self.sim.neuron.h.Section(name='dend2')

        cell.soma = [soma]
        cell.dend = [dend1, dend2]

        soma_comp = self.loc.instantiate(sim=self.sim, icell=cell)
        nt.assert_equal(soma_comp, soma(0.5))

        dend_comp = self.loc_dend.instantiate(sim=self.sim, icell=cell)
        nt.assert_equal(dend_comp, dend2(0.5))


@attr('unit')
class TestNrnSeclistCompLocation(object):

    """Test class for NrnSectionCompLocation"""

    def __init__(self):
        """Constructor"""
        self.loc = None
        self.sim = None

    def setup(self):
        """Setup"""
        self.loc = ephys.locations.NrnSeclistCompLocation(
            name='test',
            seclist_name='somatic',
            sec_index=0,
            comp_x=0.5)
        self.loc_dend = ephys.locations.NrnSeclistCompLocation(
            name='test',
            seclist_name='basal',
            sec_index=1,
            comp_x=0.5)
        nt.assert_equal(self.loc.name, 'test')
        self.sim = ephys.simulators.NrnSimulator()

    def test_instantiate(self):
        """ephys.locations.NrnSomaDistanceCompLocation: test instantiate"""

        # Create a little test class with a soma and two dendritic sections
        class Cell(object):
            """Cell class"""
            pass

        cell = Cell()
        soma = self.sim.neuron.h.Section()
        dend1 = self.sim.neuron.h.Section(name='dend1')
        dend2 = self.sim.neuron.h.Section(name='dend2')

        cell.somatic = self.sim.neuron.h.SectionList()
        cell.somatic.append(soma)
        cell.basal = self.sim.neuron.h.SectionList()
        cell.basal.append(dend1)
        cell.basal.append(dend2)

        soma_comp = self.loc.instantiate(sim=self.sim, icell=cell)
        nt.assert_equal(soma_comp, soma(0.5))

        dend_comp = self.loc_dend.instantiate(sim=self.sim, icell=cell)
        nt.assert_equal(dend_comp, dend2(0.5))

        for _ in range(10000):
            soma_comp = self.loc.instantiate(sim=self.sim, icell=cell)


@attr('unit')
class TestNrnSomaDistanceCompLocation(object):

    """Test class for NrnSomaDistanceCompLocation"""

    def __init__(self):
        """Constructor"""
        self.loc = None
        self.sim = None

    def setup(self):
        """Setup"""
        self.loc = ephys.locations.NrnSomaDistanceCompLocation(
            'test',
            125,
            'testdend')
        nt.assert_equal(self.loc.name, 'test')
        self.sim = ephys.simulators.NrnSimulator()

    def test_instantiate(self):
        """ephys.locations.NrnSomaDistanceCompLocation: test instantiate"""

        # Create a little test class with a soma and two dendritic sections
        class Cell(object):

            """Cell class"""
            pass
        cell = Cell()
        soma = self.sim.neuron.h.Section()
        cell.soma = [soma]
        cell.testdend = self.sim.neuron.h.SectionList()
        dend1 = self.sim.neuron.h.Section(name='dend1')
        dend2 = self.sim.neuron.h.Section(name='dend2')

        cell.testdend.append(sec=dend1)
        cell.testdend.append(sec=dend2)

        nt.assert_raises(ephys.locations.EPhysLocInstantiateException,
                         self.loc.instantiate,
                         sim=self.sim,
                         icell=cell)

        dend1.connect(soma(0.5), 0.0)
        dend2.connect(dend1(1.0), 0.0)

        comp = self.loc.instantiate(sim=self.sim, icell=cell)
        nt.assert_equal(comp, dend2(0.5))


@attr('unit')
def test_serialize():
    """ephys.locations: Test serialize functionality"""
    from bluepyopt.ephys.locations import (
        NrnSeclistCompLocation,
        NrnSeclistLocation,
        NrnSeclistSecLocation,
        NrnSomaDistanceCompLocation)

    seclist_name, sec_index, comp_x, soma_distance = 'somatic', 0, 0.5, 800
    locations = (
        NrnSeclistCompLocation('NrnSeclistCompLocation',
                               seclist_name, sec_index, comp_x),
        NrnSeclistLocation(
            'NrnSeclistLocation', seclist_name),
        NrnSeclistSecLocation(
            'NrnSeclistSecLocation', seclist_name, sec_index),
        NrnSomaDistanceCompLocation(
            'NrnSomaDistanceCompLocation', soma_distance, seclist_name),)

    for loc in locations:
        serialized = loc.to_dict()
        nt.ok_(isinstance(json.dumps(serialized), str))
        deserialized = instantiator(serialized)
        nt.ok_(isinstance(deserialized, loc.__class__))
        nt.eq_(deserialized.seclist_name, seclist_name)
        nt.eq_(deserialized.name, loc.__class__.__name__)
