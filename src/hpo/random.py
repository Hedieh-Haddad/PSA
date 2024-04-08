import random
class Random:
    def gen_random_strategy(self):
        while True:
            varh_values = random.choice(self.parameters['varh_values'])
            valh_values = random.choice(self.parameters['valh_values'])
            RestartStrategy = random.choice(self.RestartStrategy)
            restartsequence = random.choice(self.restartsequence)
            geocoef = random.choice(self.geocoef)

            if self.format == "Minizinc":
                if self.hyperparameters_search == "Block_Search":
                    block = random.choice(self.Blocks)
                    pair = {'varh_values': varh_values, 'valh_values': valh_values, 'RestartStrategy': RestartStrategy,
                            'restartsequence': restartsequence, 'geocoef': geocoef, 'block': block}
                    if pair not in self.used_pairs:
                        self.used_pairs.append(pair)
                        return pair
                else:
                    pair = {'varh_values': varh_values, 'valh_values': valh_values, 'RestartStrategy': RestartStrategy,
                            'restartsequence': restartsequence, 'geocoef': geocoef}
                    if pair not in self.used_pairs:
                        self.used_pairs.append(pair)
                        return pair

            elif self.format == "XCSP3":
                pair = {'varh_values':varh_values, 'valh_values':valh_values, 'RestartStrategy':RestartStrategy, 'restartsequence':restartsequence, 'geocoef':geocoef}
                if pair not in self.used_pairs:
                    self.used_pairs.append(pair)
                    return pair




