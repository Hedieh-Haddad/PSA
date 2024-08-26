import json
import traceback
import logging
import re
from main import *
from pathlib import Path
from datetime import timedelta
from pyparsing import Word, alphas, alphanums, nestedExpr, Group, OneOrMore
from pyparsing import *
import regex
from ResultCollection import *


class MinizincSolver:
  def extract_solve_statement(self):
    """
    Extracts the solve statement from a .mzn file and separates the rest of the content.
    """
    content = Path(self.config.model).read_text()
    lines = content.split('\n')
    lines = [line for line in lines if not line.strip().startswith('%')]
    content = '\n'.join(lines)
    pattern = r"(solve\s*::.*?;)"
    matches = re.findall(pattern, content, re.DOTALL)
    if matches:
      self.solve_statement = matches[0]
      self.model = content.replace(self.solve_statement, '')
    else:
      print("No solve statement found in the model.")

  def extract_blocks(self):
    def find_matching_parenthesis(s, start):
      depth = 0
      for i in range(start, len(s)):
        if s[i] == '(':
          depth += 1
        elif s[i] == ')':
          depth -= 1
          if depth == 0:
            return i
      return -1

    def split_params(params):
      parts = []
      depth = 0
      start = 0
      for i, char in enumerate(params):
        if char == '[' or char == '(':
          depth += 1
        elif char == ']' or char == ')':
          depth -= 1
        elif char == ',' and depth == 0:
          parts.append(params[start:i].strip())
          start = i + 1
      parts.append(params[start:].strip())
      return parts
    pattern = re.compile(r'((?:bool|int)_search)\s*\(', re.DOTALL)
    pos = 0
    while pos < len(self.solve_statement):
      match = pattern.search(self.solve_statement, pos)
      if not match:
        break
      function_name = match.group(1)
      start = match.end()
      end = find_matching_parenthesis(self.solve_statement, start - 1)
      if end == -1:
        break
      params = self.solve_statement[start:end].strip()
      params = split_params(params)
      block = [function_name] + params
      self.blocks.append(tuple(block))
      pos = end + 1

  def extract_optimisation_statement(self):
    self.mode = 'minimize'
    optim = self.solve_statement.find(self.mode)
    if optim == -1:
      self.mode = 'maximize'
      optim = self.solve_statement.find(self.mode)
      if optim == -1:
        print("This is not an optimisation problem (no minimize or maximize statement).")
        exit(1)
    self.optimisation_statement = self.solve_statement[optim:].strip()[:-1]
    self.optimisation_variable = self.optimisation_statement[len('minimize'):].strip()

  def __init__(self, config):
    self.new_constraint = ""
    self.solver_config = ResultCollection.load_config(config)
    self.config = config
    self.extract_solve_statement()
    self.extract_optimisation_statement()
    self.blocks = []
    self.result = {}
    self.extract_blocks()

  def num_blocks(self):
    return len(self.blocks)

  def add_free_search_options(self, parameters):
    parameters['options']  = ["-f"]

  def build_varh(self, parameters):
    if "varh_values" in parameters:
      return parameters["varh_values"]
    else:
      return "first_fail"

  def build_valh(self, parameters):
    if "valh_values" in parameters:
      return parameters["valh_values"]
    else:
      return "indomain_min"

  def build_variables(self, parameters):
    if "blocks" in parameters:
      i = parameters["blocks"]
      return (self.blocks[i][0], self.blocks[i][1])
    else:
      return ("int_search", " ++ ".join([ b[1] for b in self.blocks if b[0] == "int_search"]))

  def build_restart(self, parameters):
    if parameters["restart_strategies"] == "geometric":
      return "restart_linear(100)"
    if parameters["restart_strategies"] == "luby":
      return "restart_luby(100)"

  def better_bound_constraint(self, parameters):
    if 'best_bound' in parameters:
      op = ">" if self.mode == "maximize" else "<"
      self.new_constraint = f"\nconstraint {self.optimisation_variable} {op} {parameters['best_bound']};\n"
      return self.new_constraint
    else:
      return ""

  def parse_output(self, output):
      bound = None
      solver_solve_time = None
      lines = output
      csv_SolveTime = 0
      csv_objective = 0
      if lines:
          if self.config.solver == 'choco':
              o_lines = [line for line in lines if line.startswith('o')]
              if o_lines:
                  last_o_line = o_lines[-1]
                  components = last_o_line.split()
                  if len(components) >= 2:
                      bound = components[1]
              s_lines = [line for line in lines if line.startswith('s')]
              if s_lines:
                  last_s_line = s_lines[-1]
                  components = last_s_line.split(';')
                  if len(components) >= 6:
                      csv_SolveTime = float(components[2])
                      csv_objective = int(components[5])
                  components = last_s_line.split()
                  if len(components) >= 3:
                      solver_solve_time = components[2]
      else:
          print("No lines in the output.")
      return bound, solver_solve_time, csv_SolveTime

  def solve_(self, parameters, cp_framework):
    output_lines = []
    config = self.config
    model = self.model
    cmd = []
    if config.search_strategy in ["FreeSearch"]:
      fs = (config.search_strategy == "FreeSearch")
      search = f"solve {self.optimisation_statement};" if fs else self.solve_statement
      model += search
      with open(config.model, 'w') as f:
          f.write(model)
      timeoutt = int(parameters['timeout'] * 1000)
      cmd = ["java", "-jar", f"../../choco-solver-4.10.14/choco-solver/choco.jar", config.model,"-limit", str(timeoutt),  "-f"]
      cmd.append("-lvl=RESANA")
      new_lines = f"\nvarh = 'Not-known'\nvalh = 'Not-known'\nsolver = '{self.config.solver}'\n"
    else:
      varh = self.build_varh(parameters)
      valh = self.build_valh(parameters)
      search_annot, variables = self.build_variables(parameters)
      search = f"solve :: seq_search(["
      if len(self.blocks) == 1:
          search += f"{search_annot}({variables},{varh},{valh},complete)"
      if len(self.blocks) > 1:
          for i, b in enumerate(self.blocks):
              if b[1] != variables:
                  if i == 0:
                      search += f"{search_annot}({b[1]},{varh},{valh},complete)"
                  else:
                      search += f",{search_annot}({b[1]},{varh},{valh},complete)"
      search += f"]) {self.optimisation_statement};"
      model += search
      with open(config.model, 'w') as f:
          f.write(model)
      if parameters['timeout'] == 0:
          timeoutt = int(float(parameters['timeout']) * 1000) + 1000
      else:
          timeoutt = int(float(parameters['timeout']) * 1000)
      if config.solver == "choco":
          # if config.model.endswith(".mzn"):
          #     cmd = ["minizinc", "-jar", f"../../choco-solver-4.10.14/choco-solver/choco.jar", config.model,
          #            config.data, "-f", f"-limit{timeoutt}"]
          if config.model.endswith(".fzn"):
              cmd = ["java", "-jar", f"../../choco-solver-4.10.14/choco-solver/choco.jar", config.model, "-limit", str(timeoutt)]
              cmd.append("-lvl=RESANA")
          if varh == "Solver_Default" and valh == "Solver_Default":
            model = self.model
            fs = (config.search_strategy == "FreeSearch")
            search = f"solve {self.optimisation_statement};" if fs else self.solve_statement
            model += search
            with open(config.model, 'w') as f:
                f.write(model)
            timeoutt = int(float(parameters['timeout']) * 1000)
            cmd = ["java", "-jar", f"../../choco-solver-4.10.14/choco-solver/choco.jar", config.model, "--free-search", "-limit", str(timeoutt)]
            # cmd.append("-lc=1")
            # cmd.append(f"-restarts=[luby,500,50000,true]")
            cmd.append("-lvl=RESANA")
      new_lines = f"\nvarh = '{varh}'\nvalh = '{valh}'\nsolver = '{self.config.solver}'\n"
    try:
      # print(cmd)
      output = subprocess.Popen(cmd, stdout=subprocess.PIPE)
      for line in iter(output.stdout.readline, b''):
        line = line.decode().strip()
        # print(line)
        output_lines.append(line)
    except TimeoutError:
      print("TimeoutError")
    finally:
        output.kill()
    bound, solver_solve_time, csv_SolveTime = self.parse_output(output_lines)
    if config.search_strategy in ["FreeSearch"]:
        self.model += self.solve_statement
        with open(config.model, 'w') as f:
            f.write(self.model)
    self.result["objective"] = bound
    if config.solver == "choco":
        if solver_solve_time is None:
            self.result["solveTime"] = float(csv_SolveTime)
        elif solver_solve_time is not None:
            self.result["solveTime"] = float(solver_solve_time)
    elif config.solver == "ace":
        if solver_solve_time is None:
            self.result["solveTime"] = float(parameters['timeout'])
        else:
            self.result["solveTime"] = solver_solve_time
    self.result["method"] = self.mode
    if cp_framework.flag == True and output_lines:
        # print(cmd)
        # parameters["rounds"] = config.rounds
        parameters["probing_ratio"] = config.probing_ratio
        ResultCollection.update_json_file(parameters, config, self.result, cmd) ##########################
    return new_lines, self.result

  def solve(self, parameters, cp_framework):
    search, result = self.solve_(parameters, cp_framework)
    result["search"] = search
    result["parameters"] = parameters
    if "objective" not in result:
      try:
        result["objective"] = result.solution.objective
      except AttributeError:
        result["objective"] = None
    if parameters.get('varh_values') is None :
      if parameters.get('varh_values') is None:
        save.append_results(parameters, result, result)
    return result