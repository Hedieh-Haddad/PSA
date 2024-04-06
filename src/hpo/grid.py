
class Grid:
    def GridSearch(self):
        varh_values = self.parameters['varh_values']
        valh_values = self.parameters['valh_values']
        RestartStrategy = self.RestartStrategy
        restartsequence = self.restartsequence
        geocoef = self.geocoef
        for varh in varh_values:
            for valh in valh_values:
                for strategy in RestartStrategy:
                    for seq in restartsequence:
                        for coef in geocoef:
                            self.solveXCSP(varh, valh, strategy, seq, coef)