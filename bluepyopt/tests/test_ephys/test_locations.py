"""bluepyopt.ephys.simulators tests"""

"""
Copyright (c) 2016-2022, EPFL/Blue Brain Project

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
import numpy as np

import pytest

from bluepyopt import ephys
from bluepyopt.ephys.serializer import instantiator


@pytest.mark.unit
def test_location_init():
    """ephys.locations: test if Location works"""

    loc = ephys.locations.Location('test')
    assert isinstance(loc, ephys.locations.Location)
    assert loc.name == 'test'


@pytest.mark.unit
class TestNrnSectionCompLocation(object):

    """Test class for NrnSectionCompLocation"""

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
        assert self.loc.name == 'test'
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
        assert soma_comp == soma(0.5)

        dend_comp = self.loc_dend.instantiate(sim=self.sim, icell=cell)
        assert dend_comp == dend2(0.5)


@pytest.mark.unit
class TestNrnSeclistCompLocation(object):

    """Test class for NrnSectionCompLocation"""

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
        assert self.loc.name == 'test'
        self.sim = ephys.simulators.NrnSimulator()

    def test_instantiate(self):
        """ephys.locations.NrnSeclistCompLocation: test instantiate"""

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
        assert soma_comp == soma(0.5)

        dend_comp = self.loc_dend.instantiate(sim=self.sim, icell=cell)
        assert dend_comp == dend2(0.5)

        for _ in range(10000):
            soma_comp = self.loc.instantiate(sim=self.sim, icell=cell)


@pytest.mark.unit
class TestNrnSeclistSecLocation(object):

    """Test class for NrnSeclistSecLocation"""

    def setup(self):
        """Setup"""
        self.loc = ephys.locations.NrnSeclistSecLocation(
            name='test',
            seclist_name='somatic',
            sec_index=0)
        self.loc_dend = ephys.locations.NrnSeclistSecLocation(
            name='test',
            seclist_name='basal',
            sec_index=1)
        assert self.loc.name == 'test'
        self.sim = ephys.simulators.NrnSimulator()

    def test_instantiate(self):
        """ephys.locations.NrnSeclistSecLocation: test instantiate"""

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
        assert soma_comp == soma

        dend_comp = self.loc_dend.instantiate(sim=self.sim, icell=cell)
        assert dend_comp == dend2


@pytest.mark.unit
class TestNrnSomaDistanceCompLocation(object):

    """Test class for NrnSomaDistanceCompLocation"""

    def setup(self):
        """Setup"""
        self.loc = ephys.locations.NrnSomaDistanceCompLocation(
            'test',
            125,
            'testdend')
        assert self.loc.name == 'test'
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

        pytest.raises(ephys.locations.EPhysLocInstantiateException,
                      self.loc.instantiate,
                      sim=self.sim,
                      icell=cell)

        dend1.connect(soma(0.5), 0.0)
        dend2.connect(dend1(1.0), 0.0)

        comp = self.loc.instantiate(sim=self.sim, icell=cell)
        assert comp == dend2(0.5)


@pytest.mark.unit
class TestNrnSecSomaDistanceCompLocation(object):

    """Test class for NrnSecSomaDistanceCompLocation"""

    def setup(self):
        """Setup"""
        self.loc = ephys.locations.NrnSecSomaDistanceCompLocation(
            'test',
            125,
            1,
            'testdend')
        self.loc_other = ephys.locations.NrnSecSomaDistanceCompLocation(
            'test',
            250,
            4,
            'testdend')
        assert self.loc.name == 'test'
        self.sim = ephys.simulators.NrnSimulator()

    def test_instantiate(self):
        """ephys.locations.NrnSomaDistanceCompLocation: test instantiate"""

        # Create a little test class with a soma and two dendritic sections
        class Cell(object):

            """Cell class"""
            pass
        cell = Cell()
        soma = self.sim.neuron.h.Section(name="soma[0]")
        cell.soma = [soma]
        cell.testdend = self.sim.neuron.h.SectionList()
        dend1 = self.sim.neuron.h.Section(name='dend[0]')
        dend2 = self.sim.neuron.h.Section(name='dend[1]')
        dend3 = self.sim.neuron.h.Section(name='dend[2]')
        dend4 = self.sim.neuron.h.Section(name='dend[3]')
        dend5 = self.sim.neuron.h.Section(name='dend[4]')

        cell.testdend.append(sec=dend1)
        cell.testdend.append(sec=dend2)
        cell.testdend.append(sec=dend3)
        cell.testdend.append(sec=dend4)
        cell.testdend.append(sec=dend5)

        dend1.connect(soma(0.5), 0.0)
        dend2.connect(dend1(1.0), 0.0)
        dend3.connect(dend1(1.0), 0.0)
        dend4.connect(dend3(1.0), 0.0)
        dend5.connect(dend4(1.0), 0.0)

        comp = self.loc.instantiate(sim=self.sim, icell=cell)
        assert comp == dend2(0.5)
        comp = self.loc_other.instantiate(sim=self.sim, icell=cell)
        assert comp == dend4(0.5)


@pytest.mark.unit
class TestNrnTrunkSomaDistanceCompLocation(object):

    """Test class for NrnTrunkSomaDistanceCompLocation"""

    def setup(self):
        """Setup"""
        self.loc = ephys.locations.NrnTrunkSomaDistanceCompLocation(
            'test',
            soma_distance=150,
            sec_name='testdend')
        self.loc_other = ephys.locations.NrnTrunkSomaDistanceCompLocation(
            'test',
            soma_distance=350,
            sec_name='testdend')

        assert self.loc.name == 'test'
        self.sim = ephys.simulators.NrnSimulator()

    def test_instantiate(self):
        """ephys.locations.NrnSomaDistanceCompLocation: test instantiate"""

        # Create a little test class with a soma and two dendritic sections
        class Cell(object):

            """Cell class"""
            pass
        cell = Cell()
        soma = self.sim.neuron.h.Section(name="soma[0]")
        cell.soma = [soma]
        cell.testdend = self.sim.neuron.h.SectionList()
        dend1 = self.sim.neuron.h.Section(name='dend[0]')
        dend2 = self.sim.neuron.h.Section(name='dend[1]')
        dend3 = self.sim.neuron.h.Section(name='dend[2]')
        dend4 = self.sim.neuron.h.Section(name='dend[3]')
        dend5 = self.sim.neuron.h.Section(name='dend[4]')

        cell.testdend.append(sec=dend1)
        cell.testdend.append(sec=dend2)
        cell.testdend.append(sec=dend3)
        cell.testdend.append(sec=dend4)
        cell.testdend.append(sec=dend5)

        x0 = self.sim.neuron.h.Vector([0] * 10)
        d = self.sim.neuron.h.Vector([1] * 10)

        x1 = self.sim.neuron.h.Vector(np.linspace(0, 100, 10))
        self.sim.neuron.h.pt3dadd(x0, x1, x0, d, sec=dend1)
        x2 = self.sim.neuron.h.Vector(np.linspace(100, 200, 10))
        self.sim.neuron.h.pt3dadd(x0, x2, x0, d, sec=dend2)
        x3 = self.sim.neuron.h.Vector(np.linspace(200, 300, 10))
        self.sim.neuron.h.pt3dadd(x0, x3, x0, d, sec=dend3)
        x4 = self.sim.neuron.h.Vector(np.linspace(300, 400, 10))
        self.sim.neuron.h.pt3dadd(x0, x4, x0, d, sec=dend4)
        x5 = self.sim.neuron.h.Vector(np.linspace(400, 500, 10))
        self.sim.neuron.h.pt3dadd(x0, x5, x0, d, sec=dend5)

        dend1.connect(soma(0.5), 0.0)
        dend2.connect(dend1(1.0), 0.0)
        dend3.connect(dend1(1.0), 0.0)
        dend4.connect(dend3(1.0), 0.0)
        dend5.connect(dend4(1.0), 0.0)

        comp = self.loc.instantiate(sim=self.sim, icell=cell)
        assert comp == dend3(0.5)
        comp = self.loc_other.instantiate(sim=self.sim, icell=cell)
        assert comp == dend5(0.5)


@pytest.mark.unit
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
        assert isinstance(json.dumps(serialized), str)
        deserialized = instantiator(serialized)
        assert isinstance(deserialized, loc.__class__)
        assert deserialized.seclist_name == seclist_name
        assert deserialized.name == loc.__class__.__name__
