#!/bin/bash

nrnivmodl ./mechanisms
python opt_l5pc.py --start
