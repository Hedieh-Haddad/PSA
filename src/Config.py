import os
import argparse

class Config:
  def __init__(self):
    parser = argparse.ArgumentParser(
                prog = 'HPO-CP',
                description = 'Apply HPO to constraint solvers before solving the instance.')

    parser.add_argument('--model', type=str, required=True, help='The model to run (.py or .mzn)')
    parser.add_argument('--data', type=str, required=False, help='The data file (.dzn)')
    parser.add_argument('--dataparser', type=str, required=False, help='The data parser (.py), only for XCSP3 instances.')
    # parser.add_argument('--format', type=str , required=True, help='The format of problems: Minizinc | XCSP3 .')
    parser.add_argument('--solver', type=str , required=True, help='The backend solver: ace | choco | or-tools .')
    parser.add_argument('--timeout', required=True, type=int, help='The solving timeout in seconds.')
    parser.add_argument('--hpo', required=True, type=str, help='HPO algorithm to apply: None | BayesianOptimisation | GridSearch | MultiArmed | RandomSearch | HyperBand') # | FreeSearch
    parser.add_argument('--rounds', type=int, required=False, help='The number of iterations the HPO algorithm performs. The more iterations, the less time per iterations. Only when --hpo is not `None`.')
    parser.add_argument('--probing_ratio', required=False, type=float, help='If 0.2, 20 percent of the time is dedicated to selecting the best search strategy (probing phase). Only when --hpo is not `None`.')
    parser.add_argument('--search_strategy', required=False, type=str, help='The search strategy to use: UserDefined | FreeSearch | [var]_[val]. `UserDefined` (just MiniZinc) indicates we use the search strategy in the model, if any. `free` means free search. You can use `{var}_` or `_{val}` for using the default variable selection strategy. Only when --hpo is `None`.')
    parser.add_argument('--hyperparameters_restart', required=False, type=str, help='The restart hyperparameters the algorithm will optimise: None | Restart | Full_Restart')
    parser.add_argument('--hyperparameters_search', required=False, type=str, help='The search hyperparameters the algorithm will optimise: None | Only_Var | Only_Val | Simple_Search | Block_Search')

    args = parser.parse_args()
    self.model = args.model
    self.data = args.data
    self.dataparser = args.dataparser
    # self.format = args.format
    self.solver = args.solver
    self.timeout = args.timeout
    self.hpo = args.hpo
    self.probing_ratio = args.probing_ratio
    self.rounds = args.rounds
    self.search_strategy = args.search_strategy
    self.hyperparameters_search = args.hyperparameters_search
    self.hyperparameters_restart = args.hyperparameters_restart

  def print_config(self):
    print(f"%%%%%%mzn-stat: problem_path={self.model}")
    print(f"%%%%%%mzn-stat: data_path={self.data}")
    # print(f"%%%%%%mzn-stat: format={self.format}")
    print(f"%%%%%%mzn-stat: solver={self.solver}")
    print(f"%%%%%%mzn-stat: timeout_ms={self.timeout * 1000}")
    print(f"%%%%%%mzn-stat: hpo={self.hpo}")
    if self.hpo != "none":
      print(f"%%%%%%mzn-stat: probing_ratio={self.probing_ratio}")
      print(f"%%%%%%mzn-stat: rounds={self.rounds}")
      print(f"%%%%%%mzn-stat: hyperparameters_search={self.hyperparameters_search}")
      print(f"%%%%%%mzn-stat: hyperparameters_restart={self.hyperparameters_restart}")
    else:
      print(f"%%%%%%mzn-stat: search_strategy={self.search_strategy}")
