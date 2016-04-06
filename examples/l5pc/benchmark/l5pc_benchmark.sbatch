#!/bin/bash

#SBATCH --ntasks=50
#SBATCH --partition=prod
#SBATCH --job-name=l5pc_benchmark
#SBATCH --time=1-00:00:00
#SBATCH --error=logs/l5pc_benchmark.stdout
#SBATCH --output=logs/l5pc_benchmark.stdout

set -e
set -x

./start.sh
