from Config import *
# from XCSP import *
import random
from hpo.bayesian import Bayesian
# from hpo.multiarmed import MultiArmed
# from hpo.hyperband import HyperBand
# from hpo.grid import Grid
# from hpo.random import Random
from MinizincSolver import *
from XCSP3Solver import *

from skopt.space.space import Real, Integer, Categorical

def make_cp_framework(config):
  if config.model.endswith(".mzn"):
    config.format = "Minizinc"
    return MinizincSolver(config)
  elif config.model.endswith(".py"):
    config.format = "XCSP3"
    return XCSP3Solver(config)
  else:
    print("Unknown model format, we need a .mzn or .py file.")
    exit(1)

def load_config(config):
  with open(f'../solvers/{config.solver}.json', 'r') as f:
    solver_config = json.load(f)
    if config.format in solver_config:
      return solver_config[config.format]
    else:
      print(f"This solver has no {config.format} configuration.")
      exit(1)

def build_search_hyperparameters(cp_framework, hyperparameters):
  config = cp_framework.config
  if config.hyperparameters_search == "Only_Var":
    if config.format == "Minizinc":
      hyperparameters["valh_values"] = ["indomain_median"]
    elif config.format == "XCSP3":
      hyperparameters.pop("valh_values")
    else:
      assert(False)
  elif config.hyperparameters_search == "Only_Val":
    if config.format == "Minizinc":
      hyperparameters["varh_values"] = ["dom_w_deg"]
    elif config.format == "XCSP3":
      hyperparameters.pop("varh_values")
    else:
      assert(False)
  elif config.hyperparameters_search == "None":
    if config.format == "Minizinc":
      print("Minizinc does not support no search annotation in HPO mode. Use free search or user-defined mode instead.")
    hyperparameters.pop("varh_values")
    hyperparameters.pop("valh_values")
  elif config.hyperparameters_search == "Simple_Search":
    hyperparameters.pop("blocks")
  elif config.hyperparameters_search == "Block_Search":
    pass
  else:
    print(f"Unknown --hyperparameters_search value {config.hyperparameters_search}")
    exit(1)

def build_restart_hyperparameters(cp_framework, hyperparameters):
  config = cp_framework.config
  if config.hyperparameters_restart == "None":
    hyperparameters.pop("restart_strategies")
    hyperparameters.pop("restart_sequences")
    hyperparameters.pop("geometric_coefficients")
  elif config.hyperparameters_restart == "Restart":
    hyperparameters.pop("restart_sequences")
    hyperparameters.pop("geometric_coefficients")
  elif config.hyperparameters_restart == "Full_Restart":
    pass
  else:
    print(f"Unknown --hyperparameters_restart value {config.hyperparameters_restart}")
    exit(1)

def build_hyperparameters(cp_framework):
  config = cp_framework.config
  hyperparameters = {
    "varh_values": Categorical(cp_framework.solver_config["search"]["varh_values"]),
    "valh_values": Categorical(cp_framework.solver_config["search"]["valh_values"]),
    "restart_strategies": Categorical(cp_framework.solver_config["restart_strategies"]),
    "restart_sequences": Integer(100, 1000),
    "geometric_coefficients": Real(1.1, 2.0)
  }
  nblocks = cp_framework.num_blocks()
  if nblocks > 1:
    hyperparameters["blocks"] = Integer(0, nblocks-1)
  elif config.hyperparameters_search == "Block_Search":
    print("This model has no block to optimize, so you should use the option `--hyperparameters_search Simple_Search` instead.")
    exit(1)
  build_search_hyperparameters(cp_framework, hyperparameters)
  build_restart_hyperparameters(cp_framework, hyperparameters)
  return hyperparameters

def probe(cp_framework):
  config = cp_framework.config
  if config.probing_ratio > 1.0 or config.probing_ratio < 0.0:
    print("The probing ratio must be between 0.0 and 1.0.")
    exit(1)
  probe_timeout_sec = config.timeout * config.probing_ratio
  hyperparameters = build_hyperparameters(cp_framework)
  if config.hpo == "bayesian":
    return Bayesian.probe(cp_framework, hyperparameters, probe_timeout_sec)
  # elif config.hpo == "grid":
  #   return Grid(cp_framework).probe(hyperparameters, probe_timeout_sec)
  # elif config.hpo == "multiarmed":
  #   return MultiArmed(cp_framework).probe(hyperparameters, probe_timeout_sec)
  # elif config.hpo == "random":
  #   return Random(cp_framework).probe(hyperparameters, probe_timeout_sec)
  # elif config.hpo == "hyperband":
  #   return HyperBand(cp_framework).probe(hyperparameters, probe_timeout_sec)
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
  if config.search_strategy == "UserDefined":
    if config.format != 'Minizinc':
      print("The UserDefined search strategy is only valid for MiniZinc models.")
      exit(1)
    # No option to add when we use the user-defined search strategy.
  elif config.search_strategy == "FreeSearch":
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

def print_json(statistics):
  print("""{"type": "statistics", "statistics": """ + str(statistics) + "}")

def main():
  random.seed()
  config = Config()
  cp_framework = make_cp_framework(config)
  parameters = configure_parameters(cp_framework)
  print_json(cp_framework.solve(parameters))

if __name__ == "__main__":
  main()
