[![Build Status](https://travis-ci.org/BlueBrain/BluePyOpt.svg?branch=master)](https://travis-ci.org/BlueBrain/BluePyOpt)
[![codecov.io](https://codecov.io/github/BlueBrain/BluePyOpt/coverage.svg?branch=master)](https://codecov.io/github/BlueBrain/BluePyOpt?branch=master)
[![Join the chat at https://gitter.im/BlueBrain/BluePyOpt](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/BlueBrain/BluePyOpt?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Code Climate](https://codeclimate.com/github/BlueBrain/BluePyOpt/badges/gpa.svg)](https://codeclimate.com/github/BlueBrain/BluePyOpt)
 [![Binder](http://mybinder.org/badge.svg)](http://mybinder.org/repo/BlueBrain/BluePyOpt)

Introduction
============

The Blue Brain Python Optimisation Library (BluePyOpt) is an extensible framework for data-driven model parameter optimisation that wraps and standardises several existing open-source tools. It simplifies the task of creating and sharing these optimisations, and the associated techniques and knowledge. This is achieved by abstracting the optimisation and evaluation tasks into various reusable and flexible discrete elements according to established best-practices. Further, BluePyOpt provides methods for setting up both small- and large-scale optimisations on a variety of platforms, ranging from laptops to Linux clusters and cloud-based compute infrastructures. 

Citation
========

When you use the BluePyOpt software or method for your research, we ask you to cite the following Arxiv preprint in your publications:

[Van Geit, W., M. Gevaert, G. Chindemi, C. Rössert, J.-D. Courcol, E. Muller, F. Schürmann, I. Segev, and H. Markram (2016, March). BluePyOpt: Leveraging open source software and cloud infrastructure to optimise model parameters in neuroscience. ArXiv e-prints.](http://arxiv.org/abs/1603.00500)

```bibtex
@ARTICLE{bluepyopt,
   author = {{Van Geit}, W. and {Gevaert}, M. and {Chindemi}, G. and {R{\"o}ssert}, C. and 
	{Courcol}, J.-D. and {Muller}, E. and {Sch{\"u}rmann}, F. and 
	{Segev}, I. and {Markram}, H.},
    title = "{BluePyOpt: Leveraging open source software and cloud infrastructure to optimise model parameters in neuroscience}",
  journal = {ArXiv e-prints},
archivePrefix = "arXiv",
   eprint = {1603.00500},
 primaryClass = "q-bio.NC",
 keywords = {Quantitative Biology - Neurons and Cognition},
     year = 2016,
    month = mar
}
```

News
====
- 2016/04/20: BluePyOpt now contains the code of the IBEA selector, no need to install a BBP-specific version of DEAP anymore
- 2016/03/24: Released version 1.0

Requirements
============

* [Python 2.7+](https://www.python.org/download/releases/2.7/)
* [Pip](https://pip.pypa.io) (installed by default in newer versions of Python)
* [BlueBrain version of DEAP](https://github.com/BlueBrain/deap)
* [Neuron 7.4](http://neuron.yale.edu/) (compiled with Python support)
* [eFEL eFeature Extraction Library](https://github.com/BlueBrain/eFEL) (automatically installed by pip)
* [Numpy](http://www.numpy.org) (automatically installed by pip)
* [Pandas](http://pandas.pydata.org/) (automatically installed by pip)
* The instruction below are written assuming you have access to a command shell
on Linux / UNIX / MacOSX / Cygwin

Installation
============

If you want to use the ephys module of BluePyOpt, you first need to install Neuron with Python support on your machine.

And then bluepyopt itself:

```bash
pip install bluepyopt
```

Cloud infrastructure
====================

We provide instruction on how to set up an optimisation environment on cloud
infrastructure or cluster computers 
[here](https://github.com/BlueBrain/BluePyOpt/tree/master/cloud-config)

Quick Start
===========

Single compartmental model
--------------------------

An iPython notebook with an introductory optimisation of a one compartmental 
model with 2 HH channels can be found at

https://github.com/BlueBrain/BluePyOpt/blob/master/examples/simplecell/simplecell.ipynb

There is a Binder Virtual Machine available that allows you to run this notebook in your browser:

http://mybinder.org/repo/BlueBrain/BluePyOpt/examples/simplecell/simplecell.ipynb

![Landscape example](https://github.com/BlueBrain/BluePyOpt/blob/master/examples/simplecell/figures/landscape_example.png)
**Figure**: The solution space of a single compartmental model with two parameters: the maximal conductance of Na and K ion channels. The color represents how well the model fits two objectives: when injected with two different currents, the model has to fire 1 and 4 action potential respectively during the stimuli. Dark blue is the best fitness. The blue circles represent solutions with a perfect score.

Neocortical Layer 5 Pyramidal Cell
----------------------------------
Scripts for a more complex neocortical L5PC are in 
[this directory](https://github.com/BlueBrain/BluePyOpt/tree/master/examples/l5pc)

With a notebook:

https://github.com/BlueBrain/BluePyOpt/blob/master/examples/l5pc/L5PC.ipynb

And you can run this in a VM:

http://mybinder.org/repo/BlueBrain/BluePyOpt/examples/l5pc/L5PC.ipynb

API documentation
==================
The API documentation can be found [here](http://bluebrain.github.io/BluePyOpt)
