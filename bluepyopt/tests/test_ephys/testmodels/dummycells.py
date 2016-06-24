"""Dummy cell model used for testing"""

import bluepyopt.ephys as ephys


class DummyCellModel1(ephys.models.Model):

    """Dummy cell model 1"""

    def __init__(self, name=None):
        """Constructor"""

        super(DummyCellModel1, self).__init__(name)
        self.persistent = []

    def instantiate(self, sim=None):
        """Instantiate cell in simulator"""

        class Cell(object):

            """Empty cell class"""
            pass

        icell = Cell()

        soma = sim.neuron.h.Section(name='soma', cell=icell)

        icell.somatic = sim.neuron.h.SectionList()  # pylint: disable = W0201
        icell.somatic.append(sec=soma)

        self.persistent.append(icell)
        self.persistent.append(soma)

        return icell

    def destroy(self, sim=None):
        """Destroy cell from simulator"""

        self.persistent = []
