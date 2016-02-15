[![Build Status](https://travis-ci.org/BlueBrain/BluePyOpt.svg?branch=master)](https://travis-ci.org/BlueBrain/BluePyOpt)

Introduction
============

BlueBrain Python Optimisation Library

This software is currently in an *ALPHA* stage. Use at your own risk.

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
pip install git+git://github.com/BlueBrain/BluePyOpt
```

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
