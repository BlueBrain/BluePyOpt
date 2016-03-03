[![Build Status](https://travis-ci.org/BlueBrain/BluePyOpt.svg?branch=master)](https://travis-ci.org/BlueBrain/BluePyOpt)
[![codecov.io](https://codecov.io/github/BlueBrain/BluePyOpt/coverage.svg?branch=master)](https://codecov.io/github/BlueBrain/BluePyOpt?branch=master)
[![Join the chat at https://gitter.im/BlueBrain/BluePyOpt](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/BlueBrain/BluePyOpt?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Code Climate](https://codeclimate.com/github/BlueBrain/BluePyOpt/badges/gpa.svg)](https://codeclimate.com/github/BlueBrain/BluePyOpt)

Introduction
============

BlueBrain Python Optimisation Library

Citation
========

When you use the BluePyOpt software or method for your research, we ask you to cite the following paper in your publications:

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

After installing Neuron and DEAP, run the following command:

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

An iPython notebook with an introductory optimisation of a one compartmental 
model with 2 HH channels can be found 
[here](https://github.com/BlueBrain/BluePyOpt/blob/master/examples/simplecell/simplecell.ipynb)

Scripts for a more complex neocortical L5PC are in 
[this directory](https://github.com/BlueBrain/BluePyOpt/tree/master/examples/l5pc)

API documentation
==================
The API documentation can be found [here](http://bluebrain.github.io/BluePyOpt)
