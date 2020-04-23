"""Run BluePyOpt on Neuroscience Gateway"""

import os

os.system('python opt_l5pc.py --start --max_ngen=100 '
          '--offspring_size=50 --checkpoint checkpoint.pkl')
