#!/bin/bash

export TOPDIR=$(pwd)
export FEATURE_SET='extra'

for seed in {1..2}; do
    
    export OPT_SEED=${seed}

    mkdir .ipython
    mkdir logs
    sbatch ipyparallel.sbatch

done

