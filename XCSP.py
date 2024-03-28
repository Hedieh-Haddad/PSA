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
        self.final_results_list = []
        self.results_list = []
        self.model = config.model
        self.data = config.data
        self.dataparser = config.dataparser
        # self.solver = 'choco'
        self.solver = 'ace'
        # self.modes = ["MultiArmed"]
        self.modes = ["BayesianOptimisation", "FreeSearch", "MultiArmed"]
        if self.solver == 'choco':
            self.parameters = {
                'varh_values': ['DOM', 'CHS', 'FIRST_FAIL', 'DOMWDEG', 'DOMWDEG_CACD', 'FLBA', 'FRBA', 'PICKONDOM0'],
                'valh_values': ['MAX', 'MIN', 'MED', 'MIDFLOOR', 'MIDCEIL', 'RAND']}

        elif self.solver == 'ace':
            self.parameters = {
                'varh_values' : ['Impact', 'Dom', 'Activity', 'Wdeg', 'Deg', 'Memory', 'DdegOnDom', 'Ddeg', 'CRBS', 'PickOnDom' ],
                'valh_values' : ['Dist', 'Vals', 'OccsR', 'Bivs3', 'Median', 'AsgsFp'] }

        self.RestartStrategy = ["luby", "GEOMETRIC"]
        self.used_pairs = []
        self.rounds = config.rounds
        self.baselines_used = set()
        self.max_iter = 0
        self.eta = 0
        self.counter = 0
        self.global_timeout_sec = config.global_timeout_sec
        # self.probe_timeout_sec = int(self.global_timeout_sec*(2/10))
        self.probe_timeout_sec = 0
        self.result_timeout_sec = 0
        self.newval = ''
        self.flagpick = False
        self.NSolution = None
        self.Objective = None
        self.Status = None
        self.Solution = None
        self.flag = False
        self.fractions = [0.5]  # 0.1, 0.2, 0.5 , 0.7 , 1
        self.K = len(self.parameters['varh_values'])
        self.m = [8] # [1, 2, 4, 8, 16]
        self.reward = 0

        def handler (signum, frame):
            raise TimeoutError
        signal.signal (signal.SIGALRM, handler)
        for mode in self.modes:
            self.mode = mode
            if self.mode == "ProbingEvaluation":
                print(
                    f"Running {self.mode} analysis")
            elif self.mode == "BayesianOptimisation":
                print(
                    f"Running {self.mode} analysis")
            elif self.mode == "RandomSearch":
                print(
                    f"Running {self.mode} analysis")
            elif self.mode == "FreeSearch":
                print(
                    f"Running {self.mode} analysis with, solver={self.solver} , Time={int(self.global_timeout_sec)} sec")
            elif self.mode == "DefualtMinizinc":
                print(
                    f"Running {self.mode} analysis")
            elif self.mode == "SensitivityAnalysis":
                print(
                    f"Running {self.mode} analysis")
            elif self.mode == "MultiArmed":
                print(
                    f"Running {self.mode} analysis")
            else:
                print(
                    f"Running {self.mode} analysis")

            if self.mode == "GridSearch":
                self.results_list = []
                self.GridSearch()
                self.find_best_rows()
                BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                           "valh": self.find_best_rows()['valh'].iloc[0]}
                self.solveXCSP(BestRow["varh"], BestRow["valh"])
                self.save_results_to_csv()

            # elif self.mode == "RandomSearch":
            #     self.results_list = []
            #     for i in range(self.rounds):
            #         random_strategy = self.gen_random_strategy()
            #         varh = random_strategy['varh_values']
            #         valh = random_strategy['valh_values']
            #         print(f"Iteration {i + 1} with varh={varh}, valh={valh}, solver={self.solver}")
            #         self.solveXCSP(varh, valh)
            #     self.find_best_rows()
            #     BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
            #                "valh": self.find_best_rows()['valh'].iloc[0]}
            #     self.solveXCSP(BestRow["varh"], BestRow["valh"])
            #     self.save_results_to_csv()

            # elif self.mode == "SensitivityAnalysis":
            #     self.used_pairs = []
            #     self.results_list = []
            #     for i in range(self.SArounds):
            #         baseline = self.gen_random_strategy()
            #         varh = baseline['varh_values']
            #         valh = baseline['valh_values']
            #         print(f"Iteration {i + 1} with varh={varh}, valh={valh}, solver={self.solver}")
            #         for param in self.parameters['valh_values']:
            #             self.solveXCSP(varh, param)
            #         for param in self.parameters['varh_values']:
            #             self.solveXCSP(param, valh)
            #     self.find_best_rows()
            #     BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
            #                "valh": self.find_best_rows()['valh'].iloc[0]}
            #     self.solveXCSP(BestRow["varh"], BestRow["valh"])
            #     self.save_results_to_csv()

            # elif self.mode == "HyperBand":
            #     self.used_pairs = []
            #     self.results_list = []
            #     self.hyperband_optimisation()
            #     self.find_best_rows()
            #     BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
            #                "valh": self.find_best_rows()['valh'].iloc[0]}
            #     self.solveXCSP(BestRow["varh"], BestRow["valh"])
            #     self.save_results_to_csv()

            # elif self.mode == "ProbingEvaluation":
            #     self.EvaluationFlag = True
            #     self.results_list = []
            #     self.GridSearch()
            #     self.save_results_to_csv()

            elif self.mode == "BayesianOptimisation":
                for fraction in self.fractions:
                    self.f = fraction
                    self.probe_timeout_sec = self.global_timeout_sec * fraction
                    print(self.probe_timeout_sec)
                    self.results_list = []
                    self.beysian_optimisation()
                    self.find_best_rows()
                    BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                               "valh": self.find_best_rows()['valh'].iloc[0],
                               "restart": self.find_best_rows()['restart'].iloc[0]}
                    self.solveXCSP(BestRow["varh"], BestRow["valh"], BestRow["restart"])
                    self.newval = BestRow["valh"]
                    # print(self.newval)
                    self.save_results_to_csv()

            elif self.mode == "MultiArmed":
                for fraction in self.fractions:
                    self.f = fraction
                    self.probe_timeout_sec = self.global_timeout_sec * fraction
                    self.results_list = []
                    for m in self.m :
                        self.AST(self.K, m)
                        self.find_best_rows()
                        BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                                   "valh": self.find_best_rows()['valh'].iloc[0],
                                   "restart": self.find_best_rows()['restart'].iloc[0]}
                        self.solveXCSP(BestRow["varh"], BestRow["valh"], BestRow["restart"])
                        self.newval = BestRow["valh"]
                        # print(self.newval)
                        self.save_results_to_csv()

            elif self.mode == "FreeSearch":
                self.freesearch()
                self.save_results_to_csv()

            elif self.mode == "DefaulPick":
                self.results_list = []
                self.parameters = {
                    'varh_values': ['PICKONDOM0'],
                    'valh_values': ['MAX','MIN', 'MED', 'MIDFLOOR', 'MIDCEIL', 'RAND']}
                    # 'valh_values': [self.newval]}
                self.GridSearch()
                self.find_best_rows()
                BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                           "valh": self.find_best_rows()['valh'].iloc[0]}
                self.newval = BestRow["valh"]
                # print(BestRow)
                self.flagpick = True
                self.results_list = []
                self.parameters = {
                    'varh_values': ['PICKONDOM0'],
                    # 'valh_values': ['MIN', 'MAX', 'MED', 'MIDFLOOR', 'MIDCEIL', 'RAND']}
                    'valh_values': [self.newval]}
                # print(self.parameters)
                self.GridSearch()
                # self.find_best_rows()
                # BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                #            "valh": self.find_best_rows()['valh'].iloc[0]}
                # self.solveXCSP(BestRow["varh"], BestRow["valh"])
                self.save_results_to_csv()
                self.flagpick = False

            elif self.mode == "DefaulDomwdeg":
                self.results_list = []
                self.parameters = {
                    'varh_values': ['DOMWDEG'],
                    'valh_values': ['MAX','MIN', 'MED', 'MIDFLOOR', 'MIDCEIL', 'RAND']} #'MAX','MIN', 'MED', 'MIDFLOOR', 'MIDCEIL', 'RAND'
                self.GridSearch()
                self.find_best_rows()
                BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                           "valh": self.find_best_rows()['valh'].iloc[0]}
                self.newval = BestRow["valh"]
                # print("global" , self.global_timeout_sec)
                self.flagpick = True
                self.results_list = []
                self.parameters = {
                    'varh_values': ['DOMWDEG'],
                    'valh_values': [self.newval]}
                    # 'valh_values': ['MIN', 'MAX', 'MED', 'MIDFLOOR', 'MIDCEIL', 'RAND']}
                self.GridSearch()
                # self.find_best_rows()
                # BestRow = {"varh": self.find_best_rows()['varh'].iloc[0],
                #            "valh": self.find_best_rows()['valh'].iloc[0]}
                # self.solveXCSP(BestRow["varh"], BestRow["valh"])
                self.save_results_to_csv()
                self.flagpick = False

    def gen_random_strategy(self):
        while True:
            varh_values = random.choice(self.parameters['varh_values'])
            valh_values = random.choice(self.parameters['valh_values'])
            pair = {'varh_values':varh_values, 'valh_values':valh_values}
            if pair not in self.used_pairs:
                self.used_pairs.append(pair)
                return pair

    def GridSearch(self):
        varh_values = self.parameters['varh_values']
        valh_values = self.parameters['valh_values']
        for varh in varh_values:
            for valh in valh_values:
                self.solveXCSP(varh, valh)

    def beysian_optimisation(self):
        SpaceParams = {**self.parameters, 'RestartStrategy': self.RestartStrategy}
        opt = Optimizer(dimensions=dimensions_aslist(SpaceParams), base_estimator="GP")
        def func(params):
            params = point_asdict(SpaceParams, params)
            varh = params["varh_values"]
            valh = params["valh_values"]
            restrat = params["RestartStrategy"]
            self.solveXCSP(varh, valh, restrat)
            return 1

        for i in range(self.rounds):
            next_x = opt.ask()
            f_val = func(next_x)
            output = opt.tell(next_x, f_val)
            if len(output.func_vals) >= 4 and (tuple(output.func_vals[-1:]) == tuple(output.func_vals[-2:-1])) and (
                    tuple(output.func_vals[-2:-1]) == tuple(output.func_vals[-3:-2])) and (
                    tuple(output.func_vals[-3:-2]) == tuple(output.func_vals[-4:-3])):
                if len(output.x_iters) >= 4 and (tuple(output.x_iters[-1:]) == tuple(output.x_iters[-2:-1])) and (
                        tuple(output.x_iters[-2:-1]) == tuple(output.x_iters[-3:-2])) and (
                        tuple(output.x_iters[-3:-2]) == tuple(output.x_iters[-4:-3])):
                    break
        best_params = point_asdict(SpaceParams, opt.Xi[np.argmin(opt.yi)])
        return best_params



    def AST(self, K, m):
        def sigma_luby(n):
            sequence = [1]
            while len(sequence) < n:
                sequence += sequence + [2 * sequence[-1]]
            return sequence[:n]

        S = self.parameters['varh_values']
        V = iter(sorted(self.parameters['valh_values']))
        R = iter(self.RestartStrategy)
        t = 1
        arms_played = {}
        for t in range(1, m):
            valh = next(V, None)
            restart = next(R, None)
            if valh is None:
                V = iter(sorted(self.parameters['valh_values']))
                valh = next(V)
            if restart is None:
                R = iter(self.RestartStrategy)
                restart = next(R)
            if sigma_luby(t)[-1] == 1:
                i = np.random.choice(S)
                arms_played[t] = i
                S.remove(i)
                if len(S) == 0:
                    S = K
            else:
                i_right = arms_played[t - 1]
                i_left = arms_played[t - (sigma_luby(t)[-1])]
                self.solveXCSP(i_left, valh, restart)
                left_reward = self.reward
                self.solveXCSP(i_right, valh, restart)
                right_reward = self.reward
                if left_reward < right_reward:
                    i = i_left
                else:
                    i = i_right
                arms_played[t] = i
            self.solveXCSP(i, valh, restart)

    def freesearch(self):
        n_solutions, bound, status, solution = None, None, None, None
        signal.alarm(self.global_timeout_sec)
        # try:
        cmd = ["python3", f"modelsXCSP22/COP/{self.model}/{self.model}.py"]
        if self.data:
            cmd.append(f"-data=modelsXCSP22/COP/{self.model}/{self.data}")
        if self.dataparser:
            cmd.append(f"-dataparser=modelsXCSP22/COP/{self.model}/{self.dataparser}.py")
        # print("Solverrrrrrrrrrrrrrrrrr",self.solver)
        # cmd.extend(["-f ", f"-solver=[{self.solver},v]"])
        if self.solver == "ace":
            cmd.extend([f"-solver=[ace] -luby -r_n=500 -ref="""])
        elif self.solver == "choco":
            cmd.extend(["-f ", f"-solver=[choco,v] -best -last -lc 1 -restarts [luby,500,0,50000,true]"])
        # if self.solver == "ace":
        #     cmd.extend([f"-solver=[{self.solver}]"])
        # elif self.solver == "choco":
        #     cmd.extend(["-f ", f"-solver=[{self.solver},v]"])
        # cmd.extend(["-f ", "-solver=[ACE,v]"]) #-best -last -lc 1 -restarts [luby,500,0,50000,true]
        start_time = time.time()
        try:
            output = subprocess.run(cmd, universal_newlines=True, text=True, capture_output=True)
            end_time = time.time()
            elapsed_time = end_time - start_time
            elapsed_time = round(elapsed_time, 3)
            n_solutions, bound, status, solution = self.parse_output(output)
        except TimeoutError:
            end_time = time.time()
            elapsed_time = end_time - start_time
            elapsed_time = round((elapsed_time - 0.01), 3)
            log_files = glob.glob('*.log')
            if log_files:
                latest_log_file = max(log_files, key=os.path.getctime)
                with open(latest_log_file, 'r') as log_file:
                    content = log_file.read()
                    lines = content.splitlines()
                    if lines:
                        last_line = lines[-1]
                        components = last_line.split()
                        if len(components) == 3 and components[0] == 'o':
                            bound = components[1]
                    else:
                        print("No lines in the content.")
        self.NSolution = n_solutions
        self.Objective = bound
        self.Status = status
        self.Solution = solution
        self.ElapsedTime = elapsed_time
        # print("FreeSearchchchchchchchch", self.flag)
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
        # except TimeoutError:
        #     print('Timeout reached, moving on to the next pair')
        signal.alarm(0)

        self.flag = False
        if bound is None:
            bound = 10000000000
        return bound

    def hyperband_optimisation(self):
        def get_random_configuration(self):
            varh_values = random.choice(self.parameters['varh_values'])
            valh_values = random.choice(self.parameters['valh_values'])
            return {'varh_values':varh_values, 'valh_values':valh_values}

        def func(params):
            varh = params["varh_values"]
            valh = params["valh_values"]
            result = self.solveXCSP(varh, valh)
            return result

        self.max_iter = 5
        self.eta = 3
        logeta = lambda x: np.log(x) / np.log(self.eta)
        s_max = int(logeta(self.max_iter))
        B = (s_max + 1) * self.max_iter
        self.counter = B/s_max
        for s in reversed(range(s_max + 1)):
            n = int(np.ceil(int(B / self.max_iter / (s + 1)) * self.eta ** s))
            r = self.max_iter * self.eta ** (-s)
            T = [get_random_configuration(self) for i in range(n)]
            for i in range(s + 1):
                n_i = n * self.eta ** (-i)
                r_i = r * self.eta ** (i)
                val_losses = [func(params) for params in T]
                T = [T[i] for i in np.argsort(val_losses)[0:int(n_i / self.eta)]]
        # print(self.counter)
        return T

    def solveXCSP(self , varh , valh, restart):
        if not self.flag:
            if self.mode == "GridSearch":
                self.result_timeout_sec = self.probe_timeout_sec / (
                        (len(self.parameters['varh_values']) * len(
                            self.parameters['varh_values'])))
            # elif self.mode == "RandomSearch":
            #     self.result_timeout_sec = self.probe_timeout_sec / (
            #             self.rounds)
            # elif self.mode == "SensitivityAnalysis":
            #     self.result_timeout_sec = self.probe_timeout_sec / (
            #             (len(self.parameters['varh_values']) + len(
            #                 self.parameters['varh_values'])) * self.SArounds)
            elif self.mode == "BayesianOptimisation":
                self.result_timeout_sec = self.probe_timeout_sec / (
                        self.rounds)
            # elif self.mode == "HyperBand":
            #     self.result_timeout_sec = self.probe_timeout_sec / (
            #             self.counter)
            elif self.mode == "MultiArmed":
                self.result_timeout_sec = self.probe_timeout_sec / (
                        self.rounds)
            # elif self.mode == "HyperBand":
            #     self.result_timeout_sec = self.probe_timeout_sec / (
            #             self.counter)
            elif self.mode == "DefaulPick":
                self.result_timeout_sec = self.probe_timeout_sec / (len(self.parameters['valh_values'])) #(48)
                # self.result_timeout_sec = self.probe_timeout_sec / (
                #     (len(self.parameters['varh_values']) * len(
                #         self.parameters['varh_values'])))
            elif self.mode == "DefaulDomwdeg":
                self.result_timeout_sec = self.probe_timeout_sec / (len(self.parameters['valh_values']))#(48)
                # self.result_timeout_sec = self.probe_timeout_sec / (
                #     (len(self.parameters['varh_values']) * len(
                #         self.parameters['varh_values'])))
            else:
                self.result_timeout_sec = self.global_timeout_sec
        if self.flag:
            self.result_timeout_sec = self.global_timeout_sec - self.probe_timeout_sec
            if self.flagpick:
                self.result_timeout_sec = self.global_timeout_sec
        n_solutions, bound, status, solution = None , None , None , None
        log_data = {
            "runs": [],
            "wrong_decisions": 0,
            "found_solutions": 0,
            "final_bound": 0
        }
        print(f'Running with varh={varh}, valh={valh}, restart={restart}, solver={self.solver} , Time={int(self.result_timeout_sec)} sec')
        signal.alarm(int(self.result_timeout_sec))
        with open('datavarval.txt', 'w') as f:
            f.write(f'{varh}\n')
            f.write(f'{valh}\n')
            f.write(f'{self.flag}\n')
            f.write(f'{self.solver}\n')
            f.write(f'{restart}\n')
        cmd = ["python3", f"modelsXCSP22/COP/{self.model}/{self.model}.py"]
        if self.data:
            cmd.append(f"-data=modelsXCSP22/COP/{self.model}/{self.data}")
        if self.dataparser:
            cmd.append(f"-dataparser=modelsXCSP22/COP/{self.model}/{self.dataparser}.py")
        # cmd = ["python3", f"{self.model}.xml.Lzma"]
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
                        if self.solver == 'choco':
                            last_line = lines[-1]
                            components = last_line.split()
                            if len(components) == 3 and components[0] == 'o':
                                bound = components[1]
                        elif self.solver == 'ace':
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
                                        # print(f"Effs: {effs}, Revisions: {revisions}, Useless: {useless}, nogoods: {nogoods}")
                                elif stripped_line.startswith('d WRONG DECISIONS'):
                                    words = line.split()
                                    wrongdecision = int(words[-1])
                                    # print(f"WrongDecision: {wrongdecision}")
            try:
                # self.reward = (math.log2(nogoods+useless)) / (math.log2(wrongdecision))
                self.reward = (math.log2(wrongdecision)) / (math.log2(nogoods + useless))
                # self.reward = (math.log2(elapsed_time)) / (math.log2(bound))
            except:
                self.reward = None
            # print("Reward: ", self.reward)
        except TimeoutError:
            end_time = time.time()
            elapsed_time = end_time - start_time
            elapsed_time = round((elapsed_time - 0.01), 3)
