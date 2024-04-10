import signal
import subprocess
import pandas as pd
import time
import glob
import os
import math
import re
import json
from hpo.bayesian import Bayesian
from hpo.multiarmed import MultiArmed
from hpo.hyperband import HyperBand
from hpo.grid import Grid
from hpo.random import Random
from fetchmethod import FetchMethod

class TimeoutError (Exception):
    pass

class XCSP(Bayesian, MultiArmed, HyperBand, Grid, Random, FetchMethod):
    def __init__(self, config):
        self.format = config.format
        self.final_results_list = []
        self.results_list = []
        self.used_pairs = []
        self.method = "" # m
        self.counter = 0 # m
        self.EvaluationFlag = False # m
        self.StrategyFlag = False # m
        self.f = ''  # m
        self.model = config.model
        self.data = config.data
        self.dataparser = config.dataparser
        self.solver = config.solver
        self.hyperparameters_search = config.hyperparameters_search
        self.hpo = config.hpo
        self.probing_ratio = config.probing_ratio
        self.search_strategy = config.search_strategy
        if self.hyperparameters_search == "Only_Var":
            if self.format == "Minizinc":
                # if self.solver == 'choco':
                self.parameters = {
                    "varh_values": ["input_order", "first_fail", "smallest"], #, "largest", "dom_w_deg", "occurrence","most_constrained", "max_regret"
                    "valh_values": ["indomain_median"]}
            elif self.format == "XCSP3":
                if self.solver == 'choco':
                    self.parameters = {
                        'varh_values': ['DOM', 'CHS', 'FIRST_FAIL', 'DOMWDEG', 'DOMWDEG_CACD', 'FLBA', 'FRBA', 'PICKONDOM0'],
                        'valh_values': ['MED']}
                elif self.solver == 'ace':
                    self.parameters = {
                        'varh_values': ['Impact', 'Dom', 'Activity', 'Wdeg', 'Deg', 'Memory', 'DdegOnDom', 'Ddeg', 'CRBS', 'PickOnDom'],
                        'valh_values': ['Median']}

        elif self.hyperparameters_search == "Only_Val":
            if self.format == "Minizinc":
                # if self.solver == 'choco':
                self.parameters = {
                    "varh_values": ["dom_w_deg"],
                    "valh_values": ["indomain_min", "indomain_max", "indomain_median"]} #, "indomain_random", "indomain_split","indomain_reverse_split", "indomain_interval"

            elif self.format == "XCSP3":
                if self.solver == 'choco':
                    self.parameters = {
                        'varh_values': ['DOMWDEG'],
                        'valh_values': ['MAX', 'MIN', 'MED', 'MIDFLOOR', 'MIDCEIL', 'RAND']}
                elif self.solver == 'ace':
                    self.parameters = {
                        'varh_values': ['Wdeg'],
                        'valh_values': ['Dist', 'Vals', 'OccsR', 'Bivs3', 'Median', 'AsgsFp']}

        elif self.hyperparameters_search == "Simple_Search":
            if self.format == "Minizinc":
                # if self.solver == 'choco':
                self.parameters = {
                    "varh_values": ["input_order", "first_fail", "smallest"], #, "largest", "dom_w_deg", "occurrence","most_constrained", "max_regret"
                    "valh_values": ["indomain_min", "indomain_max", "indomain_median"]} #, "indomain_random", "indomain_split","indomain_reverse_split", "indomain_interval"
            elif self.format == "XCSP3":
                if self.solver == 'choco':
                    self.parameters = {
                        'varh_values': ['DOM', 'CHS', 'FIRST_FAIL', 'DOMWDEG'], # , 'DOMWDEG_CACD', 'FLBA', 'FRBA', 'PICKONDOM0'
                        'valh_values': ['MAX', 'MIN', 'MED']} #, 'MIDFLOOR', 'MIDCEIL', 'RAND'
                elif self.solver == 'ace':
                    self.parameters = {
                        'varh_values': ['Impact', 'Dom', 'Activity', 'Wdeg', 'Deg', 'Memory', 'DdegOnDom', 'Ddeg', 'CRBS', 'PickOnDom'],
                        'valh_values': ['Dist', 'Vals', 'OccsR', 'Bivs3', 'Median', 'AsgsFp']}

        if self.format == "Minizinc":
            if self.hyperparameters_search == "Block_Search":
                self.Blocks = []  # m
                self.NBlocks = 0  # m
                # if self.solver == 'choco':
                self.parameters = {
                    "varh_values": ["input_order", "first_fail", "smallest", "largest", "dom_w_deg",
                                    "occurrence", "most_constrained", "max_regret"],
                    "valh_values": ["indomain_min", "indomain_max", "indomain_median", "indomain_random",
                                    "indomain_split", "indomain_reverse_split", "indomain_interval"]}


        if config.hyperparameters_restart == "None":
            self.RestartStrategy = ["None"]
            self.restartsequence = ["None"]
            self.geocoef = ["None"]
        elif config.hyperparameters_restart == "Restart":
            self.RestartStrategy = ["luby", "GEOMETRIC"]
            self.restartsequence = [100 , 500]
            self.geocoef = ["None"]
        elif config.hyperparameters_restart == "Full_Restart":
            self.RestartStrategy = ["luby", "GEOMETRIC"]
            self.restartsequence = [100 , 200,  500]
            self.geocoef = [1.2 , 1.5, 2]

        self.global_timeout_sec = config.timeout
        self.probe_timeout_sec = 0
        self.result_timeout_sec = 0
        self.NSolution = None
        self.Objective = None
        self.Status = None
        self.Solution = None
        self.flag = False

        if self.hpo != "None":
            self.modes = [self.hpo]
            self.fractions = [self.probing_ratio]
            self.rounds = config.rounds
        elif config.hpo == "None":
            self.modes = [self.search_strategy]

        if self.hyperparameters_search == "None":
            if self.format == "Minizinc" :
                self.search_strategy = "UserDefined"
                self.modes = [self.search_strategy]
            if self.format == "XCSP3" :
                self.search_strategy = "DefaultPick"
                self.modes = [self.search_strategy]
                if self.solver == 'choco':
                    self.parameters = {
                        'varh_values': ['PICKONDOM0'], # , 'DOMWDEG_CACD', 'FLBA', 'FRBA', 'PICKONDOM0'
                        'valh_values': ['MAX', 'MIN']} #, 'MIDFLOOR', 'MIDCEIL', 'RAND'

        self.reward = 0

        def handler(signum, frame):
            raise TimeoutError

        signal.signal(signal.SIGALRM, handler)

        for mode in self.modes:
            self.mode = mode
            print(f"Running {self.mode} analysis with, solver={self.solver}, Time={int(self.global_timeout_sec)} sec")
            if self.format == "Minizinc":
                self.fetch_method()

            if self.mode == "GridSearch":
                for fraction in self.fractions:
                    self.probe_timeout_sec = self.global_timeout_sec * fraction
                    self.results_list = []
                    self.GridSearch()
                    self.find_best_rows()
                    if self.format == "Minizinc":
                        if self.hyperparameters_search == "Block_Search":
                            BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                       "valh": self.find_best_rows()['valh'].iloc[0],
                                       "restart": self.find_best_rows()['restart'].iloc[0],
                                       "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                       "geocoef": self.find_best_rows()['geocoef'].iloc[0],
                                       "block": self.find_best_rows()['block'].iloc[0]}
                            self.BlockSolveStrategy(BestRow["varh"], BestRow["valh"], BestRow["restart"],
                                               BestRow["restartsequence"],
                                               BestRow["geocoef"],
                                               BestRow["block"])  # call main function again for last run(solving phase)
                        else:
                            BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                       "valh": self.find_best_rows()['valh'].iloc[0],
                                       "restart": self.find_best_rows()['restart'].iloc[0],
                                       "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                       "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                            self.solveStrategy(BestRow["varh"], BestRow["valh"], BestRow["restart"],
                                                    BestRow["restartsequence"],
                                                    BestRow["geocoef"])

                    elif self.format == "XCSP3":
                        BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                   # fetch the configuration of the best row based of probing phase for transmitting to the solve phase
                                   "valh": self.find_best_rows()['valh'].iloc[0],
                                   "restart": self.find_best_rows()['restart'].iloc[0],
                                   "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                   "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                        self.solveXCSP(BestRow["varh"], BestRow["valh"], BestRow["restart"], BestRow["restartsequence"],
                                       BestRow["geocoef"])  # call main function again for last run(solving phase)
                    self.save_results_to_csv()

            elif self.mode == "RandomSearch":
                for fraction in self.fractions:
                    self.probe_timeout_sec = self.global_timeout_sec * fraction
                    self.results_list = []
                    for i in range(self.rounds):
                        random_strategy = self.gen_random_strategy()
                        varh = random_strategy['varh_values']
                        valh = random_strategy['valh_values']
                        strategy = random_strategy['RestartStrategy']
                        seq = random_strategy['restartsequence']
                        coef = random_strategy['geocoef']
                        print(f"Iteration {i + 1} with varh={varh}, valh={valh}, restart={strategy}, restartsequence={seq}, ,geocoef={coef}, solver={self.solver}")

                        if self.format == "Minizinc":
                            if self.hyperparameters_search == "Block_Search":
                                block = random_strategy['block']
                                self.BlockSolveStrategy(varh, valh, strategy, seq, coef, block)
                            else:
                                self.solveStrategy(varh, valh, strategy, seq, coef)
                        elif self.format == "XCSP3":
                            self.solveXCSP(varh, valh, strategy, seq, coef)
                    self.find_best_rows()
                    if self.format == "Minizinc":
                        if self.hyperparameters_search == "Block_Search":
                            BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                       "valh": self.find_best_rows()['valh'].iloc[0],
                                       "restart": self.find_best_rows()['restart'].iloc[0],
                                       "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                       "geocoef": self.find_best_rows()['geocoef'].iloc[0],
                                       "block": self.find_best_rows()['block'].iloc[0]}
                            self.BlockSolveStrategy(BestRow["varh"], BestRow["valh"], BestRow["restart"],
                                               BestRow["restartsequence"],
                                               BestRow["geocoef"],
                                               BestRow["block"])  # call main function again for last run(solving phase)
                        else:
                            BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                       "valh": self.find_best_rows()['valh'].iloc[0],
                                       "restart": self.find_best_rows()['restart'].iloc[0],
                                       "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                       "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                            self.solveStrategy(BestRow["varh"], BestRow["valh"], BestRow["restart"],
                                                    BestRow["restartsequence"],
                                                    BestRow["geocoef"])

                    elif self.format == "XCSP3":
                        BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                   # fetch the configuration of the best row based of probing phase for transmitting to the solve phase
                                   "valh": self.find_best_rows()['valh'].iloc[0],
                                   "restart": self.find_best_rows()['restart'].iloc[0],
                                   "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                   "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                        self.solveXCSP(BestRow["varh"], BestRow["valh"], BestRow["restart"], BestRow["restartsequence"],
                                       BestRow["geocoef"])  # call main function again for last run(solving phase)
                    self.save_results_to_csv()

            elif self.mode == "HyperBand":
                for fraction in self.fractions:
                    self.probe_timeout_sec = self.global_timeout_sec * fraction
                    self.used_pairs = []
                    self.results_list = []
                    self.hyperband_optimisation()
                    print(len(self.parameters['varh_values']), self.rounds)
                    self.find_best_rows()
                    if self.format == "Minizinc":
                        if self.hyperparameters_search == "Block_Search":
                            BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                       "valh": self.find_best_rows()['valh'].iloc[0],
                                       "restart": self.find_best_rows()['restart'].iloc[0],
                                       "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                       "geocoef": self.find_best_rows()['geocoef'].iloc[0],
                                       "block": self.find_best_rows()['block'].iloc[0]}
                            self.BlockSolveStrategy(BestRow["varh"], BestRow["valh"], BestRow["restart"],
                                               BestRow["restartsequence"],
                                               BestRow["geocoef"],
                                               BestRow["block"])  # call main function again for last run(solving phase)
                        else:

                            BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                       "valh": self.find_best_rows()['valh'].iloc[0],
                                       "restart": self.find_best_rows()['restart'].iloc[0],
                                       "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                       "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                            self.solveStrategy(BestRow["varh"], BestRow["valh"], BestRow["restart"],
                                                    BestRow["restartsequence"],
                                                    BestRow["geocoef"])

                    elif self.format == "XCSP3":
                        BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                   # fetch the configuration of the best row based of probing phase for transmitting to the solve phase
                                   "valh": self.find_best_rows()['valh'].iloc[0],
                                   "restart": self.find_best_rows()['restart'].iloc[0],
                                   "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                   "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                        self.solveXCSP(BestRow["varh"], BestRow["valh"], BestRow["restart"], BestRow["restartsequence"],
                                       BestRow["geocoef"])  # call main function again for last run(solving phase)
                    self.save_results_to_csv()

            elif self.mode == "BayesianOptimisation":
                for fraction in self.fractions:
                    self.probe_timeout_sec = self.global_timeout_sec * fraction #set the probing time-out
                    self.results_list = []
                    self.Bayesian_optimisation()
                    self.find_best_rows()
                    if self.format == "Minizinc":
                        if self.hyperparameters_search == "Block_Search":
                            BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                       "valh": self.find_best_rows()['valh'].iloc[0],
                                       "restart": self.find_best_rows()['restart'].iloc[0],
                                       "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                       "geocoef": self.find_best_rows()['geocoef'].iloc[0],
                                       "block": self.find_best_rows()['block'].iloc[0]}
                            self.BlockSolveStrategy(BestRow["varh"], BestRow["valh"], BestRow["restart"], BestRow["restartsequence"],
                                           BestRow["geocoef"], BestRow["block"])  # call main function again for last run(solving phase)
                        else:
                            BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                       "valh": self.find_best_rows()['valh'].iloc[0],
                                       "restart": self.find_best_rows()['restart'].iloc[0],
                                       "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                       "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                            self.solveStrategy(BestRow["varh"], BestRow["valh"], BestRow["restart"],
                                                    BestRow["restartsequence"],
                                                    BestRow["geocoef"])

                    elif self.format == "XCSP3":
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
                    self.AST(len(self.parameters['varh_values']) , self.rounds)
                    self.find_best_rows()
                    if self.format == "Minizinc":
                        if self.hyperparameters_search == "Block_Search":
                            BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                       "valh": self.find_best_rows()['valh'].iloc[0],
                                       "restart": self.find_best_rows()['restart'].iloc[0],
                                       "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                       "geocoef": self.find_best_rows()['geocoef'].iloc[0],
                                       "block": self.find_best_rows()['block'].iloc[0]}
                            self.BlockSolveStrategy(BestRow["varh"], BestRow["valh"], BestRow["restart"],
                                               BestRow["restartsequence"],
                                               BestRow["geocoef"],
                                               BestRow["block"])  # call main function again for last run(solving phase)
                        else:
                            BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                       "valh": self.find_best_rows()['valh'].iloc[0],
                                       "restart": self.find_best_rows()['restart'].iloc[0],
                                       "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                       "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                            self.solveStrategy(BestRow["varh"], BestRow["valh"], BestRow["restart"],
                                                    BestRow["restartsequence"],
                                                    BestRow["geocoef"])

                    elif self.format == "XCSP3":
                        BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                   # fetch the configuration of the best row based of probing phase for transmitting to the solve phase
                                   "valh": self.find_best_rows()['valh'].iloc[0],
                                   "restart": self.find_best_rows()['restart'].iloc[0],
                                   "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                                   "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                        self.solveXCSP(BestRow["varh"], BestRow["valh"], BestRow["restart"], BestRow["restartsequence"],
                                       BestRow["geocoef"])  # call main function again for last run(solving phase)
                    self.save_results_to_csv()

            elif self.mode == "FreeSearch":
                if self.format == "Minizinc":
                    self.solvefree()
                elif self.format == "XCSP3":
                    self.freesearch()
                self.save_results_to_csv()

            elif self.mode == "UserDefined":
                if self.format == "Minizinc":
                    self.Defaultsolve()
                self.save_results_to_csv()

            elif self.mode == "DefaultPick":
                self.results_list = []
                self.GridSearch()
                self.find_best_rows()
                BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                           "valh": self.find_best_rows()['valh'].iloc[0],
                           "restart": self.find_best_rows()['restart'].iloc[0],
                           "restartsequence": self.find_best_rows()['restartsequence'].iloc[0],
                           "geocoef": self.find_best_rows()['geocoef'].iloc[0]}
                self.solveXCSP(BestRow["varh"], BestRow["valh"], BestRow["restart"], BestRow["restartsequence"],
                               BestRow["geocoef"])  # call main function again for last run(solving phase)
                self.save_results_to_csv()



    def solveXCSP(self , varh , valh, restart, restartsequence , geocoef):
        if not self.flag:
            if self.mode == "GridSearch":
                self.result_timeout_sec = self.probe_timeout_sec / (
                        (len(self.parameters['varh_values']) * len(
                            self.parameters['valh_values']) * len(self.RestartStrategy) * len(
                            self.restartsequence) * len(self.geocoef)))
            elif self.mode in ["BayesianOptimisation", "RandomSearch", "MultiArmed", "HyperBand"]:
                self.result_timeout_sec = self.probe_timeout_sec / (self.rounds)
            elif self.mode == "DefaultPick":
                self.result_timeout_sec = self.probe_timeout_sec / (
                    (len(self.parameters['valh_values']) * len(self.RestartStrategy) * len(
                        self.restartsequence) * len(self.geocoef)))

        if self.flag:
            self.result_timeout_sec = self.global_timeout_sec - self.probe_timeout_sec
        n_solutions, bound, status, solution = None , None , None , None

        print(f'Running with varh={varh}, valh={valh}, restart={restart}, restartsequence={restartsequence} , geocoef={geocoef} , solver={self.solver} , Time={round(self.result_timeout_sec, 3)} sec')
        # signal.alarm(int(self.result_timeout_sec))
        signal.setitimer(signal.ITIMER_REAL, round(self.result_timeout_sec, 3), 0)
        # Set an alarm based on the calculated timeout

        with open('datavarval.txt', 'w') as f: # Write the parameters to a file to fetch the parameters from this file and put them in xcsp model
            f.write(f'{varh}\n')
            f.write(f'{valh}\n')
            f.write(f'{self.flag}\n')
            f.write(f'{self.solver}\n')
            f.write(f'{restart}\n')
            f.write(f'{restartsequence}\n')
            f.write(f'{geocoef}\n')

        # Construct the command to run the model
        cmd = ["python3", f"benchmarks/data/modelsXCSP22/COP/{self.model}/{self.model}.py"]
        if self.data:# If data is provided, add it to the command, some times we dont have it, and the data provided inside the model
            cmd.append(f"-data=benchmarks/data/modelsXCSP22/COP/{self.model}/{self.data}")
        if self.dataparser:
            cmd.append(f"-dataparser=benchmarks/data/modelsXCSP22/COP/{self.model}/{self.dataparser}.py")
        start_time = time.time()
        # Run the model and capture the output
        try:
            # try:
            output = subprocess.run(cmd, universal_newlines=True, text=True, capture_output=True)

            #     output = subprocess.run(cmd, universal_newlines=True, text=True, capture_output=True , timeout=round(self.result_timeout_sec, 3))
            # except subprocess.TimeoutExpired:
            #     print("The command timed out.")
            #     output = None
            #     return 1
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
        cmd = ["python3", f"benchmarks/data/modelsXCSP22/COP/{self.model}/{self.model}.py"] # Prepare the command to run the model with the required information for free search based on documentation
        if self.data:
            cmd.append(f"-data=benchmarks/data/modelsXCSP22/COP/{self.model}/{self.data}")
        if self.dataparser:
            cmd.append(f"-dataparser=benchmarks/data/modelsXCSP22/COP/{self.model}/{self.dataparser}.py")
        # related commands for each solver just the base lines are used (for being fair, these commands are here, but we dont need them actually)
        if self.solver == "ace":
            cmd.extend([f"-solver=[ace] -luby -r_n=500 "])
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
        if output == None:
            n_solutions, bound, status, solution = None, None, None, None
            return n_solutions, bound, status, solution
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
        results_df = pd.DataFrame(self.results_list)
        try:
            if self.format == "Minizinc":
                if self.results_list[0]['method'] == "maximize":
                        results_df.sort_values(by=['mode', 'Objective', 'ElapsedTime'],
                                               ascending=[True, False, True], inplace=True)
                elif self.results_list[0]['method'] == "minimize":
                        results_df.sort_values(by=['mode', 'Objective', 'ElapsedTime'],
                                               ascending=[True, True, True], inplace=True)

            elif self.format == "XCSP3":
                results_df.sort_values(by=['mode', 'Objective', 'ElapsedTime'],
                                           ascending=[True, True, True], inplace=True)
            best_rows = results_df.drop_duplicates(subset='mode', keep='first')
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
