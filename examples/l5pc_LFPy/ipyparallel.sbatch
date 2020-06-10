#!/bin/bash

#SBATCH --constraint=cpu
#SBATCH --ntasks=250
#SBATCH --partition=prod
#SBATCH --job-name=LFPy
#SBATCH --time=0-24:00:00
#SBATCH --error=./logs/%A.stdout
#SBATCH --output=./logs/%A.stdout
#SBATCH --account=proj38

set -e
set -x

#nrnivmodl mechanisms

LOGS=./logs/${SLURM_JOBID}
mkdir -p $LOGS

export IPYTHONDIR=./.ipython
export IPYTHON_PROFILE=benchmark.${SLURM_JOBID}

ipcontroller --init --ip='*' --ping=30000 --profile=${IPYTHON_PROFILE} &
sleep 30
srun --output="${LOGS}/engine.out" ipengine --timeout=300 --profile=${IPYTHON_PROFILE} &
sleep 30

touch ${LOGS}/params.dat
echo ${TYPE_FEATURES} >> ${LOGS}/params.dat

python opt_l5pc.py -v --start --seed=${OPT_SEED} --ipyparallel --feature_set=${FEATURE_SET} --checkpoint="${LOGS}/run.pkl"
