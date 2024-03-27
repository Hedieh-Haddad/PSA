import os
import argparse
import multiprocessing
class Config:
  """Configuration class for the multi-objective constraint programming.
     It parses the commandline arguments and initializes the temporary and result directories."""
  def __init__(self):
    parser = argparse.ArgumentParser(
                prog = 'XCSP',
                description = 'Run models with different parameters.')
    parser.add_argument('-model', type=str, required=True, help='The model to run')
    parser.add_argument('-data', type=str, required=False, help='The data file')
    parser.add_argument('-dataparser', type=str, required=False, help='The data parser')
    # parser.add_argument('-solver_name', type=str , required=True)
    parser.add_argument('-global_timeout_sec', required=True, type=int)
    # parser.add_argument('-probe_timeout_sec', required=True, type=int)
    parser.add_argument('-rounds', type=int, required=True)
    # parser.add_argument('-SArounds', type=int, required=True)
    # parser.add_argument('-free_search', required=False, action='store_true', default=False)
    args = parser.parse_args()

    self.model = args.model
    self.data = args.data
    self.dataparser = args.dataparser
    # self.solver_name = args.solver_name
    self.global_timeout_sec = int(args.global_timeout_sec)
    # self.probe_timeout_sec = int(args.probe_timeout_sec)
    self.rounds = args.rounds
    # self.SArounds = args.SArounds
    # self.free_search = args.free_search
  def init_statistics(self, statistics):
    statistics["model"] = self.model
    statistics["data"] = self.data
    statistics["dataparser"] = self.dataparser
    # statistics["solver_name"] = self.solver_name
    statistics["global_timeout_sec"] = self.global_timeout_sec
    # statistics["probe_timeout_sec"] = self.probe_timeout_sec
    statistics["rounds"] = self.rounds
    # statistics["SArounds"] = self.SArounds
    # statistics["free_search"] = self.free_search
  def uid(self):
    """Unique identifier for this experiment."""
    return self.model + str(self.global_timeout_sec)



