|banner|

BluePyOpt
=========


+----------------+------------+
| Latest Release | |pypi|     |
+----------------+------------+
| Documentation  | |docs|     |
+----------------+------------+
| License        | |license|  |
+----------------+------------+
| Build Status 	 | |build|    |
+----------------+------------+
| Coverage       | |coverage| |
+----------------+------------+
| Gitter         | |gitter|   |
+----------------+------------+
| Zenodo         | |zenodo|   |
+----------------+------------+


Introduction
============

The Blue Brain Python Optimisation Library (BluePyOpt) is an extensible
framework for data-driven model parameter optimisation that wraps and
standardises several existing open-source tools.

It simplifies the task of creating and sharing these optimisations,
and the associated techniques and knowledge.
This is achieved by abstracting the optimisation and evaluation tasks
into various reusable and flexible discrete elements according to established
best-practices.

Further, BluePyOpt provides methods for setting up both small- and large-scale
optimisations on a variety of platforms,
ranging from laptops to Linux clusters and cloud-based compute infrastructures.

Citation
========

When you use the BluePyOpt software or method for your research, we ask you to cite the following publication (**this includes poster presentations**):

`Van Geit W, Gevaert M, Chindemi G, Rössert C, Courcol J, Muller EB, Schürmann F, Segev I and Markram H (2016). BluePyOpt: Leveraging open source software and cloud infrastructure to optimise model parameters in neuroscience. Front. Neuroinform. 10:17. doi: 10.3389/fninf.2016.00017 <http://journal.frontiersin.org/article/10.3389/fninf.2016.00017>`_.

