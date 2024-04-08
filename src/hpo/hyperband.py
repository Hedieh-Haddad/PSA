import numpy as np
import random

class HyperBand:
    def hyperband_optimisation(self):
        def get_random_configuration(self):
            varh_values = random.choice(self.parameters['varh_values'])
            valh_values = random.choice(self.parameters['valh_values'])
            RestartStrategy = random.choice(self.RestartStrategy)
            restartsequence = random.choice(self.restartsequence)
            geocoef = random.choice(self.geocoef)

            if self.format == "Minizinc":
                if self.hyperparameters_search == "Block_Search":
                    Blocks = random.choice(self.Blocks)
                    return {'varh_values': varh_values, 'valh_values': valh_values, 'RestartStrategy': RestartStrategy,
                            'restartsequence': restartsequence, 'geocoef': geocoef, 'Blocks': Blocks}
                else:
                    return {'varh_values': varh_values, 'valh_values': valh_values, 'RestartStrategy': RestartStrategy,
                            'restartsequence': restartsequence, 'geocoef': geocoef}
            elif self.format == "XCSP3":
                return {'varh_values':varh_values, 'valh_values':valh_values, 'RestartStrategy':RestartStrategy, 'restartsequence':restartsequence, 'geocoef':geocoef}

        def func(params):
            varh = params["varh_values"]
            valh = params["valh_values"]
            strategy = params["RestartStrategy"]
            seq = params["restartsequence"]
            coef = params["geocoef"]
            if self.format == "Minizinc":
                if self.hyperparameters_search == "Block_Search":
                    Blocks = params["Blocks"]
                    result = self.BlockSolveStrategy(varh, valh, strategy, seq, coef, Blocks)
                else:
                    result = self.solveStrategy(varh, valh, strategy, seq, coef)
            elif self.format == "XCSP3":
                result = self.solveXCSP(varh, valh, strategy, seq, coef)
            return result

        self.max_iter = self.rounds
        self.eta = 5
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
        return T

