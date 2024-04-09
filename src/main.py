from Config import *
from XCSP import *
import random
from hpo.bayesian import Bayesian
from hpo.multiarmed import MultiArmed
from hpo.hyperband import HyperBand
from hpo.grid import Grid
from hpo.random import Random
from fetchmethod import FetchMethod

def make_cp_framework(config):
  if config.model.endswith(".mzn"):
    return MinizincSolver(config)
  else if config.model.endswith(".py"):
    return XCSP3Solver(config)
  else:
    print("Unknown model format, we need a .mzn or .py file.")
    exit(1)

def probe(config, cp_framework):
  if config.probing_ratio > 1.0 or config.probing_ratio < 0.0:
    print("The probing ratio must be between 0.0 and 1.0.")
    exit(1)
  probe_timeout_sec = config.timeout * config.probing_ratio
  if config.hpo == "BayesianOptimisation":
    return Bayesian(config, cp_framework).probe(probe_timeout_sec)
  else if config.hpo == "GridSearch":
    return Grid(config, cp_framework).probe(probe_timeout_sec)
  else if config.hpo == "MultiArmed":
    return MultiArmed(config, cp_framework).probe(probe_timeout_sec)
  else if config.hpo == "RandomSearch":
    return Random(config, cp_framework).probe(probe_timeout_sec)
  else if config.hpo == "HyperBand":
    return HyperBand(config, cp_framework).probe(probe_timeout_sec)
  else:
    print("Unknown HPO method, please see the options.")
    exit(1)

def hyperparameters_from(config, cp_framework):
  parameters = {}
  if config.search_strategy == "UserDefined":
    if not config.model.endswith(".mzn"):
      print("The UserDefined search strategy is only valid for MiniZinc models.")
      exit(1)
  else if config.search_strategy == "FreeSearch":
    cp_framework.add_free_search_options(parameters)
  else:
    if config.search_strategy.startswith('_'):
      cp_framework.add_options_with_value_selection(parameters, config.search_strategy[1:])
    else if config.search_strategy.endswith('_'):
      cp_framework.add_options_with_variable_selection(parameters, config.search_strategy[:-1])
    else:
      search = config.search_strategy.split('_')
      if len(options) != 2:
        print("Invalid format of the search strategy: must be [var]_[val].")
        exit(1)
      cp_framework.add_options_with_search(parameters, search[0], search[1])
  cp_framework.add_timeout_option(parameters, config.timeout)
  return parameters

def main():
  random.seed()
  config = Config()
  cp_framework = make_cp_framework(config)
  if config.hpo == "None":
    if config.search_strategy == None:
      print("The --search_strategy option is mandatory when a HPO method is not specified.")
      exit(1)
    parameters = hyperparameters_from(config, cp_framework)
    cp_framework.solve(parameters).print()
  else:
    if config.search_strategy != None:
      print("The --hpo option is not compatible with --search_strategy (you either guess the search strategy with HPO or use an existing one).")
      exit(1)
    best_parameters = probe(config, cp_framework)
    cp_framework.solve(best_parameters).print()

if __name__ == "__main__":
  main()
