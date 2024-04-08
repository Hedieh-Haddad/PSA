from minizinc import Instance, Model, Solver
from datetime import timedelta
import traceback
import logging
import re

class SolveMinizinc:
    def BlockSolveStrategy(self, varh, valh, restart, restartSeq, geocoef, Block):
        print(f'Running with varh={varh}, valh={valh}, restart={restart}, restartsequence={restartSeq} , geocoef={geocoef} , Block={Block} , solver={self.solver} , Time={round(self.result_timeout_sec, 3)} sec')
        rest_elements = " ++ ".join([elem for elem in self.Blocks if elem != Block])
        # print(f"Block of variables with the ({Block},{varh}, {valh})")
        # print(f"\t \t \t ({rest_elements}, {varh}, {valh})")
        model = Model(self.model.replace('.mzn', '-strategy.mzn'))
        model.add_file(self.data, parse_data=True)

        if self.mode == "GridSearch":
            self.result_timeout_sec = self.probe_timeout_sec / (
                    (len(self.parameters['varh_values']) * len(
                        self.parameters['valh_values']) * len(self.RestartStrategy) * len(
                        self.restartsequence) * len(self.geocoef) * len(self.Blocks)))
        elif self.mode in ["BayesianOptimisation", "RandomSearch", "MultiArmed", "HyperBand"]:
            self.result_timeout_sec = self.probe_timeout_sec / (self.rounds)

        if self.flag:
            self.result_timeout_sec = self.global_timeout_sec - self.probe_timeout_sec
        solver = Solver.lookup(self.solver)
        instance = Instance(solver, model)

        if len(self.Blocks) == 1:
            solve_item = "solve ::seq_search([\n"
            solve_item += f"    int_search( {Block}, {varh}, {valh}, complete )])\n"
            solve_item += f"{self.method} objective;"
            instance.add_string(solve_item)
        elif len(self.Blocks) > 1:
            solve_item = "solve ::seq_search([\n"
            solve_item += f"    int_search( {Block}, {varh}, {valh}, complete )\n"
            solve_item += f"    int_search( {rest_elements}, {varh}, {valh}, complete )])\n"
            solve_item += f"{self.method} objective;"
            instance.add_string(solve_item)

        benchmark_name = self.extract_benchmark(self.model)
        data_name = self.extract_data(self.data)
        try:
            # objective_result = None
            result = instance.solve(timeout=timedelta(seconds=round(self.result_timeout_sec, 3)))
            try:
                objective_result = abs(result.solution.objective)

            except AttributeError:
                objective_result = None
            solvetime = result.statistics.get('solveTime', None)
            if solvetime is not None:
                solvetime = solvetime.total_seconds()
            nodes = result.statistics.get('nodes', None)
            print(f"Objective={objective_result}||ElapsedTime={solvetime}||Benchmark={benchmark_name}||Data={data_name}||Mode={self.mode}")

            self.results_list.append({
                "phase": "Probe",
                "mode": self.mode,
                "varh": varh,
                "valh": valh,
                "restart": restart,
                "restartsequence": restartSeq,
                "geocoef": geocoef,
                "block": Block,
                "Objective": objective_result,
                "ElapsedTime": solvetime,
                "Fraction": self.result_timeout_sec,
                "method": self.method
            })
            if not self.flag:
                self.final_results_list.append({
                    "phase": "Probe",
                    "mode": self.mode,
                    "varh": varh,
                    "valh": valh,
                    "restart": restart,
                    "restartsequence": restartSeq,
                    "geocoef": geocoef,
                    "block": Block,
                    "Objective": objective_result,
                    "ElapsedTime": solvetime,
                    "Fraction": self.result_timeout_sec,
                    "method": self.method
                })
            if self.flag:
                self.final_results_list.append({
                    "phase": "Result",
                    "mode": self.mode,
                    "varh": varh,
                    "valh": valh,
                    "restart": restart,
                    "restartsequence": restartSeq,
                    "geocoef": geocoef,
                    "block": Block,
                    "Objective": objective_result,
                    "ElapsedTime": solvetime,
                    "Fraction": self.result_timeout_sec,
                    "method": self.method
                })

        except Exception as e:
            print("Execption raised: " + str(e))
            logging.error(traceback.format_exc())

        self.flag = False
        self.StrategyFlag = False
        if self.method == "maximize":
            if objective_result is None:
                objective_result = 0
                return objective_result

        elif self.method == "minimize":
            if objective_result is None:
                objective_result = 10000000000
                return objective_result



    def solveStrategy(self, varh, valh, restart, restartSeq, geocoef):
        model = Model(self.model)
        model.add_file(self.data, parse_data=True)
        if self.mode == "GridSearch":
            self.result_timeout_sec = self.probe_timeout_sec / (
                    (len(self.parameters['varh_values']) * len(
                        self.parameters['valh_values']) * len(self.RestartStrategy) * len(
                        self.restartsequence) * len(self.geocoef)))
        elif self.mode in ["BayesianOptimisation", "RandomSearch", "MultiArmed", "HyperBand"]:
            self.result_timeout_sec = self.probe_timeout_sec / (self.rounds)
        if self.flag:
            self.result_timeout_sec = self.global_timeout_sec - self.probe_timeout_sec

        print(f'Running with varh={varh}, valh={valh}, restart={restart}, restartsequence={restartSeq} , geocoef={geocoef} , solver={self.solver} , Time={round(self.result_timeout_sec, 3)} sec')

        model.add_string(f"varsel = {varh};")
        model.add_string(f"valsel = {valh};")
        solver = Solver.lookup(self.solver)
        instance = Instance(solver, model)

        benchmark_name = self.extract_benchmark(self.model)
        data_name = self.extract_data(self.data)
        # print(self.config.result_timeout_sec)
        try:
            objective_result = None
            result = instance.solve(timeout=timedelta(seconds=round(self.result_timeout_sec, 3)))
            # print("resultttttttttt", result)
            try:
                objective_result = abs(result.solution.objective)
            except AttributeError:
                objective_result = None
            solvetime = result.statistics.get('solveTime', None)
            if solvetime is not None:
                solvetime = solvetime.total_seconds()
            nodes = result.statistics.get('nodes', None)
            print(f"Objective={objective_result}||ElapsedTime={solvetime}||Benchmark={benchmark_name}||Data={data_name}||Mode={self.mode}")
            # print(f"Objective={objective_result}||Nodes={nodes}||SolveTime={solvetime}||Method={self.method}||Benchmark={benchmark_name}||DZN={data_name}||Mode={self.mode}||Fraction={self.f}")

            self.results_list.append({
                "phase": "Probe",
                "mode": self.mode,
                "varh": varh,
                "valh": valh,
                "restart": restart,
                "restartsequence": restartSeq,
                "geocoef": geocoef,
                # "block": Block,
                "Objective": objective_result,
                "ElapsedTime": solvetime,
                "Fraction": self.result_timeout_sec,
                "method": self.method
            })
            if not self.flag:
                self.final_results_list.append({
                    "phase": "Probe",
                    "mode": self.mode,
                    "varh": varh,
                    "valh": valh,
                    "restart": restart,
                    "restartsequence": restartSeq,
                    "geocoef": geocoef,
                    # "block": Block,
                    "Objective": objective_result,
                    "ElapsedTime": solvetime,
                    "Fraction": self.result_timeout_sec,
                    "method": self.method
                })
            if self.flag:
                self.final_results_list.append({
                    "phase": "Result",
                    "mode": self.mode,
                    "varh": varh,
                    "valh": valh,
                    "restart": restart,
                    "restartsequence": restartSeq,
                    "geocoef": geocoef,
                    # "block": Block,
                    "Objective": objective_result,
                    "ElapsedTime": solvetime,
                    "Fraction": self.result_timeout_sec,
                    "method": self.method
                })

        except Exception as e:
            print("Execption raised: " + str(e))
            logging.error(traceback.format_exc())

        self.flag = False
        self.StrategyFlag = False
        if self.method == "maximize":
            if objective_result is None:
                objective_result = 0
                return objective_result

        elif self.method == "minimize":
            if objective_result is None:
                objective_result = 10000000000
                return objective_result


    def solvefree(self):
        print(f"Analyze the parameter for FreeSearch.")
        model = Model(self.model.replace('.mzn', '-free.mzn'))
        model.add_file(self.data, parse_data=True)
        solver = Solver.lookup(self.solver)
        instance = Instance(solver, model)
        free_search_timeout_sec = self.global_timeout_sec

        try:
          result = instance.solve(timeout=timedelta(seconds=free_search_timeout_sec), free_search=True)
          objective_result = result.solution.objective
          solvetime = result.statistics['solveTime'].total_seconds()
          # nodes = result.statistics['nodes']
          method = result.statistics['method']

          print(f"  Objective={objective_result}   |   SolveTime={solvetime}")

          self.final_results_list.append({
              "phase": "Result",
              "mode": self.mode,
              "varh": "Not-Known",
              "valh": "Not-Known",
              "restart": "Default",
              "restartsequence": "Default",
              "geocoef": "Default",
              "block": "Default",
              "Objective": objective_result,
              "ElapsedTime": solvetime,
              "Fraction": self.result_timeout_sec,
              "method": self.method
          })

        except Exception as e:
          print("Execption raised: " + str(e))
          logging.error(traceback.format_exc())



    def Defaultsolve(self):
        print(f"Analyze the parameter for MiniZinc Default.")
        model = Model(self.model.replace('.mzn', '-free.mzn'))
        model.add_file(self.data, parse_data=True)
        solver = Solver.lookup(self.solver)
        instance = Instance(solver, model)

        try:
          result = instance.solve(timeout=timedelta(seconds=self.global_timeout_sec))
          objective_result = result.solution.objective
          solvetime = result.statistics['solveTime'].total_seconds()
          # nodes = result.statistics['nodes']
          method = result.statistics['method']
          print(f"  Objective={objective_result}   |   SolveTime={solvetime}")

          self.final_results_list.append({
              "phase": "Result",
              "mode": self.mode,
              "varh": "Default",
              "valh": "Default",
              "restart": "Default",
              "restartsequence": "Default",
              "geocoef": "Default",
              "block": "Default",
              "Objective": objective_result,
              "ElapsedTime": solvetime,
              "Fraction": self.result_timeout_sec,
              "method": method
          })

        except Exception as e:
          print("Execption raised: " + str(e))
          logging.error(traceback.format_exc())

    def extract_benchmark(self, path):
        match = re.search(r'benchmarks/(.*?)/', path)
        if match:
            return match.group(1)
        return None

    def extract_data(self, path):
        match = re.search(r'/([^/]*)\.dzn', path)
        if match:
            return match.group(1)
        return None