#             log_files = glob.glob('*.log')
#             if log_files:
#                 latest_log_file = max(log_files, key=os.path.getctime)
#                 with open(latest_log_file, 'r') as log_file:
#                     content = log_file.read()
#                     lines = content.splitlines()
#                     if lines:
#                         last_line = lines[-1]
#                         components = last_line.split()
#                         if len(components) == 3 and components[0] == 'o':
#                             bound = components[1]
# ###################################################################################################
#                         if line.startswith('run'):
#                             # Extract the run data
#                             run_data = line.split()
#                             # Extract the number of fails and wrong decisions from the run data
#                             fails = int(run_data[run_data.index('fails:') + 1])
#                             wrgs = int(run_data[run_data.index('wrgs:') + 1])
#                             # Append the run data to the runs list in log_data
#                             log_data["runs"].append({"fails": fails, "wrgs": wrgs})
#                         elif line.startswith('d WRONG DECISIONS'):
#                             # Extract the number of wrong decisions
#                             log_data["wrong_decisions"] = int(line.split()[2])
#                         elif line.startswith('d FOUND SOLUTIONS'):
#                             # Extract the number of found solutions
#                             log_data["found_solutions"] = int(line.split()[2])
#                         elif line.startswith('d BOUND'):
#                             # Extract the final bound
#                             log_data["final_bound"] = int(line.split()[1])
#                         print("#####################", log_data)
###################################################################################################
                    # else:
                    #     print("No lines in the content.")
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
                "Objective": bound,
                "ElapsedTime": elapsed_time,
                "Fraction": self.result_timeout_sec
            })
        signal.alarm(0)

        self.flag = False
        if bound is None:
            bound = 10000000000
        return bound

    def parse_output(self, output):
        lines = output.stdout.split('\n')
        # print(lines)
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

    def find_best_rows(self):
        results_df = pd.DataFrame(self.results_list)
        try:
            results_df.sort_values(by=['mode', 'Objective', 'ElapsedTime'],
                                       ascending=[True, True, True], inplace=True)
            best_rows = results_df.drop_duplicates(subset='mode', keep='first')
            self.flag = True
            print(best_rows)
            return best_rows
        except AttributeError:
            return None

    def save_results_to_csv(self, file_name="results.csv"):
        results_df = pd.DataFrame(self.final_results_list)
        results_df.sort_values(by=['mode', 'Objective', 'ElapsedTime'],
                                       ascending=[True, True, True], inplace=True)
        results_df.to_csv(file_name, index=False)
        print(f"Sorted results saved to {file_name}")

    # def estimate_pruned_tree_size(log_data):
    #     total_fails = sum(run["fails"] for run in log_data["runs"])
    #     total_wrong_decisions = log_data["wrong_decisions"]
    #     found_solutions = log_data["found_solutions"]
    #     final_bound = log_data["final_bound"]
    #
    #     # Estimate the pruned tree size
    #     # This is a rough estimate, as we do not have the exact tree structure
    #     pruned_tree_size = total_fails + total_wrong_decisions
    #
    #     return {
    #         "estimated_pruned_tree_size": pruned_tree_size,
    #         "found_solutions": found_solutions,
    #         "final_bound": final_bound
    #     }
    #
    # # Estimate the pruned tree size from the log data
    # estimated_data = estimate_pruned_tree_size(log_data)
