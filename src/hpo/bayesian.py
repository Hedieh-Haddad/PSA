from skopt import Optimizer
from skopt.utils import point_asdict, dimensions_aslist
import numpy as np
class Bayesian:
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