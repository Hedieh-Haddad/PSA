"""
See PhD thesis by Adrien Varet (2022)
"""

from pycsp3 import *
from pycsp3.classes.auxiliary.ptypes import TypeHexagonSymmetry

def Benzenoide():
    with open('datavarval.txt', 'r') as f:
        varh = f.readline().strip()
        valh = f.readline().strip()
        phase = f.readline().strip()
        solver = f.readline().strip()
    n = data or 8  # order of the coronenoide
    w = 2 * n - 1  # maximal width
    widths = [w - abs(n - i - 1) for i in range(w)]

    symmetries = [sym.apply_on(n) for sym in TypeHexagonSymmetry]  # if sym.is_rotation()]


    def valid(*t):
        return [(i, j) for i, j in t if 0 <= i < w and 0 <= j < widths[i]]


    neighbors = [[valid(
        (i, j - 1), (i, j + 1),
        (i - 1, j - (1 if i < n else 0)), (i - 1, j + (0 if i < n else 1)),
        (i + 1, j - (1 if i >= n - 1 else 0)), (i + 1, j + (0 if i >= n - 1 else 1)))
        for j in range(widths[i])] for i in range(w)]


    def table(i, j):
        r = len(neighbors[i][j])
        return [(0, 0, *[ANY] * r)] + [(1, 1, *[ANY] * r)] + \
            [(2, 1, *[1 if j == i else ANY for j in range(r)]) for i in range(r)] + \
            [(v, 1, *[v - 1 if j == i else {0}.union(range(v - 1, n + 1)) for j in range(r)]) for v in range(3, n + 1) for i in range(r)]


    T = [(1, 1, 1, 1, 1, 1, 1)] + [(ANY, *[0 if j == i else ANY for j in range(6)]) for i in range(6)]

    # x[i][j] is 1 iff the hexagon at row i and column j is selected
    x = VarArray(size=[w, w], dom=lambda i, j: {0, 1} if j < widths[i] else None)

    # y[i][j] is the distance (+1) wrt the root of the connected tree
    y = VarArray(size=[w, w], dom=lambda i, j: range(n + 1) if j < widths[i] else None)

    satisfy(
        # only one root
        Count(y, value=1) == 1,

        # ensuring connectedness
        [(y[i][j], x[i][j], [y[k, l] for k, l in neighbors[i][j]]) in table(i, j) for i in range(w) for j in range(widths[i])],

        # exactly n hexagons
        Sum(x) == n,

        # ensuring no holes
        [(x[i][j], [x[k][l] for k, l in neighbors[i][j]]) in T for i in range(w) for j in range(widths[i]) if len(neighbors[i][j]) == 6],

        # tag(symmetry-breaking)
        [
            [LexDecreasing(x, [[x[k][l] for (k, l) in row] for row in sym]) for sym in symmetries],

            [Precedence(y, values=(1, v)) for v in range(2, n + 1)]

            # # at least one hexagon on the left
            # Sum(x[:, 0]) > 0,  # x[0][0] == 1
            #
            # # at least one hexagon on the top left
            # Sum(x[0] + x[1:n, 0]) > 0,

            # at least one hexagon on the two rightmost columns
            # Sum(x[i][widths[i]-2:] for i in range(w)) > 0
        ]
    )

    minimize(
        Sum(x[i][j] * ((n - i) * w + (n - j)) for i in range(w) for j in range(w) if j < widths[i])
    )

    """
    1) for being compatible with the competition mini-track, we use:
      z = VarArray(size=[w, w], dom=lambda i, j: {0, 1} if j < widths[i] else None)
    
      satisfy(
        # only one root
        [
            [(z[i][j], y[i][j]) in [(1, 1)] + [(0, v) for v in range(n + 1) if v != 1] for i in range(w) for j in range(widths[i])],
            Sum(z) == 1
        ],
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

Benzenoide()