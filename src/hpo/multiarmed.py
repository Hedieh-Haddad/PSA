import numpy as np

class MultiArmed:
    def find_m(self , target_rounds):
        def sigma_luby(n):
            sequence = [1]
            while len(sequence) < n:
                sequence += sequence + [2 * sequence[-1]]
            return sequence[:n]
        m = 0
        total_rounds = 0
        while total_rounds < target_rounds:
            m += 1
            total_rounds = sum(sigma_luby(m))
        return m

    def AST(self, K, m):
        def sigma_luby(n):  # Define the Luby sequence function
            sequence = [1]
            while len(sequence) < n:
                sequence += sequence + [2 * sequence[-1]]
            return sequence[:n]

        S = self.parameters['varh_values']  # the set of variable heuristics
        V = iter(sorted(self.parameters['valh_values']))  # the set of sorted values heuristics alphabetically
        R = iter(self.RestartStrategy)  # the set of sorted restart strategies alphabetically
        Seq = iter(self.restartsequence)  # the set of restart sequences
        geo = iter(self.geocoef)  # the set of geometric coefficients     "Blocks" : self.Blocks
        if self.hyperparameters_search == "Block_Search":
            blks = iter(self.Blocks)
        arms_played = {}  # Initialize a set for the played arms
        # print(self.rounds)
        m = self.find_m(self.rounds)
        # print("M", m)
        for t in range(1, m):
            # Get the next values from the iterators, or reset them if they're exhausted
            valh = next(V, None)
            restart = next(R, None)
            restartsequence = next(Seq, None)
            geocoef = next(geo, None)
            if self.hyperparameters_search == "Block_Search":
                blocks = next(blks, None)

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
            if self.hyperparameters_search == "Block_Search":
                if blocks is None:
                    blks = iter(self.Blocks)
                    blocks = next(blks)

            if sigma_luby(t)[-1] == 1:  # If the last value in the Luby sequence is 1, choose a random arm and play it then remove it from the list
                i = np.random.choice(S)
                arms_played[t] = i
                S.remove(i)
                if len(S) == 0:
                    S = K
                if self.format == "Minizinc":
                    if self.hyperparameters_search == "Block_Search":
                        self.BlockSolveStrategy(i, valh, restart, restartsequence, geocoef, blocks)
                    else:
                        self.solveStrategy(i, valh, restart, restartsequence, geocoef)
                elif self.format == "XCSP3":
                    self.solveXCSP(i, valh, restart, restartsequence, geocoef)

            else:  # play the arms from the previous two trials and choose the one with the highest reward
                # Let ileft be the arm played at run t − σluby(t)
                # Let iright be the arm played at run t − 1
                i_right = arms_played[t - 1]
                i_left = arms_played[t - (sigma_luby(t)[-1])]

                if self.format == "Minizinc":
                    if self.hyperparameters_search == "Block_Search":
                        self.BlockSolveStrategy(i_left, valh, restart, restartsequence, geocoef, blocks)
                    else:
                        self.solveStrategy(i_left, valh, restart, restartsequence, geocoef)
                elif self.format == "XCSP3":
                    self.solveXCSP(i_left, valh, restart, restartsequence, geocoef)

                left_reward = self.reward

                if self.format == "Minizinc":
                    if self.hyperparameters_search == "Block_Search":
                        self.BlockSolveStrategy(i_right, valh, restart, restartsequence, geocoef, blocks)
                    else:
                        self.solveStrategy(i_right, valh, restart, restartsequence, geocoef)
                elif self.format == "XCSP3":
                    self.solveXCSP(i_right, valh, restart, restartsequence, geocoef)

                right_reward = self.reward
                if left_reward is None or right_reward is None:
                    print("Warning: One or both rewards are None")
                elif left_reward < right_reward:
                    i = i_left
                else:
                    i = i_right
                arms_played[t] = i
                if self.format == "Minizinc":
                    if self.hyperparameters_search == "Block_Search":
                        self.BlockSolveStrategy(i, valh, restart, restartsequence, geocoef, blocks)
                    else:
                        self.solveStrategy(i, valh, restart, restartsequence, geocoef)
                elif self.format == "XCSP3":
                    self.solveXCSP(i, valh, restart, restartsequence, geocoef)