#!/bin/bash

module load Python/3.11.3-GCCcore-12.3.0
module load parallel/20230722-GCCcore-12.3.0

export PATH=$PATH:/project/scratch/p200244/deps/libminizinc/build
source /project/scratch/p200244/cp-hpo/benchmarks/pybench/bin/activate

