from minizinc import Instance, Model, Solver
from datetime import timedelta
import re
import random
class FetchMethod:

    def fetch_method(self, config, parameters):
        Blocks = []
        model = Model(config.model.replace('.mzn', '-free.mzn'))
        model.add_file(config.data, parse_data=True)
        model.add_string("output [\"Defaul_Var = \", show(Defaul_Var), \";\"];")
        model.add_string("output [\"Defaul_Val = \", show(Defaul_Val), \";\"];")
        solver = Solver.lookup(config.solver)
        instance = Instance(solver, model)
        result = instance.solve(timeout=timedelta(seconds=20)) #20
        self.method = result.statistics['method']
        output = str(result.solution)
        defaul_var_value = re.search('Defaul_Var = "(.*?)"', output)
        if defaul_var_value is None:
          Default_Var = "input_order"
        if defaul_var_value:
          Default_Var = defaul_var_value.group(1)
        defaul_val_value = re.search('Defaul_Val = "(.*?)"', output)
        if defaul_val_value is None:
          Default_Val = "indomain_min"
        if defaul_val_value:
          Default_Val = defaul_val_value.group(1)

        # print(Default_Var, Default_Val)
    ################################################################################
        if config.hyperparameters_search == "Block_Search":
            model = Model(config.model)
            model.add_file(config.data, parse_data=True)
            model.add_string(f"varsel = {Default_Var};")
            model.add_string(f"valsel = {Default_Val};")
            model.add_string("output [\"BlocksNumber = \", show(BlocksNumber), \";\"];")
            solver = Solver.lookup(config.solver)
            instance = Instance(solver, model)
            result = instance.solve(timeout=timedelta(seconds=60))# 60
            self.method = result.statistics['method']
            output = str(result.solution)
            # print(output)
            line = [line for line in output.split('\n') if 'BlocksNumber' in line][0]
            self.NBlocks = int(re.search(r'BlocksNumber = (\d+);', line).group(1))
            # print("Blockssssssssssss",self.NBlocks)
            #################################################################################
            # print(parameters['parameters']['varh_values'], parameters['parameters']['valh_values'])
            if isinstance(parameters['parameters']['varh_values'], list):
                variable_strategy = random.choice(parameters['parameters']['varh_values'])
            else:
                variable_strategy = parameters['parameters']['varh_values']

            if isinstance(parameters['parameters']['valh_values'], list):
                value_strategy = random.choice(parameters['parameters']['valh_values'])
            else:
                value_strategy = parameters['parameters']['valh_values']
            # value_strategy = random.choice(parameters['parameters']['valh_values'])
            pair = {"variable_strategy": variable_strategy, "value_strategy": value_strategy}
            # print(pair)
            model = Model(config.model)
            model.add_file(config.data, parse_data=True)
            model.add_string(f"varsel = {pair['variable_strategy']};")
            model.add_string(f"valsel = {pair['value_strategy']};")
            model.add_string("output [\"BlocksNumber = \", show(BlocksNumber), \";\"];")
            for i in range(1, (self.NBlocks) + 1):
                model.add_string(f"output [\"Group_{i} = \", show(Group_{i}), \";\"];")
            solver = Solver.lookup(config.solver)
            instance = Instance(solver, model)
            result = instance.solve(timeout=timedelta(seconds=20))  # 20
            output = str(result.solution)
            # print("outputtttttttt",output)
            for i in range(1, (self.NBlocks) + 1):
                index_group_i = output.find('Group_' + str(i) + ' = "') + len('Group_' + str(i) + ' = "')
                group_i_value = output[index_group_i: output.find('"', index_group_i)]
                Blocks.append(group_i_value)

        # print(Default_Var, Default_Val, Blocks)
        return (Default_Var, Default_Val, Blocks)