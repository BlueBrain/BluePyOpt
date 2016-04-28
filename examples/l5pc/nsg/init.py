"""Run BluePyOpt on Neuroscience Gateway"""

import os

os.system('pip install efel --user')

os.system('pip install bluepyopt --upgrade --user')

# os.system('nrnivmodl mechanisms')

os.system('python opt_l5pc.py --start')
