# BluePyOpt Examples

This directory contains examples of optimizations that can be performed with `BluePyOpt`.
They can be used to learn the concepts behind the package, and also as a starting point for other optimizations

* expsyn: Example optimization of a synapse (a point process) in NEURON

* graupnerbrunelstdp: Graupner-Brunel STDP model fitting

* l5pc: Layer 5 pyramidal neuron parameter optimization

* simplecell: optimisation of simple single compartmental cell with two free parameters

* stochkv: simple cell optimization with stochastic channels

* tsodyksmarkramstp: optimizing parameters of the Tsodyks-Markram model of short-term synaptic plasticity

The expsyn, l5pc and simplecell examples contain an implementation for [Arbor](https://arbor-sim.org/) as an alternative simulator backend to NEURON.

# Documentation

[Parallelization with ipyparallel](BluePyOpt-ipyparallel.md)
