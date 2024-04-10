import json
import traceback
import logging
from main import *
from pathlib import Path

class MinizincSolver:
  def extract_solve_statement(file_path):
    """
    Extracts the solve statement from a .mzn file and separates the rest of the content.

    Parameters:
    - file_path: The path to the .mzn file.

    Returns:
    - A tuple containing two strings: the solve statement and the rest of the file content.
    """
    content = Path(file_path).read_text()
    solve_start = content.find('solve')
    solve_end = content.find(';', solve_start) + 1
    solve_statement = content[solve_start:solve_end]
    rest_content = content[:solve_start] + content[solve_end:]
    return rest_content, solve_statement

  def __init__(self, config):
    self.solver_config = load_config(config)
    self.config = config
    self.model, self.solve_statement = extract_solve_statement(config.model)
    self.blocks = self.extract_blocks()

  def retrieve_all_blocks():
    FetchMethod.fetch_method(self, config, self.solver_config)


  def add_base_options(self, parameters):
    pass

  def add_free_search_options(self, parameters):
    parameters['options']  = ["-f"]

  def add_user_defined_search(self, parameters):
    pass

  def add_options_with_restart(self, config, parameters):
    parameters['restartsequence'] = ["500"]
    if config.hyperparameters_restart == "Full_Restart":
      parameters['geocoef'] = ["1.5"]
    elif config.hyperparameters_restart == "Restart":
      parameters['geocoef'] = ["None"]
    elif config.hyperparameters_restart == "None":
      parameters['restartsequence'] = ["None"]
      parameters['geocoef'] = ["None"]

  def add_timeout_option(self, parameters, timeout):
    parameters['timeout'] = timeout

  def restart_strategies(self, config):
    return self.solver_config['RestartStrategy']

  def variable_strategies(self, config):
    return self.solver_config['parameters']['varh_values']

  def value_strategies(self, config):
    return self.solver_config['parameters']['valh_values']

#################################################################################
  def solve(self, config, parameters):
    # varh = parameters['parameters']['varh_values']
    # valh = parameters['parameters']['valh_values']
    # restart = parameters['RestartStrategy']
    # restartSeq = parameters['restartsequence']
    # geocoef = parameters['geocoef']
    # Block = parameters['blocks']
    varh = "input_order"
    valh = "indomain_median"
    restart = "luby"
    restartSeq = 500
    geocoef = 1.5
    Block = 'Team'
    timeout = round(parameters['timeout'], 3)
    # print(varh, valh, restart, restartSeq, geocoef, Block, timeout)

    if config.hyperparameters_search in ["Simple_Search", "Only_Var", "Only_Val"]:
      model = Model(config.model)
      model.add_file(config.data, parse_data=True)
      print(f'Running with varh={varh}, valh={valh}, restart={restart}, restartsequence={restartSeq} , geocoef={geocoef} , solver={config.solver} , Time={round(timeout, 3)} sec')
      model.add_string(f"varsel = {varh};")
      model.add_string(f"valsel = {valh};")
      solver = Solver.lookup(config.solver)
      instance = Instance(solver, model)


    elif config.hyperparameters_search == "Block_Search":
      rest_elements = " ++ ".join([elem for elem in self.Blocks if elem != Block])
      model = Model(config.model.replace('.mzn', '-strategy.mzn'))
      model.add_file(config.data, parse_data=True)
      solver = Solver.lookup(config.solver)
      instance = Instance(solver, model)
      print(f"{Block}, {varh}, {valh}")
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
      print(f'Running with varh={varh}, valh={valh}, restart={restart}, restartsequence={restartSeq} , geocoef={geocoef} , Block={Block} , solver={config.solver} , Time={round(timeout, 3)} sec')

    if config.search_strategy in ["UserDefined" , "FreeSearch"] or config.hyperparameters_search == "None":
      model = Model(config.model.replace('.mzn', '-free.mzn'))
      model.add_file(config.data, parse_data=True)
      solver = Solver.lookup(config.solver)
      instance = Instance(solver, model)

    try:
      if config.search_strategy == "FreeSearch":
        print(f"Analyze the parameter for FreeSearch.")
        result = instance.solve(timeout=timedelta(seconds=timeout), free_search=True)
      else:
        print(f"Analyze the parameter for {config.hpo}.")
        result = instance.solve(timeout=timedelta(seconds=timeout))

      try:
        objective_result = abs(result.solution.objective)
      except AttributeError:
        objective_result = None
      solvetime = result.statistics.get('solveTime', None)
      if solvetime is not None:
        solvetime = solvetime.total_seconds()
      method = result.statistics['method']
      benchmark_name = self.extract_benchmark(config.model)
      data_name = self.extract_data(config.data)
      print(f"Objective={objective_result}||ElapsedTime={solvetime}||Benchmark={benchmark_name}||Data={data_name}")

      if config.search_strategy == "UserDefined" or config.hyperparameters_search == "None":
        self.final_results_list.append({
          "phase": "Result",
          "mode": config.search_strategy,
          "varh": "Default",
          "valh": "Default",
          "restart": "Default",
          "restartsequence": "Default",
          "geocoef": "Default",
          "block": "Default",
          "Objective": objective_result,
          "ElapsedTime": solvetime,
          "Fraction": timeout,
          "method": method
        })
      elif config.search_strategy == "FreeSearch":
        self.final_results_list.append({
          "phase": "Result",
          "mode": config.search_strategy,
          "varh": "Not-Known",
          "valh": "Not-Known",
          "restart": "Default",
          "restartsequence": "Default",
          "geocoef": "Default",
          "block": "Default",
          "Objective": objective_result,
          "ElapsedTime": solvetime,
          "Fraction": timeout,
          "method": method
        })
      else:
        self.results_list.append({
          "phase": "Probe",
          "mode": config.hpo,
          "varh": varh,
          "valh": valh,
          "restart": restart,
          "restartsequence": restartSeq,
          "geocoef": geocoef,
          "block": Block,
          "Objective": objective_result,
          "ElapsedTime": solvetime,
          "Fraction": timeout,
          "method": method
        })
        if not self.flag:
          self.final_results_list.append({
            "phase": "Probe",
            "mode": config.hpo,
            "varh": varh,
            "valh": valh,
            "restart": restart,
            "restartsequence": restartSeq,
            "geocoef": geocoef,
            "block": Block,
            "Objective": objective_result,
            "ElapsedTime": solvetime,
            "Fraction": timeout,
            "method": method
          })
        if self.flag:
          self.final_results_list.append({
            "phase": "Result",
            "mode": config.hpo,
            "varh": varh,
            "valh": valh,
            "restart": restart,
            "restartsequence": restartSeq,
            "geocoef": geocoef,
            "block": Block,
            "Objective": objective_result,
            "ElapsedTime": solvetime,
            "Fraction": timeout,
            "method": method
          })

    except Exception as e:
      print("Execption raised: " + str(e))
      logging.error(traceback.format_exc())

    self.flag = False
    self.StrategyFlag = False
    if method == "maximize":
      if objective_result is None:
        objective_result = 0
        return objective_result

    elif method == "minimize":
      if objective_result is None:
        objective_result = 10000000000
        return objective_result

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