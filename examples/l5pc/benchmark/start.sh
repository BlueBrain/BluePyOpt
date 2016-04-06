#!/bin/bash

set -e
set -x 

cd ..

export IPYTHONDIR="`pwd`/.ipython"
export IPYTHON_PROFILE=benchmark.${SLURM_JOBID} 
# ipython profile create --profile=${IPYTHON_PROFILE}
ipcontroller --init --ip='*' --sqlitedb --profile=${IPYTHON_PROFILE} &
sleep 10
srun ipengine --profile=${IPYTHON_PROFILE} &

python opt_l5pc.py --start
