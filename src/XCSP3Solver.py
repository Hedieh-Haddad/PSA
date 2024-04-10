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
    self.solver_config = load_config(config)
    self.config = config

    self.solve(config, self.solver_config)

  def add_base_options(self, parameters):
    parameters['options'].setdefault([])
    if config.solver == "ace":
      parameters['options'].add(f"-solver=[ace]")
    elif config.solver == "choco":
      parameters['options'].add(f"-solver=[choco,v] -best -last -lc 1")

  def add_free_search_options(self, parameters):
    parameters['options'].setdefault([])
    parameters['options'].add("-f")
    if config.solver == "ace":
      parameters['options'].add(f"-solver=[ace] -luby -r_n=500 ")
    elif config.solver == "choco":
      parameters['options'].add(f"-solver=[choco,v] -best -last -lc 1 -restarts [luby,500,0,50000,true]")

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
