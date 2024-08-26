import sys
import pandas as pd
from skopt import Optimizer
from skopt.utils import point_asdict, dimensions_aslist
import numpy as np
from .save_result import save
import time
import math

class Bayesian:
  def geometric_sequence(i):
    return 1.2 * i
  def luby_sequence(i , current_timeout, timeout_list):
    timeout_list.append(current_timeout)
    sequence = [timeout_list[0]]
    while len(sequence) <= i:
      sequence += sequence + [2*sequence[-1]]
    return sequence[i]
  def probe(cp_framework, hyperparameters, ratio_timeout_sec):
    results_list = []
    first_non_none_objective = False
    seed = int(time.time())
    # seed = 1719576238
    np.random.seed(seed)
    config = cp_framework.config
    opt = Optimizer(dimensions=dimensions_aslist(hyperparameters), base_estimator="GP", acq_func="EI")
    best = tell_obj = float('-99999999999') if cp_framework.mode == "maximize" else float('99999999999')
    best_time = None
    none_counter = total_time_used = solve_call_counter = 0
    current_timeout = 5
    luby_index = 0
    initial_timeout = None
    initial_timeout_flag = False
    memo = {}
    memo_flag = False
    all_combinations = set((varh, valh) for varh in cp_framework.solver_config["search"]["default_varh"] for valh in cp_framework.solver_config["search"]["default_valh"])
    while total_time_used + current_timeout < ratio_timeout_sec and current_timeout != 0:
      memo_flag = False
      print("current timeout:", current_timeout)
      params = opt.ask()
      parameters = point_asdict(hyperparameters, params) if total_time_used != 0 else {
        "varh_values": cp_framework.solver_config["search"]["default_varh"],
        "valh_values": cp_framework.solver_config["search"]["default_valh"],
      }
      parameters.update({"timeout": current_timeout})
      parameters.update({"seed": seed})
      ########################################################################################################
      param_tuple = (parameters["varh_values"], parameters["valh_values"])
      if (param_tuple in memo and memo[param_tuple]["objective"] is not None and 'timeout' in memo[param_tuple] and
              memo[param_tuple]['timeout'] == current_timeout):
        # print("I'm hereeeeeeeeeeeeeeeee")
        # print(parameters["varh_values"], parameters["valh_values"])
        stats = memo[param_tuple]
        memo_flag = True

      else:
        stats = cp_framework.solve(parameters, cp_framework)
        memo[param_tuple] = {"objective": stats["objective"], "solveTime": stats["solveTime"],
                             "timeout": current_timeout}
########################################################################################################
      if all_combinations.issubset(memo.keys()):
        print("All combinations have been seen. Exiting the loop.")
        break
      solve_call_counter += 1
      if initial_timeout is None and stats["solveTime"] > (current_timeout + 1) and not initial_timeout_flag and not first_non_none_objective:
        initial_timeout = stats["solveTime"]
        current_timeout = int(math.ceil(initial_timeout))
        initial_timeout_flag = True
      if memo_flag == False:
        total_time_used += current_timeout
      elif memo_flag == True:
        total_time_used += 2
      # print(total_time_used)
      parameters.update({"total_time_used": total_time_used})
      if memo_flag == False:
        save.print_converted_results(cp_framework, stats, parameters)
        results = save.append_results(parameters, cp_framework, stats)
        results_list.append(results)
      obj = stats["objective"]
      luby_index += 1
      if obj is None:
        obj = tell_obj
        none_counter += 1
        if not first_non_none_objective :
          current_timeout = Bayesian.geometric_sequence(current_timeout)
      else:
        obj = int(obj)
        first_non_none_objective = True
        if cp_framework.mode == "maximize":
          if obj > best or (obj == best and (best_time is None or stats["solveTime"] < best_time)):
            best = obj
            best_time = stats["solveTime"]
        else:
          if obj < best or (obj == best and (best_time is None or stats["solveTime"] < best_time)):
            best = obj
            best_time = stats["solveTime"]
      if total_time_used + current_timeout > ratio_timeout_sec:
        if ratio_timeout_sec - total_time_used > 0 :
          current_timeout = int(ratio_timeout_sec - total_time_used-1)
      obj = -obj if cp_framework.mode == "maximize" else obj
      opt.tell(params, obj)
    cp_framework.flag = True
    # save.save_results_to_csv(results_list, cp_framework)
    best_params = point_asdict(hyperparameters, opt.Xi[np.argmin(opt.yi)])
    best_params.update({"timeout": config.timeout - total_time_used +1})
    best_params.update({"varh_fallback": "None", "valh_fallback": "None"})
    best_params.update({"varh_bayesian": "None", "valh_bayesian": "None"})
    if cp_framework.solver_config["search"]["default_varh"] == best_params["varh_values"] and cp_framework.solver_config["search"]["default_valh"] == best_params["valh_values"]:
      best_params.update({"varh_bayesian": best_params["varh_values"], "valh_bayesian": best_params["valh_values"]})
    if none_counter == solve_call_counter:
      best_params["varh_values"] = "Solver_Default"
      best_params["valh_values"] = "Solver_Default"
      best_params["varh_fallback"] = "Solver_Default"
      best_params["valh_fallback"] = "Solver_Default"
    best_params.update({"seed": seed})
    best_params.update({"probing_ratio": config.probing_ratio})
    return best_params
