import signal
import subprocess
import re
from pathlib import Path
from hpo.save_result import save
from ResultCollection import *
def handler(signum, frame):
    raise TimeoutError
signal.signal(signal.SIGALRM, handler)

class XCSP3Solver:
  def convert_seconds_to_time_format(self, timeout_in_seconds):
        hours = timeout_in_seconds // 3600
        minutes = (timeout_in_seconds % 3600) // 60
        seconds = timeout_in_seconds % 60
        time_format = f"\"[{int(hours):02d}h{int(minutes):02d}m{int(seconds):02d}s]\""
        return time_format

  def extract_optimisation_statement(self):
      content = Path(self.config.model).read_text()
      lines = content.split('\n')
      lines = [line for line in lines if not line.strip().startswith('%')]
      content = '\n'.join(lines)
      pattern = r"(minimize|maximize)\s*(.*?)"
      # pattern = r"(minimize|maximize)\s*\((.*?)\)\)"
      matches = re.findall(pattern, content, re.DOTALL)
      if matches:
          self.mode = matches[0][0]
      else:
          print("This is not an optimisation problem (no minimize or maximize statement).")
          exit(1)

  def __init__(self, config):
    self.final_results_list = []
    self.results_list = []
    self.result = {}
    self.flag = False
    self.solver_config = ResultCollection.load_config(config)
    self.config = config
    self.extract_optimisation_statement()
    self.n_solutions, self.bound, self.status, self.solution = None, None, None, None

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
                      solver_solve_time = components[2]
              s_lines = [line for line in lines if line.startswith('S')]
              if s_lines:
                  last_s_line = s_lines[-1]
                  components = last_s_line.split(';')
                  if len(components) >= 6:
                      csv_SolveTime = float(components[2])
                      csv_objective = int(components[5])
          elif self.config.solver == 'ace':
              last_line = lines[-1]
              ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
              last_line = ansi_escape.sub('', last_line)
              if last_line.startswith('run'):
                  run_data = last_line.split()
                  for data in run_data:
                      if data.startswith('bound:'):
                          bound = int(data.split(':')[1].replace(',', ''))
                      elif data.startswith('bounds:'):
                          bounds = data.split(':')[1].split('..')
                          if self.mode == "maximize":
                              bound = int(bounds[0]) - 1
                          elif self.mode == "minimize":
                              bound = int(bounds[1]) + 1
              elif last_line.startswith('o'):
                  bound = int(last_line.split()[1])
              else:
                  for line in reversed(lines):
                      match = re.search(r"<instantiation id='sol\d+' type='solution' cost='(-?\d+)'>", line)
                      if match:
                          bound = int(match.group(1))
                          break
              for line in reversed(lines):
                  match = re.search(r"c real time : (\d+\.\d+)", line)
                  if match:
                      solver_solve_time = float(match.group(1))
                      break
      else:
          print("No lines in the output.")
      return bound, solver_solve_time , csv_SolveTime

  def solve_(self, parameters, cp_framework):
    output_lines = []
    config = self.config
    probe_time = self.convert_seconds_to_time_format(parameters['timeout'])
    if config.search_strategy in ["FreeSearch"]:
        if config.solver == "ace":
            cmd = ["java", "-jar", f"../../ace/build/libs/ACE-2.3.jar", config.model, f"-t={int(parameters['timeout'] * 1000)}"]
        elif config.solver == "choco":
            cmd = ["java", "-jar", f"../../choco-solver-4.10.14/choco-solver/choco.jar", config.model, "-f","-csv", f"-limit {probe_time}"]
        new_lines = f"\nvarh = 'Not-known'\nvalh = 'Not-known'\nsolver = '{self.config.solver}'\n"
    else:
        varh = parameters['varh_values']
        valh = parameters['valh_values']
        if config.solver == "ace":
            cmd = ["java", "-jar", f"../../ace/build/libs/ACE-2.3.jar" , config.model, f"-t={int(parameters['timeout'] * 1000)}"]
            cmd.append(f"-varh={varh}")
            cmd.append(f"-valh={valh}")
            if varh == "Wdeg":
                cmd.append(f"-wt=CACD")
            elif varh == "PickOnDom":
                cmd.append(f"-pm=3")
            if varh == "Solver_Default" and valh == "Solver_Default":
                cmd = ["java", "-jar", f"../../ace/build/libs/ACE-2.3.jar", config.model,f"-t={int(parameters['timeout'] * 1000)}"]
        elif config.solver == "choco":
            cmd = ["java", "-jar", f"../../choco-solver-4.10.14/choco-solver/choco.jar", config.model, "-f","-csv",f"-limit {probe_time}"]
            cmd.append(f"-valsel=[{valh},true,16,true]")
            cmd.append(f"-varsel=[{varh},tie,32]")
            cmd.append("-lc=1")
            cmd.append(f"-restarts=[luby,500,50000,true]")
            if varh == "Solver_Default" and valh == "Solver_Default":
                cmd = ["java", "-jar", f"../../choco-solver-4.10.14/choco-solver/choco.jar", config.model, "-f", "-csv", f"-limit {probe_time}"]
                cmd.append("-lc=1")
                cmd.append(f"-restarts=[luby,500,50000,true]")
        elif config.solver == "picat":
            cmd = ["java", "-jar", f"../../picat/picat", config.model, "-f","-csv", f"-limit {probe_time}"]
            cmd.append(f"-valsel=[{valh},true,1,true]")
            cmd.append(f"-varsel=[{varh},0,32]")
            # cmd.append("-lc=1")
            # cmd.append(f"-restarts=[luby,500,50000,true]")
            if varh == "Solver_Default" and valh == "Solver_Default":
                cmd = ["java", "-jar", f"../../choco-solver-4.10.14/choco-solver/choco.jar", config.model, "-f", "-csv", f"-limit {probe_time}"]
                cmd.append("-lc=1")
                cmd.append(f"-restarts=[luby,500,50000,true]")
        new_lines = f"\nvarh = '{varh}'\nvalh = '{valh}'\nsolver = '{self.config.solver}'\n"
    try:
        # print(cmd)
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        # print(output)
        for line in iter(output.stdout.readline, b''):
            line = line.decode().strip()
            output_lines.append(line)
            print(line)
    except TimeoutError:
        print("TimeoutError")
    finally:
        output.kill()
    bound, solver_solve_time, csv_SolveTime= self.parse_output(output_lines)
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
        # parameters["rounds"] = config.rounds ##########################
        parameters["probing_ratio"] = config.probing_ratio
        ResultCollection.update_json_file(parameters, config, self.result, cmd)  ##########################
    return new_lines ,self.result

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