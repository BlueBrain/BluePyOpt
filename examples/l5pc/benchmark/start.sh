#!/bin/bash

set -e
set -x

PWD=$(pwd)
LOGS=$PWD/logs
mkdir -p $LOGS

cd ..

OFFSPRING_SIZE=100
MAX_NGEN=100

export IPYTHONDIR=${PWD}/.ipython
export IPYTHON_PROFILE=benchmark.${SLURM_JOBID}

ipcontroller --init --ip='*' --sqlitedb --ping=30000 --profile=${IPYTHON_PROFILE} &
sleep 10
srun --output="${LOGS}/engine_%j_%2t.out" ipengine --timeout=300 --profile=${IPYTHON_PROFILE} &
sleep 10

CHECKPOINTS_DIR="checkpoints/run.${SLURM_JOBID}"
mkdir -p ${CHECKPOINTS_DIR}

pids=""
for seed in {1..4}; do
    python opt_l5pc.py                     \
        -vv                                \
        --offspring_size=${OFFSPRING_SIZE} \
        --max_ngen=${MAX_NGEN}             \
        --seed=${seed}                     \
        --ipyparallel                      \
        --start                            \
        --checkpoint "${CHECKPOINTS_DIR}/seed${seed}.pkl" &
    pids+="$! "
done

wait $pids
