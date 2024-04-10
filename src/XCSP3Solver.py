import json
import traceback
import logging
from main import *
from fetchmethod import *
import signal
import subprocess
import pandas as pd
import time
import glob
import os
import math
import re
import json


class XCSP3Solver:
  def __init__(self, config):
    self.final_results_list = []
    self.results_list = []
    self.flag = False
    probe_timeout_sec = config.timeout * config.probing_ratio
    with open(f'solvers/{config.solver}.json', 'r') as f:
      solver_config = json.load(f)
      if 'XCSP3' in solver_config:
        xcsp_config = solver_config['XCSP3']

    if config.hyperparameters_search == "Only_Var":
      self.add_timeout_option(xcsp_config, probe_timeout_sec)
      self.add_options_with_value_selection(xcsp_config, "indomain_median")
      # xcsp_config['parameters']['valh_values'] = "indomain_median"

    elif config.hyperparameters_search == "Only_Val":
      self.add_timeout_option(xcsp_config, probe_timeout_sec)
      self.add_options_with_variable_selection(xcsp_config, "dom_w_deg")
      # xcsp_config['parameters']['varh_values'] = "dom_w_deg"

    elif config.hyperparameters_search == "Simple_Search":
        if config.search_strategy in ['{var}_', '_{val}']:
            print("The --hyperparameters_search option is not compatible with --search_strategy.")
            exit(1)
        self.add_timeout_option(xcsp_config, probe_timeout_sec)
        self.variable_strategies(config)
        self.value_strategies(config)

    elif config.hyperparameters_search == "None":
      self.add_timeout_option(xcsp_config, probe_timeout_sec)
      config.search_strategy = "[var]_[val]"

    if config.hpo == "None":
        if config.hyperparameters_search == "None":
            if config.search_strategy in ['{var}_', '_{val}']:
                self.add_timeout_option(xcsp_config, probe_timeout_sec)
                if config.solver == "choco":
                    self.add_options_with_variable_selection(xcsp_config, "PICKONDOM0")
                elif config.solver == "ace":
                    self.add_options_with_variable_selection(xcsp_config, "PickOnDom")
                if config.solver == "choco":
                    self.add_options_with_value_selection(xcsp_config, "MED")
                elif config.solver == "ace":
                    self.add_options_with_value_selection(xcsp_config, "Dist")


    if config.hyperparameters_restart == "None":
      xcsp_config['RestartStrategy'] = ["None"]
      self.add_options_with_restart(config, xcsp_config)

    elif config.hyperparameters_restart in ["Restart", "Full_Restart"]:
      self.restart_strategies(config)
      self.add_options_with_restart(config, xcsp_config)

    self.solve(config, xcsp_config)

  def add_free_search_options(self, parameters):
    parameters['options'] = ["-f"]
    # self.parameters['options'] = ["-f"]

  def add_options_with_value_selection(self, parameters, value_strategy):
    if value_strategy in parameters['parameters']['valh_values']:
      parameters['parameters']['valh_values'] = value_strategy
    else:
      print(f"Value strategy {value_strategy} is not available for this solver.")
      exit(1)

  def add_options_with_variable_selection(self, parameters, variable_strategy):
    if variable_strategy in parameters['parameters']['varh_values']:
      parameters['parameters']['varh_values'] = variable_strategy
    else:
      print(f"Variable strategy {variable_strategy} is not available for this solver.")
      exit(1)

  def add_options_with_search(self, parameters, value_strategy, variable_strategy):
    if value_strategy in parameters['parameters']['valh_values']:
      if variable_strategy in parameters['parameters']['varh_values']:
        parameters['parameters']['valh_values'] = value_strategy
        parameters['parameters']['varh_values'] = variable_strategy
      else:
        print(f"Variable strategy {variable_strategy} is not available for this solver.")
        exit(1)
    else:
      print(f"Value strategy {value_strategy} is not available for this solver.")
      exit(1)
    # self.add_options_with_value_selection(parameters, value_strategy)
    # self.add_options_with_variable_selection(parameters, variable_strategy)

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
    with open(f'solvers/{config.solver}.json', 'r') as f:
      solver_config = json.load(f)
      if 'XCSP3' in solver_config:
        xcsp_config = solver_config['XCSP3']
    return xcsp_config['RestartStrategy']

  def variable_strategies(self, config):
    with open(f'solvers/{config.solver}.json', 'r') as f:
      solver_config = json.load(f)
      if 'XCSP3' in solver_config:
        xcsp_config = solver_config['XCSP3']
    return xcsp_config['parameters']['varh_values']

  def value_strategies(self, config):
    with open(f'solvers/{config.solver}.json', 'r') as f:
      solver_config = json.load(f)
      if 'XCSP3' in solver_config:
        xcsp_config = solver_config['XCSP3']
    return xcsp_config['parameters']['valh_values']

  #################################################################################
  def solve(self, config, parameters):
    # varh = parameters['parameters']['varh_values']
    # valh = parameters['parameters']['valh_values']
    # restart = parameters['RestartStrategy']
    # restartSeq = parameters['restartsequence']
    # geocoef = parameters['geocoef']
    varh = "PickOnDom"
    valh = "Dist"
    restart = "luby"
    restartsequence = 500
    geocoef = 1.5
    timeout = round(parameters['timeout'], 3)
    # print(varh, valh, restart, restartSeq, geocoef, timeout)

    n_solutions, bound, status, solution = None , None , None , None
    signal.setitimer(signal.ITIMER_REAL, timeout, 0)

    if config.search_strategy == "FreeSearch":
      print(f"Analyze the parameters for FreeSearch.")
      config.model = config.model.split(".")[0]
      cmd = ["python3", f"benchmarks/data/modelsXCSP22/COP/{config.model}/{config.model}.py"]
      if config.data:
          cmd.append(f"-data=benchmarks/data/modelsXCSP22/COP/{config.model}/{config.data}")
      if config.dataparser:
          cmd.append(f"-dataparser=benchmarks/data/modelsXCSP22/COP/{config.model}/{config.dataparser}")
      if config.solver == "ace":
          cmd.extend([f"-solver=[ace] -luby -r_n=500 "])
      elif config.solver == "choco":
          cmd.extend(["-f ", f"-solver=[choco,v] -best -last -lc 1 -restarts [luby,500,0,50000,true]"])
    else:
      print(f'Running hpo={config.hpo} with varh={varh}, valh={valh}, restart={restart}, restartsequence={restartsequence} , geocoef={geocoef} , solver={config.solver} , Time={timeout} sec')
      with open('datavarval.txt', 'w') as f:
          f.write(f'{varh}\n')
          f.write(f'{valh}\n')
          f.write(f'{config.solver}\n')
          f.write(f'{restart}\n')
          f.write(f'{restartsequence}\n')
          f.write(f'{geocoef}\n')
      config.model = config.model.split(".")[0]
      cmd = ["python3", f"benchmarks/data/modelsXCSP22/COP/{config.model}/{config.model}.py"]
      if config.data:
          cmd.append(f"-data=benchmarks/data/modelsXCSP22/COP/{config.model}/{config.data}")
      if config.dataparser:
          cmd.append(f"-dataparser=benchmarks/data/modelsXCSP22/COP/{config.model}/{config.dataparser}")
    start_time = time.time()
    try:
        output = subprocess.run(cmd, universal_newlines=True, text=True, capture_output=True)
        end_time = time.time()
        elapsed_time = end_time - start_time
        elapsed_time = round(elapsed_time, 3)
        n_solutions, bound, status, solution = self.parse_output(output)
        log_files = glob.glob('*.log')
        if log_files:
            latest_log_file = max(log_files, key=os.path.getctime)
            with open(latest_log_file, 'r') as log_file:
                content = log_file.read()
                lines = content.splitlines()
                if lines:
                    if config.solver == 'choco':
                        last_line = lines[-1]
                        components = last_line.split()
                        if len(components) == 3 and components[0] == 'o':
                            bound = components[1]
                    elif config.solver == 'ace':
                        for line in lines:
                            stripped_line = line.strip()
                            if stripped_line.startswith('effs'):
                                pattern = r'effs:(\d+)\s+revisions:\((\d+),useless=(\d+)\)\s+ngds:(\d+)'
                                matches = re.search(pattern, stripped_line)
                                if matches:
                                    effs = int(matches.group(1))
                                    revisions = int(matches.group(2))
                                    useless = int(matches.group(3))
                                    nogoods = int(matches.group(4))
                            elif stripped_line.startswith('d WRONG DECISIONS'): #Extract the number of wrong decisions from the lines that start with 'd WRONG DECISIONS' for calculation of rewards
                                words = line.split()
                                wrongdecision = int(words[-1])
        if config.search_strategy != "FreeSearch":
          try:
              self.reward = (math.log2(wrongdecision)) / (math.log2(nogoods + useless))
          except:
              self.reward = None
    except TimeoutError:
        end_time = time.time()
        elapsed_time = end_time - start_time
        elapsed_time = round((elapsed_time - 0.01), 3)

    self.NSolution = n_solutions
    self.Objective = bound
    self.Status = status
    self.Solution = solution
    self.ElapsedTime = elapsed_time
    print(f"Objective={bound}||ElapsedTime={elapsed_time}||Benchmark={config.model}||Data={config.data}")

    if config.search_strategy == "FreeSearch":
        self.final_results_list.append({
            "phase": "Result",
            "mode": config.search_strategy,
            "varh": "Not-Knonw",
            "valh": "Not-Knonw",
            "restart": "Default",
            "restartsequence": "Default",
            "geocoef": "Default",
            "Objective": bound,
            "ElapsedTime": elapsed_time,
            "Fraction": timeout
        })

    else:
        self.results_list.append({
            "phase": "Probe",
            "mode": config.hpo,
            "varh": varh,
            "valh": valh,
            "restart": restart,
            "restartsequence": restartsequence,
            "geocoef": geocoef,
            "Objective": bound,
            "ElapsedTime": elapsed_time,
            "Fraction": timeout
        })
        if not self.flag:
            self.final_results_list.append({
                "phase": "Probe",
                "mode": config.hpo,
                "varh": varh,
                "valh": valh,
                "restart": restart,
                "restartsequence": restartsequence,
                "geocoef": geocoef,
                "Objective": bound,
                "ElapsedTime": elapsed_time,
                "Fraction": timeout
            })
        if self.flag:
            self.final_results_list.append({
                "phase": "Result",
                "mode": config.hpo,
                "varh": varh,
                "valh": valh,
                "restart": restart,
                "restartsequence": restartsequence,
                "geocoef": geocoef,
                "Objective": bound,
                "ElapsedTime": elapsed_time,
                "Fraction": timeout
            })
    signal.alarm(0)

    self.flag = False
    if bound is None:
        bound = 10000000000
    return bound

  def parse_output(self, output):
      if output == None:
          n_solutions, bound, status, solution = None, None, None, None
          return n_solutions, bound, status, solution
      lines = output.stdout.split('\n')
      n_solutions, bound, status, solution = None , None , None , None
      for line in lines:
          if line.startswith("NSolution"):
              n_solutions = int(line.split()[1]) if line.split()[1] != 'None' else None
          elif line.startswith("Objective"):
              bound = int(line.split()[1]) if line.split()[1] != 'None' else None
          elif line.startswith("Status"):
              status = line.split()[1]
          elif line.startswith("Solution"):
              solution = line.split()[1]
      return n_solutions, bound, status, solution
