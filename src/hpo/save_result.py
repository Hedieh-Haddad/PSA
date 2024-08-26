from datetime import datetime
import pandas as pd
import os
import json
import pandas as pd
from collections import OrderedDict
import pandas as pd
from collections import OrderedDict
import numpy as np
import csv

class save:
  def print_converted_results(cp_framework, stats, parameters):
    output = []
    output.append("Solving Phase:"+str(cp_framework.flag))
    output.append("Strategy:" + str(cp_framework.mode))
    if parameters.get('seed'):
      output.append("seed:" + str(parameters['seed']))
    else:
      output.append("seed=" + str(None))
    if stats['objective'] is None :
      output.append("Objective=" + "None")
    else:
      output.append("Objective=" + str(stats['objective']))
    if isinstance(stats['solveTime'], float):
      solve_time_seconds = stats['solveTime']
    elif isinstance(stats['solveTime'], str):
      solve_time_seconds = float(stats['solveTime'])
    elif stats['solveTime'] == None:
      solve_time_seconds = str(parameters['timeout'])
    else:
      solve_time_seconds = stats['solveTime'].total_seconds()
    output.append("solveTime=" + str(solve_time_seconds))
    if parameters.get('varh_values'):
      output.append("varh=" + str(parameters['varh_values']))
    else:
      output.append("varh=" + str(None))
    if parameters.get('valh_values'):
      output.append("valh=" + str(parameters['valh_values']))
    else:
      output.append("valh=" + str(None))
    if cp_framework.flag == True:
      if parameters.get('varh_fallback'):
        output.append("varh_fallback=" + str(parameters['varh_fallback']))
      else:
        output.append("varh_fallback=" + str(None))
      if parameters.get('valh_fallback'):
        output.append("valh_fallback=" + str(parameters['valh_fallback']))
      else:
        output.append("valh_fallback=" + str(None))
      if parameters.get('varh_bayesian'):
        output.append("varh_bayesian=" + str(parameters['varh_bayesian']))
      else:
        output.append("varh_bayesian=" + str(None))
      if parameters.get('valh_bayesian'):
        output.append("valh_bayesian=" + str(parameters['valh_bayesian']))
      else:
        output.append("valh_bayesian=" + str(None))
    output.append("----------\n==========")
    print("\n".join(output))
    return (save.save_converted_results(cp_framework, stats, parameters))

  def save_converted_results(cp_framework, stats, parameters):
    timeout = cp_framework.config.timeout
    if cp_framework.flag == True:
      total_time_used = cp_framework.config.timeout
    else:
      total_time_used = parameters["total_time_used"]

    if total_time_used <= (0.05 * timeout):
      correlation = 0.05
    elif (0.05 * timeout) < total_time_used <= (0.1 * timeout):
      correlation = 0.1
    elif (0.1 * timeout) < total_time_used <= (0.2 * timeout):
      correlation = 0.2
    elif (0.2 * timeout) < total_time_used <= (0.5 * timeout):
      correlation = 0.5
    elif (0.5 * timeout) < total_time_used:
      correlation = 1

    data = {
      "model": cp_framework.config.model.split('/')[-1],
      "ratio": cp_framework.config.probing_ratio,
      "Solving Phase": str(cp_framework.flag),
      "Strategy": str(cp_framework.mode),
      "seed": str(parameters.get('seed')),
      "Objective": str(stats['objective']) if stats['objective'] is not None else "None",
      "solveTime": str(stats['solveTime']) if isinstance(stats['solveTime'], float) else str(parameters['timeout']) if
      stats['solveTime'] == None else str(stats['solveTime'].total_seconds()) if isinstance(stats['solveTime'],str) else str(stats['solveTime'].total_seconds()),
      "varh": str(parameters.get('varh_values')) if parameters.get('varh_values') else str(None),
      "valh": str(parameters.get('valh_values')) if parameters.get('valh_values') else str(None),
      "varh_fallback": str(parameters.get('varh_fallback')) if cp_framework.flag == True and parameters.get(
        'varh_fallback') else str(None),
      "valh_fallback": str(parameters.get('valh_fallback')) if cp_framework.flag == True and parameters.get(
        'valh_fallback') else str(None),
      "varh_bayesian": str(parameters.get('varh_bayesian')) if cp_framework.flag == True and parameters.get(
        'varh_bayesian') else str(None),
      "valh_bayesian": str(parameters.get('valh_bayesian')) if cp_framework.flag == True and parameters.get(
        'valh_bayesian') else str(None),
      "correlation": correlation
    }
    file_path = f"result/{cp_framework.config.model.split('/')[5]}_{cp_framework.config.hpo}_{cp_framework.config.timeout}_{cp_framework.config.probing_ratio}.csv"
    try:
      with open(file_path, 'x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)
    except FileExistsError:
      with open(file_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        writer.writerow(data)
    df = pd.read_csv(file_path)
    is_minimize = 'minimize' in df['Strategy'].values
    df['Objective'] = pd.to_numeric(df['Objective'], errors='coerce')
    df['solveTime'] = pd.to_numeric(df['solveTime'], errors='coerce')
    df = df.sort_values(by=['Strategy', 'Objective', 'solveTime'], ascending=[True, is_minimize, True])
    df = df.drop_duplicates()
    df.to_csv(file_path, index=False)
    return data

  def append_results(parameters, cp_framework, stats):
    results_list = []
    results_list.append(parameters)
    results_list.append(stats["objective"])
    if isinstance(stats['solveTime'], float):
      solve_time_seconds = stats['solveTime']
    elif isinstance(stats['solveTime'], str):
      solve_time_seconds = float(stats['solveTime'])
    elif stats['solveTime'] == None:
      solve_time_seconds = str(parameters['timeout'])
    else:
      solve_time_seconds = stats['solveTime'].total_seconds()
    results_list.append(solve_time_seconds)
    if parameters.get('varh_values') is None :
      if parameters.get('varh_values') is None:
        pass
    else:
      if parameters.get('blocks') is not None:
        results_list.append(cp_framework.blocks[parameters['blocks']][1])
      elif parameters.get('blocks') is None:
        if cp_framework.config.format == "XCSP3":
          results_list.append("Not-Known")
        else:
          results_list.append(cp_framework.blocks[0][1])
      results_list.append(cp_framework.config.probing_ratio)
    return results_list
  def save_results_to_csv(results_list, cp_framework):
    file_name = f"OUTPUT-{cp_framework.config.model.split('/')[5]}-{cp_framework.config.probing_ratio}.csv"
    headers = ['valh', 'varh', 'timeout', 'objective', 'solvetime', 'round', 'ratio']
    dict_list = []
    for item in results_list:
      result_dict = {}
      if isinstance(item[0], dict):
        result_dict.update(item[0])
      for i, header in enumerate(headers[len(result_dict):], start=1):
        if i < len(item):
          result_dict[header] = item[i]
        else:
          result_dict[header] = None
      dict_list.append(result_dict)
    results_df = pd.DataFrame(dict_list)
    results_df.sort_values(by=['objective', 'solvetime'], ascending=[True, True], inplace=True)
    results_df.to_csv(file_name, index=False)
    print(f"Sorted results saved to {file_name}")
