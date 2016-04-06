#!/bin/bash

# Script to run a benchmark optimisation on CSCS viz cluster

LOGFILENAME=logs/l5pc_benchmark.stdout

rm -rf ${LOGFILENAME}

sbatch -A proj37 l5pc_benchmark.sbatch

tail -f --retry ${LOGFILENAME}
