"""
LPCP contest 2022 (Problem 2)

See https://github.com/lpcp-contest/lpcp-contest-2022/tree/main/problem-2
"""

from pycsp3 import *

def BeerJugs():
    with open('datavarval.txt', 'r') as f:
        varh = f.readline().strip()
        valh = f.readline().strip()
        phase = f.readline().strip()
        solver = f.readline().strip()
    if isinstance(data, int):  # index of data used in the contest
        A, B, MAX = *[(3, 4), (3, 10), (7, 10), (9, 10), (5, 12), (7, 12), (11, 12), (11, 14), (11, 16), (13, 16), (15, 16)][data], 70
    else:
        A, B, MAX = data

    STOP, FILL_A, FILL_B, DROP_A, DROP_B, A_TO_B, B_TO_A = Actions = range(-1, 6)


    def execute(q1, q2, action):
        if action == STOP:
            return -1, -1
        if action == FILL_A:
            return (A, q2) if q1 != A else None
        if action == FILL_B:
            return (q1, B) if q2 != B else None
        if action == DROP_A:
            return (0, q2) if q1 > 0 else None
        if action == DROP_B:
            return (q1, 0) if q2 > 0 else None
        if action == A_TO_B:
            pour = min(q1, B - q2)
            return (q1 - pour, q2 + pour) if pour > 0 else None
        if action == B_TO_A:
            pour = min(A - q1, q2)
            return (q1 + pour, q2 - pour) if pour > 0 else None


    valid_actions = [(q1, q2, a) for q1 in range(A + 1) for q2 in range(B + 1) for a in Actions if execute(q1, q2, a)]
    T = [(-1, -1, -1, -1, -1)] + [(q1, q2, a, *execute(q1, q2, a)) for q1, q2, a in valid_actions]

    # x[t][i] is the quantity in the ith jug (i is equal to 0 for A and 1 for B) at time t
    x = VarArray(size=[MAX + 1, 2], dom=lambda i, j: {0} if i == 0 else range(-1, (A if j == 0 else B) + 1))

    # y[t] is the action taken at time t (to t+1)
    y = VarArray(size=MAX, dom=Actions)

    # z is the time when the process is stopped
    z = Var(range(MAX))

    satisfy(
       # ensuring that the same state is never encountered several times
       [(s1[0] != s2[0]) | (s1[1] != s2[1]) | (s1[0] == -1) for s1, s2 in combinations(x, 2)],

        # computing the consequences of each action
        [(x[t][0], x[t][1], y[t], x[t + 1][0], x[t + 1][1]) in T for t in range(MAX)],

        # ensuring a stable state (-1, -1) when the process is finished
        [(t < z) == (y[t] != STOP) for t in range(MAX)]
    )

    maximize(
        # maximizing the length of the sequence of actions
        z
    )

    """
    1) for being compatible with the competition mini-track, we use:
       [(z,y[t]) in [(v,STOP) for v in range(t+1)] + [(v,w) for v in range(t+1,MAX) for w in Actions if w != STOP] for t in range(MAX)]
    """
    if solver == 'choco':
        solve(solver=solver, options=f"-f -varh={varh} -valh={valh} -best -last -lc 1 -restarts [luby,500,0,50000,true]")
    elif solver == 'ace':
        solve(solver=solver, options=f"-varh={varh} -valh={valh} -luby -r_n=500") # -lc
    print("NSolution" , n_solutions())
    print("Objective" , bound())
    print("Status" , status())
    print("Solution" , solution())
    return n_solutions() , bound() , status() , solution()

BeerJugs()