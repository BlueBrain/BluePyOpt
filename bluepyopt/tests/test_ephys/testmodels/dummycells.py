"""Dummy cell model used for testing"""

import bluepyopt.ephys as ephys


class DummyCellModel1(ephys.models.Model):

    """Dummy cell model 1"""

    def __init__(self, name=None):
        """Constructor"""

        super(DummyCellModel1, self).__init__(name)
        self.persistent = []
        self.icell = None

    def freeze(self, param_values):
        """Freeze model"""
        pass

    def unfreeze(self, param_names):
        """Freeze model"""
        pass

    def instantiate(self, sim=None):
        """Instantiate cell in simulator"""

        class Cell(object):

            """Empty cell class"""

            def __init__(self):
                """Constructor"""
                self.soma = None
                self.somatic = None

        self.icell = Cell()

        self.icell.soma = [sim.neuron.h.Section(name='soma', cell=self.icell)]
        self.icell.apic = [
            sim.neuron.h.Section(
                name='apic1',
                cell=self.icell)]

        self.icell.somatic = sim.neuron.h.SectionList(
        )  # pylint: disable = W0201
        self.icell.somatic.append(sec=self.icell.soma[0])

        self.icell.apical = sim.neuron.h.SectionList()
        self.icell.apical.append(sec=self.icell.apic[0])

        self.persistent.append(self.icell)
        self.persistent.append(self.icell.soma[0])

        return self.icell

    def destroy(self, sim=None):
        """Destroy cell from simulator"""

        self.persistent = []


class DummyLFPyCellModel1(ephys.models.Model):

    """Dummy LFPy cell model 1"""

    def __init__(self, name=None):
        """Constructor"""

        super(DummyLFPyCellModel1, self).__init__(name)
        self.persistent = []
        self.icell = None
        self.lfpy_cell = None
        self.electrode = None
        self.lfpy_electrode = None

    def freeze(self, param_values):
        """Freeze model"""
        pass

    def unfreeze(self, param_names):
        """Freeze model"""
        pass

    def instantiate(self, sim=None):
        """Instantiate cell in simulator"""
        import LFPy

        class Cell(object):

            """Empty cell class"""

            def __init__(self):
                """Constructor"""
                self.soma = None
                self.somatic = None

        self.icell = Cell()

        self.icell.soma = [sim.neuron.h.Section(name='soma', cell=self.icell)]
        self.icell.apic = [
            sim.neuron.h.Section(
                name='apic1',
                cell=self.icell)]

        self.icell.somatic = sim.neuron.h.SectionList(
        )  # pylint: disable = W0201
        self.icell.somatic.append(sec=self.icell.soma[0])

        self.icell.apical = sim.neuron.h.SectionList()
        self.icell.apical.append(sec=self.icell.apic[0])

        self.persistent.append(self.icell)
        self.persistent.append(self.icell.soma[0])

        self.lfpy_cell = LFPy.Cell(
            morphology=sim.neuron.h.allsec(),
            dt=0.025,
            v_init=-65,
            pt3d=True,
            delete_sections=False,
            nsegs_method=None,
        )

        return self.icell, self.lfpy_cell

    def destroy(self, sim=None):
        """Destroy cell from simulator"""

        self.persistent = []
