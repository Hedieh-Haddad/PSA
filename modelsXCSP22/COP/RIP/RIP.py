"""
Resource Investment problem (also known as RACP)
"""

from pycsp3 import *

def RIP():
    with open('datavarval.txt', 'r') as f:
        varh = f.readline().strip()
        valh = f.readline().strip()
        phase = f.readline().strip()
        solver = f.readline().strip()
    horizon, costs, tasks = data
    durations, successors, requirements = zip(*tasks)
    nResources, nTasks = len(costs), len(tasks)
    requirements = [[r[k] for r in requirements] for k in range(nResources)]

    lb_usage = [max(row) for row in requirements]
    ub_usage = [sum(row) for row in requirements]

    # s[i] is the starting time of the ith task
    s = VarArray(size=nTasks, dom=range(horizon + 1))

    # u[k] is the maximal usage (at any time) of the kth resource
    u = VarArray(size=nResources, dom=lambda k: range(lb_usage[k], ub_usage[k] + 1))

    satisfy(
        # ending tasks before the given horizon
        [s[i] + durations[i] <= horizon for i in range(nTasks)],

        # respecting precedence relations
        [s[i] + durations[i] <= s[j] for i in range(nTasks) for j in successors[i]],

        # cumulative resource constraints
        [Cumulative(origins=s, lengths=durations, heights=requirements[k]) <= u[k] for k in range(nResources)]
    )

    minimize(
        # minimizing weighted usage of resources
        costs * u
    )

    """
    1) costs * u
       is a shortcut for 
     Sum(costs[r] * u[r] for r in range(nResources))
    """
    if solver == 'choco':
        solve(solver=solver,
              options=f"-f -varh={varh} -valh={valh} -best -last -lc 1 -restarts [luby,500,0,50000,true]")
    elif solver == 'ace':
        solve(solver=solver, options=f"-varh={varh} -valh={valh} -luby -r_n=500")  # -lc
    print("NSolution", n_solutions())
    print("Objective", bound())
    print("Status", status())
    print("Solution", solution())
    return n_solutions(), bound(), status(), solution()

RIP()