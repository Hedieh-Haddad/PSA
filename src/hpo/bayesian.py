import sys
sys.path.append('/Users/hedieh.haddad/Desktop/CP2024')
from skopt import Optimizer
from skopt.utils import point_asdict, dimensions_aslist
import numpy as np
from src.solveminizinc import SolveMinizinc
class Bayesian(SolveMinizinc):
    def __init__(self, config, cp_framework, probe_timeout_sec):
        self.format = config.format
        self.parameters = config.parameters
        self.probe_timeout_sec =probe_timeout_sec
        self.hyperparameters_search = config.hyperparameters_search

        self.Bayesian_optimisation()

    def Bayesian_optimisation(self):
        if self.format == "Minizinc":
            if self.hyperparameters_search == "Block_Search":
                SpaceParams = {**self.parameters, 'RestartStrategy': self.RestartStrategy, 'restartsequence': self.restartsequence, 'geocoef': self.geocoef, "Blocks" : self.Blocks}
            else:
                print("I'm hereeeeeeeeeeeeee")
                SpaceParams = {**self.parameters, 'RestartStrategy': self.RestartStrategy, 'restartsequence': self.restartsequence, 'geocoef': self.geocoef}

        elif self.format == "XCSP3":
            SpaceParams = {**self.parameters, 'RestartStrategy': self.RestartStrategy, 'restartsequence': self.restartsequence, 'geocoef': self.geocoef} # Combine the existing parameters, restart strategy, restart sequence, and geocoef into a dictionary
        opt = Optimizer(dimensions=dimensions_aslist(SpaceParams), base_estimator="GP")    # Initialize the optimizer with the given parameters and a Gaussian Process (GP) as the base estimator
        def func(params):
            params = point_asdict(SpaceParams, params) # Extract the parameters from dictionary
            varh = params["varh_values"]
            valh = params["valh_values"]
            restart = params["RestartStrategy"]
            restratSeq = params["restartsequence"]
            geocoef = params["geocoef"]
            if self.format == "Minizinc":
                if self.hyperparameters_search == "Block_Search":
                    Blocks = params["Blocks"]
                    self.BlockSolveStrategy(varh, valh, restart, restratSeq, geocoef, Blocks)
                else:
                    self.solveStrategy(varh, valh, restart, restratSeq, geocoef)
            elif self.format == "XCSP3":
                self.solveXCSP(varh, valh, restart, restratSeq, geocoef)
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