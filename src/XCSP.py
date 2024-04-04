import signal
import subprocess
import pandas as pd
import numpy as np
import scipy
from skopt import Optimizer
from skopt.utils import point_asdict, dimensions_aslist
import random
import time
import glob
import os
import math
import re

class TimeoutError (Exception):
    pass

class XCSP:
    def __init__(self, config):
        self.final_results_list = []  # Initialize lists for result_phase and probe_phase
        self.results_list = []
        self.model = config.model
        self.data = config.data
        self.dataparser = config.dataparser
        self.solver = 'choco'
        # self.solver = 'ace'
        self.modes = ["MultiArmed", "BayesianOptimisation", "FreeSearch"]
        if self.solver == 'choco':
            self.parameters = {
                'varh_values': ['DOM', 'CHS', 'FIRST_FAIL', 'DOMWDEG', 'DOMWDEG_CACD', 'FLBA', 'FRBA', 'PICKONDOM0'],
                'valh_values': ['MAX', 'MIN', 'MED', 'MIDFLOOR', 'MIDCEIL', 'RAND']}
        elif self.solver == 'ace':
            self.parameters = {
                'varh_values' : ['Impact', 'Dom', 'Activity', 'Wdeg', 'Deg', 'Memory', 'DdegOnDom', 'Ddeg', 'CRBS', 'PickOnDom' ],
                'valh_values' : ['Dist', 'Vals', 'OccsR', 'Bivs3', 'Median', 'AsgsFp'] }
        self.RestartStrategy = ["luby", "GEOMETRIC"] # Set restart strategy for choco and ace (we just have luby and geometric)
        self.restartsequence = [50, 100 , 200, 500 , 1000] #Set restart frequency
        self.geocoef = [1, 1.2 , 1.5 , 2 , 5] # Set geometric coefficient that will multiply into restart frequency of geometric strategy (normally it is == 1.2)
        # self.geocoef = [1.2]
        self.rounds = config.rounds
        self.global_timeout_sec = config.global_timeout_sec # Initialize the global timeout (normally == 1200)
        self.probe_timeout_sec = 0    # Initialize the timeout for probing phase (normally 20% of global time == 1200 * 0.2)
        self.result_timeout_sec = 0  # Initialize the timeout for each round in probing phase (normally  = probing time-out / number of rounds)
        self.NSolution = None # Initialize the variable for fetching information of solver like final solution, objective, CSP or COP(SAT/OPTIMUM), number of found solutions
        self.Objective = None
        self.Status = None
        self.Solution = None
        self.flag = False # set the flag for make the changes(transmit information ) from probing phase to result phase(like set the time-out for remaining time or save results separately)
        self.fractions = [0.2]  # Set different fractions for the probing time-out (probe time-out = global time-out * fraction)
        # self.fractions = [0.1, 0.2, 0.5, 0.7]
        self.K = len(self.parameters['varh_values'])     # Set K as the length of variable heuristic values used as number of arms
        self.m = [8] # [1, 2, 4, 8, 16]   for AST, the number of times for playing each arm and set the reward
        self.reward = 0     # Initialize reward for multi-armed approach

        def handler (signum, frame):
            raise TimeoutError
        signal.signal (signal.SIGALRM, handler)
        for mode in self.modes:
            self.mode = mode
            print(f"Running {self.mode} analysis with, solver={self.solver}, Time={int(self.global_timeout_sec)} sec")
            if self.mode == "BayesianOptimisation":
                for fraction in self.fractions:
                    self.probe_timeout_sec = self.global_timeout_sec * fraction #set the probing time-out
                    self.results_list = []
                    self.Bayesian_optimisation()
                    self.find_best_rows()
                    BestRow = {"varh": self.find_best_rows()['varh'].iloc[0], # fetch the configuration of the best row based of probing phase for transmitting to the solve phase
                               "valh": self.find_best_rows()['valh'].iloc[0],
                               "restart": self.find_best_rows()['restart'].iloc[0],
                               "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                               "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                    self.solveXCSP(BestRow["varh"], BestRow["valh"], BestRow["restart"], BestRow["restartsequence"], BestRow["geocoef"]) # call main function again for last run(solving phase)
                    self.save_results_to_csv()

            elif self.mode == "MultiArmed":
                for fraction in self.fractions:
                    self.probe_timeout_sec = self.global_timeout_sec * fraction
                    self.results_list = []
                    for m in self.m : # run the approach m times and set reward to the mth observed reward
                        self.AST(self.K, m)
                        self.find_best_rows()
                        BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                   "valh": self.find_best_rows()['valh'].iloc[0],
                                   "restart": self.find_best_rows()['restart'].iloc[0],
                                   "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                    "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                        self.solveXCSP(BestRow["varh"], BestRow["valh"], BestRow["restart"], BestRow["restartsequence"],
                                       BestRow["geocoef"])
                        self.save_results_to_csv()

            elif self.mode == "FreeSearch":
                self.freesearch()
                self.save_results_to_csv()

    def Bayesian_optimisation(self):
        SpaceParams = {**self.parameters, 'RestartStrategy': self.RestartStrategy, 'restartsequence': self.restartsequence, 'geocoef': self.geocoef} # Combine the existing parameters, restart strategy, restart sequence, and geocoef into a dictionary
        opt = Optimizer(dimensions=dimensions_aslist(SpaceParams), base_estimator="GP")    # Initialize the optimizer with the given parameters and a Gaussian Process (GP) as the base estimator
        def func(params):
            params = point_asdict(SpaceParams, params) # Extract the parameters from dictionary
            varh = params["varh_values"]
            valh = params["valh_values"]
            restrat = params["RestartStrategy"]
            restratSeq = params["restartsequence"]
            geocoef = params["geocoef"]
            self.solveXCSP(varh, valh, restrat, restratSeq, geocoef)
            return 1

        for i in range(self.rounds): # Perform the optimization for number of rounds
            next_x = opt.ask() # Ask the optimizer for the next set of parameters to try
            f_val = func(next_x) # Evaluate (update) the function with the given parameters
            output = opt.tell(next_x, f_val) # Tell the optimizer the result of the evaluation
            # If the function values and the parameters haven't changed for the last four iterations, break the loop
            if len(output.func_vals) >= 4 and (tuple(output.func_vals[-1:]) == tuple(output.func_vals[-2:-1])) and (
                    tuple(output.func_vals[-2:-1]) == tuple(output.func_vals[-3:-2])) and (
                    tuple(output.func_vals[-3:-2]) == tuple(output.func_vals[-4:-3])):
                if len(output.x_iters) >= 4 and (tuple(output.x_iters[-1:]) == tuple(output.x_iters[-2:-1])) and (
                        tuple(output.x_iters[-2:-1]) == tuple(output.x_iters[-3:-2])) and (
                        tuple(output.x_iters[-3:-2]) == tuple(output.x_iters[-4:-3])):
                    break
        best_params = point_asdict(SpaceParams, opt.Xi[np.argmin(opt.yi)]) # Get the best parameters found during the optimization
        return best_params

    def AST(self, K, m):
        def sigma_luby(n): # Define the Luby sequence function
            sequence = [1]
            while len(sequence) < n:
                sequence += sequence + [2 * sequence[-1]]
            return sequence[:n]

        S = self.parameters['varh_values'] # the set of variable heuristics
        V = iter(sorted(self.parameters['valh_values'])) # the set of sorted values heuristics alphabetically
        R = iter(self.RestartStrategy) # the set of sorted restart strategies alphabetically
        Seq = iter(self.restartsequence) # the set of restart sequences
        geo = iter(self.geocoef) # the set of geometric coefficients
        arms_played = {}  # Initialize a set for the played arms
        for t in range(1, m):
            # Get the next values from the iterators, or reset them if they're exhausted
            valh = next(V, None)
            restart = next(R, None)
            restartsequence = next(Seq, None)
            geocoef = next(geo, None)
            if valh is None:
                V = iter(sorted(self.parameters['valh_values']))
                valh = next(V)
            if restart is None:
                R = iter(self.RestartStrategy)
                restart = next(R)
            if restartsequence is None:
                Seq = iter(self.restartsequence)
                restartsequence = next(Seq)
            if geocoef is None:
                geo = iter(self.geocoef)
                geocoef = next(geo)

            if sigma_luby(t)[-1] == 1:# If the last value in the Luby sequence is 1, choose a random arm and play it then remove it from the list
                i = np.random.choice(S)
                arms_played[t] = i
                S.remove(i)
                if len(S) == 0:
                    S = K
                self.solveXCSP(i, valh, restart, restartsequence, geocoef)

            else: #play the arms from the previous two trials and choose the one with the highest reward
                #Let ileft be the arm played at run t − σluby(t)
                #Let iright be the arm played at run t − 1
                i_right = arms_played[t - 1]
                i_left = arms_played[t - (sigma_luby(t)[-1])]
                self.solveXCSP(i_left, valh, restart, restartsequence, geocoef)
                left_reward = self.reward
                self.solveXCSP(i_right, valh, restart, restartsequence, geocoef)
                right_reward = self.reward
                if left_reward is None or right_reward is None:
                    print("Warning: One or both rewards are None")
                elif left_reward < right_reward:
                    i = i_left
                else:
                    i = i_right
                arms_played[t] = i
                self.solveXCSP(i, valh, restart, restartsequence, geocoef)

    def solveXCSP(self , varh , valh, restart, restartsequence , geocoef):
        # set the time-out for probing phase and solving phase based on the mode, fraction and flags
        if not self.flag:
            if self.mode == "BayesianOptimisation":
                self.result_timeout_sec = self.probe_timeout_sec / (
                        self.rounds)
            elif self.mode == "MultiArmed":
                self.result_timeout_sec = self.probe_timeout_sec / (
                        self.rounds)
        if self.flag:
            self.result_timeout_sec = self.global_timeout_sec - self.probe_timeout_sec
        n_solutions, bound, status, solution = None , None , None , None

        print(f'Running with varh={varh}, valh={valh}, restart={restart}, restartsequence={restartsequence} , geocoef={geocoef} , solver={self.solver} , Time={int(self.result_timeout_sec)} sec')
        signal.alarm(int(self.result_timeout_sec))     # Set an alarm based on the calculated timeout

        with open('datavarval.txt', 'w') as f: # Write the parameters to a file to fetch the parameters from this file and put them in xcsp model
            f.write(f'{varh}\n')
            f.write(f'{valh}\n')
            f.write(f'{self.flag}\n')
            f.write(f'{self.solver}\n')
            f.write(f'{restart}\n')
            f.write(f'{restartsequence}\n')
            f.write(f'{geocoef}\n')

        # Construct the command to run the model
        cmd = ["python3", f"modelsXCSP22/COP/{self.model}/{self.model}.py"]
        if self.data:# If data is provided, add it to the command, some times we dont have it, and the data provided inside the model
            cmd.append(f"-data=modelsXCSP22/COP/{self.model}/{self.data}")
        if self.dataparser:
            cmd.append(f"-dataparser=modelsXCSP22/COP/{self.model}/{self.dataparser}.py")
        start_time = time.time()
        # Run the model and capture the output
        try:
            print(cmd)
            output = subprocess.run(cmd, universal_newlines=True, text=True, capture_output=True)
            end_time = time.time()
            elapsed_time = end_time - start_time
            elapsed_time = round(elapsed_time, 3)
            n_solutions, bound, status, solution = self.parse_output(output)
            # extract the required result from log file
            log_files = glob.glob('*.log')
            if log_files:
                latest_log_file = max(log_files, key=os.path.getctime)#open the most recent one
                with open(latest_log_file, 'r') as log_file:
                    content = log_file.read()
                    lines = content.splitlines()
                    if lines:
                        if self.solver == 'choco':
                            last_line = lines[-1]
                            components = last_line.split()
                            if len(components) == 3 and components[0] == 'o': #extract the bound from the last line
                                bound = components[1]
                        elif self.solver == 'ace':
                            for line in lines:
                                stripped_line = line.strip()
                                if stripped_line.startswith('effs'): # extract the effs, revisions, useless, and nogoods from the lines that start with 'effs'
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
            try: # Try to calculate the reward, the lower, the better
                self.reward = (math.log2(wrongdecision)) / (math.log2(nogoods + useless))
            except:
                self.reward = None
        except TimeoutError: # If a TimeoutError occurs, calculate the time
            end_time = time.time()
            elapsed_time = end_time - start_time
            elapsed_time = round((elapsed_time - 0.01), 3)

        self.NSolution = n_solutions
        self.Objective = bound
        self.Status = status
        self.Solution = solution
        self.ElapsedTime = elapsed_time
        print(f"Objective={bound}||ElapsedTime={elapsed_time}||Benchmark={self.model}||Data={self.data}||Mode={self.mode}")

        self.results_list.append({
            "phase": "Probe",
            "mode": self.mode,
            "varh": varh,
            "valh": valh,
            "restart": restart,
            "restartsequence": restartsequence,
            "geocoef": geocoef,
            "Objective": bound,
            "ElapsedTime": elapsed_time,
            "Fraction": self.result_timeout_sec
        })
        if not self.flag:
            self.final_results_list.append({
                "phase": "Probe",
                "mode": self.mode,
                "varh": varh,
                "valh": valh,
                "restart": restart,
                "restartsequence": restartsequence,
                "geocoef": geocoef,
                "Objective": bound,
                "ElapsedTime": elapsed_time,
                "Fraction": self.result_timeout_sec
            })
        if self.flag:
            self.final_results_list.append({
                "phase": "Result",
                "mode": self.mode,
                "varh": varh,
                "valh": valh,
                "restart": restart,
                "restartsequence": restartsequence,
                "geocoef": geocoef,
                "Objective": bound,
                "ElapsedTime": elapsed_time,
                "Fraction": self.result_timeout_sec
            })
        signal.alarm(0)

        self.flag = False
        if bound is None:
            bound = 10000000000
        return bound

    def freesearch(self):
        n_solutions, bound, status, solution = None, None, None, None
        signal.alarm(self.global_timeout_sec)
        cmd = ["python3", f"modelsXCSP22/COP/{self.model}/{self.model}.py"] # Prepare the command to run the model with the required information for free search based on documentation
        if self.data:
            cmd.append(f"-data=modelsXCSP22/COP/{self.model}/{self.data}")
        if self.dataparser:
            cmd.append(f"-dataparser=modelsXCSP22/COP/{self.model}/{self.dataparser}.py")
        # related commands for each solver just the base lines are used (for being fair, these commands are here, but we dont need them actually)
        if self.solver == "ace":
            cmd.extend([f"-solver=[ace] -luby -r_n=500 -ref="""])
        elif self.solver == "choco":
            cmd.extend(["-f ", f"-solver=[choco,v] -best -last -lc 1 -restarts [luby,500,0,50000,true]"])
        start_time = time.time()# Record the start time
        try:# Run the command and capture the output
            output = subprocess.run(cmd, universal_newlines=True, text=True, capture_output=True)
            end_time = time.time()
            elapsed_time = end_time - start_time # calculate the time
            elapsed_time = round(elapsed_time, 3)
            n_solutions, bound, status, solution = self.parse_output(output)# Parse the output
        except TimeoutError:
            end_time = time.time()
            elapsed_time = end_time - start_time
            elapsed_time = round((elapsed_time - 0.01), 3)
            log_files = glob.glob('*.log')
            if log_files:# If there are log files, open the latest one
                latest_log_file = max(log_files, key=os.path.getctime)
                with open(latest_log_file, 'r') as log_file:
                    content = log_file.read()# Read the content
                    lines = content.splitlines()# Split the content into lines
                    if lines:
                        last_line = lines[-1]
                        components = last_line.split()# Split the last line into components
                        if len(components) == 3 and components[0] == 'o': # If the first component is 'o' and there are three components, get the bound
                            bound = components[1]
                    else:
                        print("No lines in the content.")
        self.NSolution = n_solutions
        self.Objective = bound
        self.Status = status
        self.Solution = solution
        self.ElapsedTime = elapsed_time
        print(
                f"Objective={bound}||ElapsedTime={elapsed_time}||Benchmark={self.model}||Data={self.data}||Mode={self.mode}")

        self.results_list.append({
            "phase": "Probe",
            "mode": self.mode,
            "varh": "Not-Knonw",
            "valh": "Not-Knonw",
            "Objective": bound,
            "ElapsedTime": elapsed_time,
        })
        if not self.flag:
            self.final_results_list.append({
                "phase": "Probe",
                "mode": self.mode,
                "varh": "Not-Knonw",
                "valh": "Not-Knonw",
                "Objective": bound,
                "ElapsedTime": elapsed_time,
            })
        if self.flag:
            self.final_results_list.append({
                "phase": "Result",
                "mode": self.mode,
                "varh": "Not-Knonw",
                "valh": "Not-Knonw",
                "Objective": bound,
                "ElapsedTime": elapsed_time,
            })
        signal.alarm(0)
        self.flag = False
        if bound is None:
            bound = 10000000000
        return bound

    def parse_output(self, output):
        lines = output.stdout.split('\n') # Split the output into lines
        n_solutions, bound, status, solution = None , None , None , None
        for line in lines:# If a line starts with "NSolution", "Objective", "Status", or "Solution", extract the corresponding value
            if line.startswith("NSolution"):
                n_solutions = int(line.split()[1]) if line.split()[1] != 'None' else None
            elif line.startswith("Objective"):
                bound = int(line.split()[1]) if line.split()[1] != 'None' else None
            elif line.startswith("Status"):
                status = line.split()[1]
            elif line.startswith("Solution"):
                solution = line.split()[1]
        return n_solutions, bound, status, solution

    def find_best_rows(self):
        results_df = pd.DataFrame(self.results_list)# Convert the results list to a DataFrame
        try:# Sort the DataFrame
            results_df.sort_values(by=['mode', 'Objective', 'ElapsedTime'],
                                       ascending=[True, True, True], inplace=True)
            best_rows = results_df.drop_duplicates(subset='mode', keep='first')# Drop duplicated rows
            self.flag = True
            return best_rows
        except AttributeError:
            return None

    def save_results_to_csv(self, file_name="results.csv"):
        results_df = pd.DataFrame(self.final_results_list)
        results_df.sort_values(by=['mode', 'Objective', 'ElapsedTime'],
                                       ascending=[True, True, True], inplace=True)
        results_df.to_csv(file_name, index=False)# Save the DataFrame to a CSV file
        print(f"Sorted results saved to {file_name}")
