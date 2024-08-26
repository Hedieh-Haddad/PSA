from Config import *
import random
from pathlib import Path
from hpo.bayesian import Bayesian
from hpo.hyperband import HyperBand
from hpo.random import Random
from hpo.grid import Grid
from hpo.save_result import *
from MinizincSolver import *
from XCSP3Solver import *
from ResultCollection import *
from skopt.space.space import Real, Integer, Categorical

def make_cp_framework(config):
  if config.model.endswith(".fzn") or config.model.endswith(".mzn"):
  # if config.model.endswith(".mzn"):
    config.format = "Minizinc"
    return MinizincSolver(config)
  # elif config.model.endswith(".fzn"):
  elif config.model.endswith(".xml"):
    config.format = "XCSP3"
    return XCSP3Solver(config)
  else:
    print("Unknown model format, we need a .mzn or .py file")
    exit(1)

def build_hyperparameters(cp_framework):
  hyperparameters = {
    "varh_values": Categorical(cp_framework.solver_config["search"]["varh_values"]),
    "valh_values": Categorical(cp_framework.solver_config["search"]["valh_values"]),
    "blocks": "",
  }
  if cp_framework.config.format == "Minizinc":
    nblocks = cp_framework.num_blocks()
    if nblocks > 1:
      hyperparameters["blocks"] = Integer(0, nblocks-1)
    elif nblocks <= 1:
      hyperparameters.pop("blocks")
  elif cp_framework.config.format == "XCSP3":
    hyperparameters.pop("blocks")
  return hyperparameters

def probe(cp_framework):
  cp_framework.flag = False
  config = cp_framework.config
  if config.probing_ratio > 1.0 or config.probing_ratio < 0.0:
    print("The probing ratio must be between 0.0 and 1.0.")
    exit(1)
  probe_timeout_sec = config.timeout * config.probing_ratio
  hyperparameters = build_hyperparameters(cp_framework)
  if config.hpo == "Bayesian":
    return Bayesian.probe(cp_framework, hyperparameters, probe_timeout_sec)
  elif config.hpo == "Hyperband":
    return HyperBand.probe(cp_framework, hyperparameters, probe_timeout_sec)
  elif config.hpo == "Random":
    return Random.probe(cp_framework, hyperparameters, probe_timeout_sec)
  elif config.hpo == "Grid":
    return Grid.probe(cp_framework, hyperparameters, probe_timeout_sec)
  else:
    print("Unknown HPO method, please see the options.")
    exit(1)

def add_variable_selection_strategy(cp_framework, parameters, varh):
  if varh not in cp_framework.solver_config["search"]["varh_values"]:
    print("This variable selection strategy is not supported by the current solver.")
    exit(1)
  parameters["varh"] = varh

def add_value_selection_strategy(cp_framework, parameters, valh):
  if valh not in cp_framework.solver_config["search"]["valh_values"]:
    print("This value selection strategy is not supported by the current solver.")
    exit(1)
  parameters["valh"] = valh

def hyperparameters_from(config, cp_framework):
  parameters = {}
  parameters["timeout"] = config.timeout
  parameters["rounds"] = config.rounds
  parameters["probing_ratio"] = config.probing_ratio
  if config.search_strategy == "UserDefined":
    if config.format != 'Minizinc':
      print("The UserDefined search strategy is only valid for MiniZinc models.")
      exit(1)
  elif config.search_strategy == "FreeSearch":
    cp_framework.flag = True
    pass
  else:
    if config.search_strategy.startswith('_'):
      add_value_selection_strategy(cp_framework, parameters, config.search_strategy[1:])
    elif config.search_strategy.endswith('_'):
      add_variable_selection_strategy(cp_framework, parameters, config.search_strategy[:-1])
    else:
      search = config.search_strategy.split('_')
      if len(options) != 2:
        print("Invalid format of the search strategy: must be [var]_[val].")
        exit(1)
      add_variable_selection_strategy(cp_framework, parameters, search[0])
      add_value_selection_strategy(cp_framework, parameters, search[1])
  return parameters

def configure_parameters(cp_framework):
  config = cp_framework.config
  if config.hpo == "None":
    if config.search_strategy == "None":
      print("The --search_strategy option is mandatory when a HPO method is not specified.")
      exit(1)
    return hyperparameters_from(config, cp_framework)
  else:
    if config.search_strategy != None:
      print("The --hpo option is not compatible with --search_strategy (you either guess the search strategy with HPO or use an existing one).")
      exit(1)
    return probe(cp_framework)

def main():
  random.seed()
  config = Config()
  cp_framework = make_cp_framework(config)
  parameters= configure_parameters(cp_framework)
  if config.probing_ratio != 1 or config.search_strategy == "FreeSearch":
    statistics= cp_framework.solve(parameters, cp_framework)
    save.print_converted_results(cp_framework, statistics, parameters)
  ResultCollection.analysis(parameters,config)

if __name__ == "__main__":
  main()
