import sys
from skopt import Optimizer
from skopt.utils import point_asdict, dimensions_aslist
import numpy as np

class Bayesian:
  def probe(cp_framework, hyperparameters, probe_timeout_sec):
    config = cp_framework.config
    # Initialize the optimizer with the given hyperparameters and a Gaussian Process (GP) as the base estimator.
    opt = Optimizer(dimensions=dimensions_aslist(hyperparameters), base_estimator="GP")
    best = -1000000000 if cp_framework.mode == "maximize" else 1000000000
    for i in range(config.rounds):
      params = opt.ask()
      parameters = point_asdict(hyperparameters, params) # Extract the parameters from dictionary
      parameters["timeout"] = probe_timeout_sec / config.rounds
      stats = cp_framework.solve(parameters)
      print("""{"type": "probe", "statistics": """ + str(stats) + "}")
      obj = stats["objective"]
      if obj is None:
        obj = 1000000000
      else:
        if cp_framework.mode == "maximize" and best < obj:
          best = obj
        if cp_framework.mode == "minimize" and best > obj:
          best = obj
      obj = -obj if cp_framework.mode == "maximize" else obj
      output = opt.tell(params, obj)
      # if len(output.func_vals) >= 4 and (tuple(output.func_vals[-1:]) == tuple(output.func_vals[-2:-1])) and (
      #         tuple(output.func_vals[-2:-1]) == tuple(output.func_vals[-3:-2])) and (
      #         tuple(output.func_vals[-3:-2]) == tuple(output.func_vals[-4:-3])):
      #     if len(output.x_iters) >= 4 and (tuple(output.x_iters[-1:]) == tuple(output.x_iters[-2:-1])) and (
      #             tuple(output.x_iters[-2:-1]) == tuple(output.x_iters[-3:-2])) and (
      #             tuple(output.x_iters[-3:-2]) == tuple(output.x_iters[-4:-3])):
      #         break
    best_params = point_asdict(hyperparameters, opt.Xi[np.argmin(opt.yi)])
    best_params["timeout"] = config.timeout - probe_timeout_sec
    best_params["best_bound"] = best
    return best_params
