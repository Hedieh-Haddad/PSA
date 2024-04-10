import sys
from skopt import Optimizer
from skopt.utils import point_asdict, dimensions_aslist
import numpy as np

class Bayesian:
  def probe(cp_framework, hyperparameters, probe_timeout_sec):
    config = cp_framework.config
    # Initialize the optimizer with the given hyperparameters and a Gaussian Process (GP) as the base estimator.
    opt = Optimizer(dimensions=dimensions_aslist(hyperparameters), base_estimator="GP")
    for i in range(self.rounds):
      params = opt.ask()
      parameters = point_asdict(hyperparameters, params) # Extract the parameters from dictionary
      cp_framework.add_base_options(parameters)
      cp_framework.add_timeout_option(parameters, probe_timeout_sec / config.rounds)
      results = cp_framework.solve(parameters)
      obj = results["objective"]
      if obj is None:
        obj = 1000000000
      if results["method"] == "maximize":
        obj = -obj
      output = opt.tell(params, obj)
      # if len(output.func_vals) >= 4 and (tuple(output.func_vals[-1:]) == tuple(output.func_vals[-2:-1])) and (
      #         tuple(output.func_vals[-2:-1]) == tuple(output.func_vals[-3:-2])) and (
      #         tuple(output.func_vals[-3:-2]) == tuple(output.func_vals[-4:-3])):
      #     if len(output.x_iters) >= 4 and (tuple(output.x_iters[-1:]) == tuple(output.x_iters[-2:-1])) and (
      #             tuple(output.x_iters[-2:-1]) == tuple(output.x_iters[-3:-2])) and (
      #             tuple(output.x_iters[-3:-2]) == tuple(output.x_iters[-4:-3])):
      #         break
    best_params = point_asdict(hyperparameters, opt.Xi[np.argmin(opt.yi)])
    return best_params
