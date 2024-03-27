"""
See 'Constraint Solving and Planning with Picat' (page 43)
From Tony Hurlimann, A coin puzzle, SVOR-contest 2007

Some data: (8,4) (8,5) (9,4) (10,4) (31,14)

Examples of Execution:
  python3 CoinsGrid.py
  python3 CoinsGrid.py -data=[10,4]
"""

from pycsp3 import *

def CoinsGrid():
    with open('datavarval.txt', 'r') as f:
        varh = f.readline().strip()
        valh = f.readline().strip()
        phase = f.readline().strip()
        solver = f.readline().strip()

    n, c = data or (8, 4)

    # x[i][j] is 1 if a coin is placed at row i and column j
    x = VarArray(size=[n, n], dom={0, 1})

    satisfy(
        [Sum(x[i]) == c for i in range(n)],

        [Sum(x[:, j]) == c for j in range(n)]
    )

    minimize(
        Sum(x[i][j] * abs(i - j) ** 2 for i in range(n) for j in range(n))
    )

    """ Comments
    1) there are other variants in Hurlimann's paper (TODO)
    """
    if solver == 'choco':
        solve(solver=solver, options=f"-f -varh={varh} -valh={valh} -best -last -lc 1 -restarts [luby,500,0,50000,true]")
    elif solver == 'ace':
        solve(solver=solver, options=f"-varh={varh} -valh={valh} -luby -r_n=500") # -lc    print("NSolution" , n_solutions())
    print("NSolution", n_solutions())
    print("Objective", bound())
    print("Status", status())
    print("Solution", solution())
    return n_solutions(), bound(), status(), solution()


CoinsGrid()
