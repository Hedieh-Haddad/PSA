
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
                            if self.format == "Minizinc":
                                if self.hyperparameters_search == "Block_Search":
                                    blocks = self.Blocks
                                    for blck in blocks:
                                        self.BlockSolveStrategy(varh, valh, strategy, seq, coef, blck)
                                else:
                                    self.solveStrategy(varh, valh, strategy, seq, coef)
                            elif self.format == "XCSP3":
                                self.solveXCSP(varh, valh, strategy, seq, coef)


class Grid:
  def __init__(config, cp_framework):
    self.config = config
    self.cp_framework = cp_framework

  def generate_restart_parameters():


  def generate_search_parameters():

  def generate_parameters():


  def probe(probe_timeout_sec):
    timeout_per_round = probe_timeout_sec / self.config.rounds
    all_statistics = []
    num_rounds = 0
    for parameters in self.generate_parameters():
      if num_rounds >= self.config.rounds:
        break
      num_rounds += 1
      parameters["timeout"] = timeout_per_round
      all_statistics.add(self.cp_framework.solve(parameters))
