import os
import argparse

class Config:
  def __init__(self):
    parser = argparse.ArgumentParser(
                prog = 'HPO-CP',
                description = 'Apply HPO to constraint solvers before solving the instance.')

    parser.add_argument('--model', type=str, required=True, help='The model to run (.py or .mzn)')
    parser.add_argument('--data', type=str, required=False, help='The data file (.dzn or .json)')
    parser.add_argument('--dataparser', type=str, required=False, help='The data parser (.py), only for XCSP3 instances.')

    parser.add_argument('--solver', type=str , required=True, help='The backend solver: choco | or-tools .')
    parser.add_argument('--timeout', required=True, type=int, help='The solving timeout in seconds.')

    parser.add_argument('--hpo', required=False, default="None", type=str, help='HPO algorithm to apply: Bayesian_Optimisation ')
    parser.add_argument('--search_strategy', required=False, type=str, help='The search strategy to use: Free_Search.')

    parser.add_argument('--rounds', type=int, required=False, help='The number of iterations the HPO algorithm performs. The more iterations, the less time per iterations.')
    parser.add_argument('--probing_ratio', required=False, type=float, help='If 0.2, 20 percent of the time is dedicated to selecting the best search strategy (probing phase).')
    # parser.add_argument('--hyperparameters_search', required=False, type=str, default="None", help='The search hyperparameters the algorithm will optimise: Simple_Search | Block_Search')

    args = parser.parse_args()
    self.model = args.model
    self.data = args.data
    self.dataparser = args.dataparser

    self.solver = args.solver
    self.timeout = args.timeout
    if args.rounds is not None:
      self.rounds = args.rounds # 30
    # elif args.rounds is None:
    #   self.rounds = 30
    if args.probing_ratio is not None:
      self.probing_ratio = args.probing_ratio # 0.2
    elif args.probing_ratio is None:
      self.probing_ratio = 0.2
    self.hpo = args.hpo
    self.search_strategy = args.search_strategy

  def print_config(self):
    print(f"%%%%%%mzn-stat: problem_path={self.model}")
    print(f"%%%%%%mzn-stat: data_path={self.data}")
    print(f"%%%%%%mzn-stat: solver={self.solver}")
    print(f"%%%%%%mzn-stat: timeout_ms={self.timeout * 1000}")
    if self.hpo != "None":
      print(f"%%%%%%mzn-stat: probing_ratio={self.probing_ratio}")
      print(f"%%%%%%mzn-stat: rounds={self.rounds}")
      print(f"%%%%%%mzn-stat: hyperparameters_search={self.hyperparameters_search}")
    else:
      print(f"%%%%%%mzn-stat: search_strategy={self.search_strategy}")
