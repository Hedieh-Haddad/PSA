import math
import numpy as np
import pandas as pd
import itertools
import random
from .save_result import save
import time


class Grid:
    def geometric_sequence(i):
        return 1.2 * i
    def probe(cp_framework, hyperparameters, ratio_timeout_sec):
        results_list = []
        best_params = {}
        first_non_none_objective = False
        seed = int(time.time())
        random.seed(seed)
        np.random.seed(seed)
        config = cp_framework.config
        print(config.timeout)
        best = tell_obj = float('-99999999999') if cp_framework.mode == "maximize" else float('99999999999')
        best_time = None
        none_counter = total_time_used = solve_call_counter = 0
        current_timeout = 5
        luby_index = 0
        initial_timeout = None
        initial_timeout_flag = False
        memo = {}
        memo_flag = False
        all_combination = set((varh, valh) for varh in cp_framework.solver_config["search"]["default_varh"] for valh in
                               cp_framework.solver_config["search"]["default_valh"])
        all_combinations = list(itertools.product(cp_framework.solver_config["search"]["varh_values"], cp_framework.solver_config["search"]["valh_values"]))
        # while total_time_used + current_timeout < ratio_timeout_sec and current_timeout != 0:
        for varh_values, valh_values in all_combinations:
            current_timeout = config.timeout
            print("current timeout:", current_timeout)
            parameters = {
                "varh_values": varh_values,
                "valh_values": valh_values,
            }
            parameters.update({"timeout": current_timeout})
            parameters.update({"seed": seed})
            param_tuple = (parameters["varh_values"], parameters["valh_values"])
            if (param_tuple in memo and
                    memo[param_tuple]["objective"] is not None and
                    'timeout' in memo[param_tuple] and
                    memo[param_tuple]['timeout'] == current_timeout):
                stats = memo[param_tuple]
                memo_flag = True
            else:
                stats = cp_framework.solve(parameters, cp_framework)
                memo[param_tuple] = {"objective": stats["objective"], "solveTime": stats["solveTime"]}
            if all_combination.issubset(memo.keys()):
                print("All combinations have been seen. Exiting the loop.")
                break
            solve_call_counter += 1
            if initial_timeout is None and stats["solveTime"] > (
                    current_timeout + 1) and not initial_timeout_flag and not first_non_none_objective:
                initial_timeout = stats["solveTime"]
                current_timeout = int(math.ceil(initial_timeout))
                initial_timeout_flag = True
            if memo_flag == False:
                total_time_used += current_timeout
            elif memo_flag == True:
                total_time_used += 2
            print(total_time_used)
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
                if not first_non_none_objective:
                    current_timeout = Grid.geometric_sequence(current_timeout)
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
                if ratio_timeout_sec - total_time_used > 0:
                    current_timeout = int(ratio_timeout_sec - total_time_used - 1)
            memo_flag = False
        cp_framework.flag = True
        results_list.sort(
            key=lambda x: (
                -x[1] if cp_framework.mode == "maximize" else x[1],
                x[2] if cp_framework.mode == "maximize" else -x[2] if x[2] is not None else float('inf')
            )
        )
        best_result = results_list[0]
        best_params["varh_values"] = best_result[0]["varh_values"]
        best_params["valh_values"] = best_result[0]["valh_values"]
        best_params.update({"timeout": config.timeout - total_time_used + 1})
        best_params.update({"varh_fallback": "None", "valh_fallback": "None"})
        best_params.update({"varh_bayesian": "None", "valh_bayesian": "None"})
        if cp_framework.solver_config["search"]["default_varh"] == best_params["varh_values"] and \
                cp_framework.solver_config["search"]["default_valh"] == best_params["valh_values"]:
            best_params.update(
                {"varh_bayesian": best_params["varh_values"], "valh_bayesian": best_params["valh_values"]})
        if none_counter == solve_call_counter:
            best_params["varh_values"] = "Solver_Default"
            best_params["valh_values"] = "Solver_Default"
            best_params["varh_fallback"] = "Solver_Default"
            best_params["valh_fallback"] = "Solver_Default"
        best_params.update({"seed": seed})
        return best_params
