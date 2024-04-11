import json
import traceback
import logging
import re
from main import *
from pathlib import Path
from minizinc import Instance, Model, Solver
from datetime import timedelta

class MinizincSolver:
  def extract_solve_statement(self):
    """
    Extracts the solve statement from a .mzn file and separates the rest of the content.
    """
    content = Path(self.config.model).read_text()
    # note that if the file contains a variable's name or comment with "solve", this will not work, it should be improved!
    solve_start = content.find('solve')
    solve_end = content.find(';', solve_start) + 1
    self.solve_statement = content[solve_start:solve_end]
    self.model = content[:solve_start] + content[solve_end:]

  def extract_blocks(self):
    """
    Extracts calls and their parameters for specific functions (int_search, bool_search,
    set_search, float_search) from the given solve statement.
    Add to `self.blocks` a list of lists, where each list is a subsearch strategy, e.g., ['int_search', 'arr', 'first_fail' 'indomain_min', 'complete'].

    """
    # Regex pattern to match specific function calls and capture their names and arguments
    pattern = r'(int_search|bool_search|set_search|float_search)\(([^)]+)\)'
    # Find all matches and capture their arguments
    matches = re.findall(pattern, self.solve_statement)
    results = []
    for function_name, params in matches:
      # Split each match's parameters into an array and return the result
      params = params.split(',')
      param_lists = [param.strip() for param in params]
      results.append([function_name] + param_lists)
    self.blocks = results

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
    self.solver_config = load_config(config)
    self.config = config
    self.extract_solve_statement()
    self.extract_optimisation_statement()
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

  # TODO: verify the default values.
  def build_restart(self, parameters):
    if parameters["restart_strategies"] == "geometric":
      return "restart_geometric(1.1, 2)"
    if parameters["restart_strategies"] == "luby":
      return "restart_luby(1.1)"

  def better_bound_constraint(self, parameters):
    if 'best_bound' in parameters:
      op = ">" if self.mode == "maximize" else "<"
      return f"\nconstraint {self.optimisation_variable} {op} {parameters['best_bound']};\n"
    else:
      return ""

  def solve_(self, parameters):
    config = self.config
    solver = Solver.lookup(config.solver)
    if config.search_strategy in ["UserDefined" , "FreeSearch"]:
      model = Model(config.model)
      model.add_file(config.data)
      instance = Instance(solver, model)
      fs = (config.search_strategy == "FreeSearch")
      search = f"solve {self.optimisation_statement};" if fs else self.solve_statement
      return search, instance.solve(timeout=timedelta(seconds=parameters["timeout"]), free_search=fs)
    else:
      varh = self.build_varh(parameters)
      valh = self.build_valh(parameters)
      search_annot, variables = self.build_variables(parameters)
      search = f"solve :: {search_annot}({variables}, {varh}, {valh}, complete) "
      if "restart_strategies" in parameters:
        restart_annot = self.build_restart(parameters)
        search += f" :: {restart_annot} "
      search += f"{self.optimisation_statement};"
      model = Model()
      model.add_string(self.model)
      model.add_string(search)
      model.add_string(self.better_bound_constraint(parameters))
      model.add_file(config.data)
      instance = Instance(solver, model)
      return search, instance.solve(timeout=timedelta(seconds=parameters["timeout"]))

  def solve(self, parameters):
    search, result = self.solve_(parameters)
    stats = result.statistics
    stats["search"] = search
    stats["parameters"] = parameters
    if "objective" not in stats:
      try:
        stats["objective"] = result.solution.objective
      except AttributeError:
        stats["objective"] = None
    return stats
