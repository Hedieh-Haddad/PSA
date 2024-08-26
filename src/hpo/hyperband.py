import numpy as np
import random
import sys
import pandas as pd
import numpy as np
from .save_result import save
import time
import math

class HyperBand:
    def geometric_sequence(i):
        return 1.2 * i

    def get_random_configuration(cp_framework):
        parameters = {
            "varh_values": random.choice(list(cp_framework.solver_config["search"]["varh_values"])),
            "valh_values": random.choice(list(cp_framework.solver_config["search"]["valh_values"])),}
        return parameters
    def probe(cp_framework, hyperparameters, ratio_timeout_sec):
        results_list = []
        best_params = {}
        first_non_none_objective = False
        seed = int(time.time())
        seed = 1719576238
        np.random.seed(seed)
        config = cp_framework.config
        best = tell_obj = float('-99999999999') if cp_framework.mode == "maximize" else float('99999999999')
        best_time = None
        none_counter = total_time_used = solve_call_counter = 0
        current_timeout = 5
        luby_index = 0
        initial_timeout = None
        initial_timeout_flag = False
        memo = {}
        memo_flag = False
        max_iter = 27
        eta = 3
        all_combinations = set((varh, valh) for varh in cp_framework.solver_config["search"]["default_varh"] for valh in
                               cp_framework.solver_config["search"]["default_valh"])
        logeta = lambda x: np.log(x) / np.log(eta)
        s_max = int(logeta(max_iter))
        B = (s_max + 1) * max_iter
        counter = B / s_max
        for s in reversed(range(s_max + 1)):
            n = int(np.ceil(int(B / max_iter / (s + 1)) * eta ** s))
            r = max_iter * eta ** (-s)
            parameters = [HyperBand.get_random_configuration(cp_framework) for i in range(n)]
            for i in range(s + 1):
                n_i = n * eta ** (-i)
                r_i = r * eta ** (i)
                if i != 0:
                    current_timeout = HyperBand.geometric_sequence(current_timeout)
                stats = []
                for parameter in parameters:
                    if total_time_used + current_timeout < ratio_timeout_sec and current_timeout != 0:
                        param_tuple = (parameter["varh_values"], parameter["valh_values"])
                        print("current timeout:", current_timeout)
                        parameter.update({"timeout": current_timeout, "seed": seed})
                        if (param_tuple in memo and
                                memo[param_tuple]["objective"] is not None and
                                'timeout' in memo[param_tuple] and
                                memo[param_tuple]['timeout'] == current_timeout):
                            stats = memo[param_tuple]
                            memo_flag = True

                        else:
                            stats = cp_framework.solve(parameter, cp_framework)
                            # memo[param_tuple] = {"objective": stats["objective"], "solveTime": stats["solveTime"]}
                            memo[param_tuple] = {"objective": stats['objective'], "solveTime": stats['solveTime'],"timeout": current_timeout}
                        if all_combinations.issubset(memo.keys()):
                            print("All combinations have been seen. Exiting the loop.")
                            break
                        solve_call_counter += 1
                        if initial_timeout is None and int(stats["solveTime"]) > (
                                current_timeout + 1) and not initial_timeout_flag and not first_non_none_objective:
                            initial_timeout = stats["solveTime"]
                            current_timeout = int(math.ceil(initial_timeout))
                            initial_timeout_flag = True
                        if memo_flag == False:
                            total_time_used += current_timeout
                        elif memo_flag == True:
                            total_time_used += 2
                        parameter.update({"total_time_used": total_time_used})
                        if memo_flag == False:
                            save.print_converted_results(cp_framework, stats, parameter)
                            results = save.append_results(parameter, cp_framework, stats)
                            results_list.append(results)
                        obj = stats["objective"]
                        luby_index += 1
                        if obj is None:
                            obj = tell_obj
                            none_counter += 1
                            if not first_non_none_objective:
                                current_timeout = HyperBand.geometric_sequence(current_timeout)
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
                        stats.update(stats)
                        memo_flag = False
                sorted_indices = np.argsort(stats)
                keys = list(parameter.keys())
                selected_indices = sorted_indices[0:int(n_i / eta)]
                selected_keys = [keys[i] for i in selected_indices]
                new_parameter = {key: parameter[key] for key in selected_keys}
                parameter = new_parameter
                # print(parameter)

        print("123 hyperband",parameters)
        print(results_list)
        cp_framework.flag = True
        best_result = results_list[0]
        best_params["varh_values"] = best_result[0]["varh_values"]
        best_params["valh_values"] = best_result[0]["valh_values"]
        best_params.update({"timeout": config.timeout - total_time_used + 1})
        print(config.timeout - total_time_used + 1)
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
