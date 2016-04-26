#!/bin/bash

set -e
set -x 

cd ..

export L5PCBENCHMARK_USEIPYP=1
export IPYTHONDIR="`pwd`/.ipython"
export IPYTHON_PROFILE=benchmark.${SLURM_JOBID} 
# ipython profile create --profile=${IPYTHON_PROFILE}
ipcontroller --init --ip='*' --quiet --sqlitedb --profile=${IPYTHON_PROFILE} &
sleep 10
srun ipengine --profile=${IPYTHON_PROFILE} &

CHECKPOINTS_DIR="checkpoints/run.${SLURM_JOBID}"
mkdir -p ${CHECKPOINTS_DIR}

pids=""
for seed in `seq 1 4`
do
    BLUEPYOPT_SEED=${seed} python opt_l5pc.py --start --checkpoint "${CHECKPOINTS_DIR}/seed${seed}.pkl" &
    pids="${pids} $!"
done

wait $pids
