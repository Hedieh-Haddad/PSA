"""
See Problem 040 on CSPLib
"""

from pycsp3 import *
from math import floor, gcd
from functools import reduce

def EchelonStock():
    with open('datavarval.txt', 'r') as f:
        varh = f.readline().strip()
        valh = f.readline().strip()
        phase = f.readline().strip()
        solver = f.readline().strip()

    children, hcosts, pcosts, demands = data
    n, nPeriods, nLeaves = len(children), len(demands[0]), len(demands)

    simplification = True
    if simplification:
        g = reduce(gcd, {v for row in demands for v in row})
        demands = [[row[t] // g for t in range(nPeriods)] for row in demands]
        hcosts = [hcosts[i] * g for i in range(n)]

    sumDemands, allDemands = [], []
    for i in range(n):
        sumDemands.append(sum(demands[i]) if i < nLeaves else sum(sumDemands[j] for j in children[i]))
        allDemands.append([sum(demands[i][t:]) for t in range(nPeriods)] if i < nLeaves else [sum(allDemands[j][t] for j in children[i]) for t in range(nPeriods)])

    print(sumDemands, allDemands, children, hcosts, pcosts, demands)


    def ratio1(i, coeff=1):
        parent = next(j for j in range(n) if i in children[j])  # use a cache instead, if necessary (i., precompute parents)
        return floor(pcosts[i] // (coeff * (hcosts[i] - hcosts[parent])))


    def ratio2(i, t_inf):
        return min(sum(demands[i][t_inf: t_sup + 1]) + ratio1(i, t_sup - t_inf + 1) for t_sup in range(t_inf, nPeriods))


    def domain_x(i, t):  # ratio2 from IC4, and allDemands from IC6a
        return range(min(allDemands[i][t], ratio2(i, t)) + 1) if i < nLeaves else range(allDemands[i][t] + 1)


    def domain_y(i, t):  # {0} from IC1, ratio1 from IC3 and allDemands from IC6b (which generalizes IC1)
        return {0} if t == nPeriods - 1 else range(min(allDemands[i][t + 1], ratio1(i)) + 1) if i < n - 1 else range(allDemands[i][t + 1] + 1)


    # x[i][t] is the amount ordered at node i at period (time) t
    x = VarArray(size=[n, nPeriods], dom=domain_x)

    # y[i][t] is the amount stocked at node i at the end of period t
    y = VarArray(size=[n, nPeriods], dom=domain_y)

    satisfy(
        [y[i][0] == x[i][0] - demands[i][0] for i in range(nLeaves)],

        [y[i][t] - Sum(y[i][t - 1], x[i][t]) == -demands[i][t] for i in range(nLeaves) for t in range(1, nPeriods)],

        [y[i][0] == x[i][0] - Sum(x[j][0] for j in children[i]) for i in range(nLeaves, n)],

        [y[i][t] == y[i][t - 1] + x[i][t] - Sum(x[j][t] for j in children[i]) for i in range(nLeaves, n) for t in range(1, nPeriods)],

        # IC2
        [(x[i][t] == 0) | disjunction(x[j][t] > 0 for j in children[i]) for i in range(nLeaves, n) for t in range(nPeriods)],

        # IC5
        [(y[i][t - 1] == 0) | (x[i][t] == 0) for i in range(n) for t in range(1, nPeriods)],

        # tag(redundant-constraints)
        [Sum(x[i]) == sumDemands[i] for i in range(n)],

        [y[i][t - 1] + Sum(x[i][t:]) == allDemands[i][t] for i in range(nLeaves) for t in range(1, nPeriods)]
    )

    minimize(
        Sum(hcosts[i] * y[i][t] for i in range(n) for t in range(nPeriods))
        + Sum(pcosts[i] * (x[i][t] > 0) for i in range(n) for t in range(nPeriods))
    )

    # note that:
    # a) IC4, simple version is: [x[i][t] <= demands[i][t] + ratio(i) for i in range(nLeaves) for t in range(nPeriods)],
    # b) using only one Sum when posting the objective generates a complex XCSP3 expression
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


EchelonStock()