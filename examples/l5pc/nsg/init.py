"""Run BluePyOpt on Neuroscience Gateway"""

import os

os.system('pip install efel --user')

os.system('pip install bluepyopt --upgrade --user')

os.system('nrnivmodl mechanisms')

import sys
sys.argv = ['opt_l5pc.py', '--start']
os.system('./opt_l5pc.py --start')
