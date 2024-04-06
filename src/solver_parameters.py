
# Format is either Minizinc or XCSP3
def solver_parameters(solver, format):
  if solver == "choco":
    ...






        self.solver = 'choco'
        # self.solver = 'ace'
        self.modes = ["RandomSearch", "GridSearch", "BayesianOptimisation", "FreeSearch", "DefualtMinizinc"]  # "RandomSearch", "SensitivityAnalysis", "HyperBand", "ProbingEvaluation" , , "FreeSearch", "DefualtMinizinc"
        # self.modes = ["MultiArmed", "BayesianOptimisation", "FreeSearch"] # "MultiArmed",
        if self.solver == 'choco':
            self.parameters = {
                'varh_values': ['DOM', 'CHS', 'FIRST_FAIL', 'DOMWDEG', 'DOMWDEG_CACD', 'FLBA', 'FRBA', 'PICKONDOM0'],
                'valh_values': ['MAX', 'MIN', 'MED', 'MIDFLOOR', 'MIDCEIL', 'RAND']}
        elif self.solver == 'ace':
            self.parameters = {
                'varh_values' : ['Impact', 'Dom', 'Activity', 'Wdeg', 'Deg', 'Memory', 'DdegOnDom', 'Ddeg', 'CRBS', 'PickOnDom' ],
                'valh_values' : ['Dist', 'Vals', 'OccsR', 'Bivs3', 'Median', 'AsgsFp'] }
        self.RestartStrategy = ["luby", "GEOMETRIC"] # Set restart strategy for choco and ace (we just have luby and geometric)
        # self.restartsequence = [50, 100 , 200, 500 , 1000] #Set restart frequency
        self.restartsequence = [50, 100 ] #Set restart frequency
        # self.geocoef = [1, 1.2 , 1.5 , 2 , 5] # Set geometric coefficient that will multiply into restart frequency of geometric strategy (normally it is == 1.2)
        self.geocoef = [1.2]

        self.fractions = [0.2]  # Set different fractions for the probing time-out (probe time-out = global time-out * fraction)
        # self.fractions = [0.1, 0.2, 0.5, 0.7]
        self.K = len(self.parameters['varh_values'])     # Set K as the length of variable heuristic values used as number of arms
        self.m = [8] # [1, 2, 4, 8, 16]   for AST, the number of times for playing each arm and set the reward
        self.reward = 0
