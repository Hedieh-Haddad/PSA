from minizinc import Instance, Model, Solver
from datetime import timedelta
import re
import random
class FetchMethod:
    def fetch_method(self):
        model = Model(self.model.replace('.mzn', '-free.mzn'))
        model.add_file(self.data, parse_data=True)
        model.add_string("output [\"Defaul_Var = \", show(Defaul_Var), \";\"];")
        model.add_string("output [\"Defaul_Val = \", show(Defaul_Val), \";\"];")
        solver = Solver.lookup(self.solver)
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
    ################################################################################
        if self.hyperparameters_search == "Block_Search":
            model = Model(self.model)
            model.add_file(self.data, parse_data=True)
            model.add_string(f"varsel = {Default_Var};")
            model.add_string(f"valsel = {Default_Val};")
            model.add_string("output [\"BlocksNumber = \", show(BlocksNumber), \";\"];")
            solver = Solver.lookup(self.solver)
            instance = Instance(solver, model)
            result = instance.solve(timeout=timedelta(seconds=60))# 60
            # print(result)
            self.method = result.statistics['method']
            output = str(result.solution)
            # print(output)
            line = [line for line in output.split('\n') if 'BlocksNumber' in line][0]
            self.NBlocks = int(re.search(r'BlocksNumber = (\d+);', line).group(1))
            # print("Blockssssssssssss",self.NBlocks)
            #################################################################################
            variable_strategy = random.choice(self.parameters["varh_values"])
            value_strategy = random.choice(self.parameters["valh_values"])
            pair = {"variable_strategy": variable_strategy, "value_strategy": value_strategy}
            model = Model(self.model)
            model.add_file(self.data, parse_data=True)
            model.add_string(f"varsel = {pair['variable_strategy']};")
            model.add_string(f"valsel = {pair['value_strategy']};")
            model.add_string("output [\"BlocksNumber = \", show(BlocksNumber), \";\"];")
            for i in range(1, (self.NBlocks)+1):
              model.add_string(f"output [\"Group_{i} = \", show(Group_{i}), \";\"];")
            solver = Solver.lookup(self.solver)
            instance = Instance(solver, model)
            result = instance.solve(timeout=timedelta(seconds=20))#20
            output = str(result.solution)
            # print("outputtttttttt",output)
            for i in range(1, (self.NBlocks) + 1):
                index_group_i = output.find('Group_' + str(i) + ' = "') + len('Group_' + str(i) + ' = "')
                group_i_value = output[index_group_i: output.find('"', index_group_i)]
                self.Blocks.append(group_i_value)