.. code-block:: 

	@ARTICLE{bluepyopt,
	AUTHOR={Van Geit, Werner  and  Gevaert, Michael  and  Chindemi, Giuseppe  and  Rössert, Christian  and  Courcol, Jean-Denis  and  Muller, Eilif Benjamin  and  Schürmann, Felix  and  Segev, Idan  and  Markram, Henry},   
	TITLE={BluePyOpt: Leveraging open source software and cloud infrastructure to optimise model parameters in neuroscience},
	JOURNAL={Frontiers in Neuroinformatics},
	VOLUME={10},
	YEAR={2016},
	NUMBER={17},
	URL={http://www.frontiersin.org/neuroinformatics/10.3389/fninf.2016.00017/abstract},
	DOI={10.3389/fninf.2016.00017},
	ISSN={1662-5196}
	}


Publications that use or mention BluePyOpt
==========================================
The list of publications that use or mention BluePyOpt can be found on `the github wiki page <https://github.com/BlueBrain/BluePyOpt/wiki/Publications-that-use-or-mention-BluePyOpt>`_.

Support
=======
We are providing support using a chat channel on `Gitter <https://gitter.im/BlueBrain/BluePyOpt>`_, or the `Github discussion page <https://github.com/BlueBrain/BluePyOpt/discussions>`_.

News
====
- 2023/01: BluePyOpt now supports the Arbor simulator.
- 2022/12: Support for LFPy models merged into master. Examples and preprint: https://github.com/alejoe91/multimodalfitting, https://www.biorxiv.org/content/10.1101/2022.08.03.502468v1.full
- 2022/12: BluePyOpt now has the ability to write out NeuroML files: https://github.com/BlueBrain/BluePyOpt/tree/master/bluepyopt/neuroml
- 2021/08/30: BluePyOpt dropped Python 2.7 support.
- 2017/01/04: BluePyOpt is now considered compatible with Python 3.6+.
- 2016/11/10: BluePyOpt now supports NEURON point processes. This means we can fit parameters of Adex/GIF/Izhikevich models, and also synapse models.
- 2016/06/14: Started a wiki: https://github.com/BlueBrain/BluePyOpt/wiki
- 2016/06/07: The BluePyOpt paper was published in Frontiers in Neuroinformatics (for link, see above)
- 2016/05/03: The API documentation was moved to `ReadTheDocs <http://bluepyopt.readthedocs.io/en/latest/>`_
- 2016/04/20: BluePyOpt now contains the code of the IBEA selector, no need to install a BBP-specific version of DEAP anymore
- 2016/03/24: Released version 1.0

Requirements
============

* `Python 3.8+ <https://www.python.org/downloads/release/python-380/>`_
* `Pip <https://pip.pypa.io>`_ (installed by default in newer versions of Python)
* `Neuron 7.4+ <http://neuron.yale.edu/>`_ (compiled with Python support)
* `eFEL eFeature Extraction Library <https://github.com/BlueBrain/eFEL>`_ (automatically installed by pip)
* `Numpy <http://www.numpy.org>`_ (automatically installed by pip)
* `Pandas <http://pandas.pydata.org/>`_ (automatically installed by pip)
* The instruction below are written assuming you have access to a command shell on Linux / UNIX / MacOSX / Cygwin

Installation
============

If you want to use the ephys module of BluePyOpt, you first need to install NEURON with Python support on your machine.

And then bluepyopt itself:


.. code-block:: bash

    pip install bluepyopt

Support for simulators other than NEURON is optional and not installed by default. If you want to use [Arbor](https://arbor-sim.org/) to run your models, use the following line instead to install bluepyopt.

.. code-block:: bash

    pip install bluepyopt[arbor]

Cloud infrastructure
====================

We provide instructions on how to set up an optimisation environment on cloud
infrastructure or cluster computers
`here <https://github.com/BlueBrain/BluePyOpt/tree/master/cloud-config>`_

Quick Start
===========

Single compartmental model
--------------------------

An iPython notebook with an introductory optimisation of a one compartmental
model with 2 HH channels can be found at

https://github.com/BlueBrain/BluePyOpt/blob/master/examples/simplecell/simplecell.ipynb (NEURON)
https://github.com/BlueBrain/BluePyOpt/blob/master/examples/simplecell/simplecell_arbor.ipynb (Arbor)


|landscape_example|


**Figure**: The solution space of a single compartmental model with two parameters: the maximal conductance of Na and K ion channels. The color represents how well the model fits two objectives: when injected with two different currents, the model has to fire 1 and 4 action potential respectively during the stimuli. Dark blue is the best fitness. The blue circles represent solutions with a perfect score.

Neocortical Layer 5 Pyramidal Cell
----------------------------------
Scripts for a more complex neocortical L5PC are in
`this directory <https://github.com/BlueBrain/BluePyOpt/tree/master/examples/l5pc>`__

With a notebook:

https://github.com/BlueBrain/BluePyOpt/blob/master/examples/l5pc/L5PC.ipynb (NEURON)
https://github.com/BlueBrain/BluePyOpt/blob/master/examples/l5pc/L5PC_arbor.ipynb (Arbor)

Thalamocortical Cells
---------------------
Scripts for 2 thalamocortical cell types are in
`this directory <https://github.com/BlueBrain/BluePyOpt/tree/master/examples/thalamocortical-cell>`__

With a notebook:

https://github.com/BlueBrain/BluePyOpt/blob/master/examples/thalamocortical-cell/thalamocortical-cell_opt.ipynb


Tsodyks-Markram Model of Short-Term Plasticity
----------------------------------------------
Scripts for 2 version of fitting the Tsodyks-Markram model to synaptic traces are in
`this directory <https://github.com/BlueBrain/BluePyOpt/tree/master/examples/tsodyksmarkramstp>`__

With 2 notebooks:

https://github.com/BlueBrain/BluePyOpt/blob/master/examples/tsodyksmarkramstp/tsodyksmarkramstp.ipynb
https://github.com/BlueBrain/BluePyOpt/blob/master/examples/tsodyksmarkramstp/tsodyksmarkramstp_multiplefreqs.ipynb

Exporting cell in neuroml format
--------------------------------
An iPython notebook showing how to export a BluePyOpt cell in the neuroml format, how to create a LEMS simulation,
and how to run the LEMS simulation with the neuroml cell can be found at:

https://github.com/BlueBrain/BluePyOpt/blob/master/examples/neuroml/neuroml.ipynb


API documentation
=================
The API documentation can be found on `ReadTheDocs <http://bluepyopt.readthedocs.io/en/latest/>`_.

Funding
=======
This work has been partially funded by the European Union Seventh Framework Program (FP7/2007­2013) under grant agreement no. 604102 (HBP), the European Union’s Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 720270, 785907 (Human Brain Project SGA1/SGA2) and by the EBRAINS research infrastructure, funded from the European Union’s Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 945539 (Human Brain Project SGA3).
This project/research was supported by funding to the Blue Brain Project, a research center of the École polytechnique fédérale de Lausanne (EPFL), from the Swiss government’s ETH Board of the Swiss Federal Institutes of Technology.

Copyright (c) 2016-2022 Blue Brain Project/EPFL

..
    The following image is also defined in the index.rst file, as the relative path is 
    different, depending from where it is sourced.
    The following location is used for the github README
    The index.rst location is used for the docs README; index.rst also defined an end-marker, 
    to skip content after the marker 'substitutions'.

.. |pypi| image:: https://img.shields.io/pypi/v/bluepyopt.svg
               :target: https://pypi.org/project/bluepyopt/
               :alt: latest release

.. |docs| image:: https://readthedocs.org/projects/bluepyopt/badge/?version=latest
               :target: https://bluepyopt.readthedocs.io/
               :alt: latest documentation

.. |license| image:: https://img.shields.io/pypi/l/bluepyopt.svg
                  :target: https://github.com/BlueBrain/bluepyopt/blob/master/LICENSE.txt
                  :alt: license

.. |build| image:: https://github.com/BlueBrain/BluePyOpt/workflows/Build/badge.svg?branch=master
                :target: https://github.com/BlueBrain/BluePyOpt/actions
                :alt: actions build status

.. |coverage| image:: https://codecov.io/github/BlueBrain/BluePyOpt/coverage.svg?branch=master
                   :target: https://codecov.io/gh/BlueBrain/bluepyopt
                   :alt: coverage

.. |gitter| image:: https://badges.gitter.im/Join%20Chat.svg
                 :target: https://gitter.im/BlueBrain/blueptopt
                 :alt: Join the chat at https://gitter.im/BlueBrain/BluePyOpt

.. |zenodo| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.8135890.svg
                :target: https://doi.org/10.5281/zenodo.8135890

.. substitutions
.. |banner| image:: docs/source/logo/BluePyOptBanner.png
.. |landscape_example| image:: examples/simplecell/figures/landscape_example.png
