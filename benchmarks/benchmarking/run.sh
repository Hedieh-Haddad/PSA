#!/bin/bash

# Exits when an error occurs.
set -e

# I. Define the campaign to run and hardware information.

TIMEOUT=1200000
VERSION="1.0.0"
NUM_CPUS=2

HARDWARE="\"AMD Epyc ROME 7H12@2.6 GHz [64c/280W]; RAM 256GB\""
HPO_COMMAND="python3 ../../src/main.py --hardware $HARDWARE --timeout $TIMEOUT"
INSTANCE_FILE="mzn2023.csv"
OUTPUT_DIR=$(pwd)"/../campaign/hpo-$(VERSION)"
mkdir -p $OUTPUT_DIR

## II. Gather the list of Slurm nodes to run the experiments on many nodes if available.

if [ -n "${SLURM_JOB_NODELIST}" ]; then
  # get host name
  NODES_HOSTNAME="nodes_hostname.txt"
  scontrol show hostname $SLURM_JOB_NODELIST > $NODES_HOSTNAME
  # Collect public key and accept them
  while read -r node; do
      ssh-keyscan "$node" >> ~/.ssh/known_hosts
  done < "$NODES_HOSTNAME"
  MULTINODES_OPTION="--sshloginfile $NODES_HOSTNAME"
  cp $(realpath "$(dirname "$0")")/slurm.sh $OUTPUT_DIR/
fi

# III. Run the experiments in parallel (one per available CPUs).

DUMP_PY_PATH=$(pwd)/dump.py

cp $0 $OUTPUT_DIR/ # for replicability.
cp $DUMP_PY_PATH $OUTPUT_DIR/

# This experiment tests the various HPO algorithms and parameters of these algorithms.

parallel --no-run-if-empty $MULTINODES_OPTION --rpl '{} uq()' --jobs $NUM_CPUS -k --colsep ',' --skip-first-line \
$HPO_COMMAND --model {2} --data {3} --solver {4} --hpo {5} --rounds {6} --probing_ratio {7} --hyperparameters_restart {8} --hyperparameters_search {9} '|' python3 $DUMP_PY_PATH $OUTPUT_DIR {1} {2} {3} $SOLVER \
:::: $INSTANCE_FILE \
::: "choco" "ace" "ortools" \
::: "BayesianOptimisation" "RandomSearch" "HyperBand" "GridSearch" "MultiArmed" \
::: 10 20 30 40 50 \
::: 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 \
::: "None" "Restart" "Full_Restart" \
::: "None" "Only_Var" "Only_Val" "Simple_Search" "Block_Search"

# This experiment tests the user-defined search and the free search of the solvers.

parallel --no-run-if-empty $MULTINODES_OPTION --rpl '{} uq()' --jobs $NUM_CPUS -k --colsep ',' --skip-first-line \
$HPO_COMMAND --model {2} --data {3} --solver {4} --search_strategy {5} '|' python3 $DUMP_PY_PATH $OUTPUT_DIR {1} {2} {3} $SOLVER \
:::: $INSTANCE_FILE \
::: "choco" "ace" "ortools" \
::: "FreeSearch" "UserDefined"

# TODO: Experiments with XCSP3 on the pickondom and domwdeg.
