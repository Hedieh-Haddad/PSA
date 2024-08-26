import os
import json
import pandas as pd
import glob
import csv
import numpy as np
import matplotlib.pyplot as plt

class ResultCollection:
    def load_config(config):
        with open(f'solvers/{config.solver}.json', 'r') as f:
            solver_config = json.load(f)
            if config.format in solver_config:
                return solver_config[config.format]
            else:
                print(f"This solver has no {config.format} configuration.")
                exit(1)

    def update_json_file(parameters, config, statistics, cmd):
        solver = cmd[2].split('/')[-1].lower()
        if 'ace' in solver:
            solver_value = "ace"
        elif 'choco' in solver:
            solver_value = "choco"
        info = ResultCollection.extract_info(parameters, config, statistics, cmd, solver_value)
        header = ['model', 'data', 'solver', 'strategy', 'method', 'limit', 'rounds', 'probing_ratio', 'valh', 'varh', 'lc',
                  'restarts', 'objective', 'solveTime', 'seed', 'varh_fallback', 'valh_fallback', 'varh_bayesian', 'valh_bayesian', 'cmd']
        if info['strategy'] != 'FreeSearch':
            filename = f'{solver_value}_{config.hpo}_{config.timeout}_{info["probing_ratio"]}.csv'
        elif info['strategy'] == 'FreeSearch':
            filename = f'{solver_value}_FreeSearch_{config.timeout}.csv'
        data = []
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        for row in data:
            if row['model'] == info['model'] and row['strategy'] == info['strategy']:
                row.update(info)
                break
        else:
            data.append(info)
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(data)

    def extract_info(parameters, config, statistics, cmd, solver_value):
        lc_value = "Solver_Default"
        restarts_value = "Solver_Default"
        varh_value = "Solver_Default"
        valh_value = "Solver_Default"
        for i in range(len(cmd)):
            if '-restarts' in cmd[i]:
                restarts_value = cmd[i]
            elif '-luby' in cmd[i]:
                restarts_value = cmd[i]
            if '-lc' in cmd[i]:
                lc_value = cmd[i]
            if '-varsel' in cmd[i]:
                varh_value = cmd[i]
            elif '-varh' in cmd[i]:
                varh_value = cmd[i]
            if '-valsel' in cmd[i]:
                valh_value = cmd[i]
            elif '-valh' in cmd[i]:
                valh_value = cmd[i]

        default_info = {
            'strategy': 'FreeSearch',
            'rounds': 'None',
            'probing_ratio': 'None',
            'seed': 'None',
            'varh_fallback': 'None',
            'valh_fallback': 'None',
            'varh_bayesian': 'None',
            'valh_bayesian': 'None',
        }
        if solver_value == 'choco':
            print("80 result collection",cmd)
            model = cmd[3].split('/')[-1]
            data = cmd[1].split('/')[-1]#####
            limit = parameters['timeout']
            if parameters.get('varh_values') is not None and parameters.get('valh_values') is not None:
                info = {
                    'strategy': config.hpo,
                    'rounds': 'None', ##########################
                    'probing_ratio': parameters['probing_ratio'],
                    'seed': parameters['seed'],
                    'varh_fallback': parameters['varh_fallback'],
                    'valh_fallback': parameters['valh_fallback'],
                    'varh_bayesian': parameters['varh_bayesian'],
                    'valh_bayesian': parameters['valh_bayesian'],
                }
            else:
                info = default_info
        elif solver_value == 'ace':
            model = cmd[3].split('/')[-1]
            data = cmd[1].split('/')[-1]#######
            limit = parameters['timeout']
            if parameters.get('varh_values') is not None and parameters.get('valh_values') is not None:
                info = {
                    'strategy': config.hpo,
                    'rounds': 'None',##########################
                    'probing_ratio': parameters['probing_ratio'],
                    'seed': parameters['seed'],
                    'varh_fallback': parameters['varh_fallback'],
                    'valh_fallback': parameters['valh_fallback'],
                    'varh_bayesian': parameters['varh_bayesian'],
                    'valh_bayesian': parameters['valh_bayesian'],
                }
            else:
                info = default_info
        return {
            **info,
            "model": model,
            "data": data,
            "solver": solver_value,
            'method': statistics['method'],
            'limit': limit,
            'valh': varh_value,
            'varh': valh_value,
            'lc': lc_value,
            'restarts': restarts_value,
            'objective': statistics['objective'],
            'solveTime': statistics['solveTime'],
            'cmd': cmd[4:],
        }

    def analysis(parameters,config):
        hpo_data = pd.read_csv(f'{config.solver}_{config.hpo}_{config.timeout}_{config.probing_ratio}.csv')
        free_search_data = pd.read_csv(f'{config.solver}_FreeSearch_{config.timeout}.csv')
        merged_data = pd.merge(hpo_data, free_search_data, on='model', suffixes=('_hpo', '_free'))
        merged_data['objective_hpo'] = pd.to_numeric(merged_data['objective_hpo'].replace('None', np.nan))
        merged_data['objective_free'] = pd.to_numeric(merged_data['objective_free'].replace('None', np.nan))
        merged_data['objective_hpo'] = merged_data['objective_hpo'].astype(float)
        merged_data['objective_free'] = merged_data['objective_free'].astype(float)
        hpo_better = free_better = equal = 0
        for index, row in merged_data.iterrows():
            if row['method_hpo'] == 'minimize':
                if float(row['objective_hpo']) < float(row['objective_free']):
                    hpo_better += 1
                elif float(row['objective_hpo']) > float(row['objective_free']):
                    free_better += 1
                else:
                    equal += 1
            else:
                if float(row['objective_hpo']) > float(row['objective_free']):
                    hpo_better += 1
                elif float(row['objective_hpo']) < float(row['objective_free']):
                    free_better += 1
                else:
                    equal += 1
        total = hpo_better + free_better + equal
        hpo_percentage = (hpo_better / total) * 100
        free_percentage = (free_better / total) * 100
        equal_percentage = (equal / total) * 100
        fallback_counter = merged_data[(merged_data['varh_fallback_hpo'] != 'None') & (merged_data['valh_fallback_hpo'] != 'None')].count().max()
        exact_match_counter = merged_data[(merged_data['varh_bayesian_hpo'] != 'None') & (merged_data['valh_bayesian_hpo'] != 'None')].count().max()
        # fallback_counter = merged_data[(merged_data['varh_fallback_hpo'] != 'None') | (merged_data['varh_fallback_hpo'].notna()) & (
        #                 merged_data['valh_fallback_hpo'] != 'None') | (merged_data['valh_fallback_hpo'].notna())].count().max()
        # exact_match_counter = merged_data[(merged_data['varh_bayesian_hpo'] != 'None') | (merged_data['varh_bayesian_hpo'].notna()) & (
        #                 merged_data['valh_bayesian_hpo'] != 'None') | (merged_data['valh_bayesian_hpo'].notna())].count().max()

        with open(f'{config.solver}_{config.hpo}_{config.timeout}_{config.probing_ratio}.txt', 'w') as f:
            f.write(f'HPO performed better in {hpo_percentage}% of the models,with this number{hpo_better}\n')
            f.write(f'FreeSearch performed better in {free_percentage}% of the models,with this number{free_better}\n')
            f.write(f'The results were equal in {equal_percentage}% of the models,with this number{equal}\n')
            f.write(f'The results were equal in {(fallback_counter / len(merged_data)) * 100}% of the models,with this number{equal}\n')
            f.write(f'The results were equal in {(exact_match_counter / len(merged_data)) * 100}% of the models,with this number{equal}\n')
        print(f'HPO performed better in {hpo_percentage}% of the models.')
        print(f'FreeSearch performed better in {free_percentage}% of the models.')
        print(f'The results were equal in {equal_percentage}% of the models.')
        print(f'for {(fallback_counter / len(merged_data)) * 100}% of the cases, HPO did fallback to FreeSearch.')
        print(f'for {(exact_match_counter / len(merged_data)) * 100}% of the cases, HPO have found as same configuration as FreeSearch.')
        labels = ['HPO better', 'FreeSearch better', 'Equal']
        sizes = [hpo_better, free_better, equal]
        colors = ['green' if hpo_better >= free_better else 'orange',
                  'green' if free_better > hpo_better else 'orange',
                  (0.678, 0.847, 0.902)]
        plt.figure(figsize=(10, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        plt.title('Objective-Value Comparison between HPO and FreeSearch')
        plt.ylabel('')
        plt.legend(labels, title="Categories", loc="upper right", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.savefig(f'{config.solver}_{config.hpo}_{config.timeout}_{config.probing_ratio}.png')
