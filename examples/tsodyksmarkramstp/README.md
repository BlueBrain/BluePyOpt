# Tsodyks-Markram model examples

The Tsodyks-Markram model of short-term plasticity underwent many changes in the last twenty years.
In this folder we provide 2 examples to fit 2 different versions using BluePyOpt.

`tsodyksmarkramstp.ipynb` numerically integrates the "full version" of the TM model and fits a postsynaptic voltage trace.


`tsodyksmarkramstp_multiplefreqs.ipynb` implements the event-based solution of the (reduced, but) more common version of the TM model and fits amplitudes from multiple stimulation frequencies for better generalization.

