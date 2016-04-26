#!/bin/bash

set -e
set -x 

cd ..

OFFSPRING_SIZE=100
MAX_NGEN=100

export L5PCBENCHMARK_USEIPYP=1
export IPYTHONDIR="`pwd`/.ipython"
export IPYTHON_PROFILE=benchmark.${SLURM_JOBID} 
# ipython profile create --profile=${IPYTHON_PROFILE}
ipcontroller --init --ip='*' --sqlitedb --profile=${IPYTHON_PROFILE} &
sleep 10
srun ipengine --profile=${IPYTHON_PROFILE} &

CHECKPOINTS_DIR="checkpoints/run.${SLURM_JOBID}"
mkdir -p ${CHECKPOINTS_DIR}

pids=""
for seed in `seq 1 4`
do
    BLUEPYOPT_SEED=${seed} python opt_l5pc.py --offspring_size=${OFFSPRING_SIZE} --max_ngen=${MAX_NGEN} --start --checkpoint "${CHECKPOINTS_DIR}/seed${seed}.pkl" &
    pids="${pids} $!"
done

wait $pids
