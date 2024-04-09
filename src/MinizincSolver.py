class MinizincSolver:
  def __init__(config):
    # read the solver.json file

  def add_free_search_options(self, parameters):
    parameters["options"] = ["-f"]

  def add_options_with_value_selection(self, parameters, value_strategy):
    # check the value strategy is available for this solver.
    parameters["value_strategy"] = value_strategy

  def add_options_with_variable_selection(self, parameters, variable_strategy):
    # check the variable strategy is available for this solver.
    parameters["variable_strategy"] = variable_strategy

  def add_options_with_search(self, parameters, value_strategy, variable_strategy):
    parameters["todo"] = "todo"

  def add_timeout_option(self, parameters, timeout):
    parameters["todo"] = "todo"

  def restart_strategies():
    # read solver config file (choco.json)
    return [...]

  def variable_strategies():
    # read solver config file (choco.json)
    return [...]

  def value_strategies():
    # read solver config file (choco.json)
    return [...]

  def solve(self, parameters):
    return "todo"
