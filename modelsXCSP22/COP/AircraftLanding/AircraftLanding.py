"""
Execution:
  python3 AircraftLanding.py -data=airland01.txt -dataparser=AircraftLanding_Parser.py
  python3 AircraftLanding.py -data=airland01.txt -dataparser=AircraftLanding_Parser.py -variant=table
"""
from pycsp3 import *

def aircraftlanding():
    with open('datavarval.txt', 'r') as f:
        varh = f.readline().strip()
        valh = f.readline().strip()
        phase = f.readline().strip()
        solver = f.readline().strip()
        restart = f.readline().strip()
        restartsequence = f.readline().strip()
        geocoef = f.readline().strip()

    nPlanes, times, costs, separations = data
    earliest, target, latest = zip(*times)
    early_penalties, late_penalties = zip(*costs)

    # x[i] is the landing time of the ith plane
    x = VarArray(size=nPlanes, dom=lambda i: range(earliest[i], latest[i] + 1))

    # e[i] is the earliness of the ith plane
    e = VarArray(size=nPlanes, dom=lambda i: range(target[i] - earliest[i] + 1))

    # t[i] is the tardiness of the ith plane
    t = VarArray(size=nPlanes, dom=lambda i: range(latest[i] - target[i] + 1))

    satisfy(
        # planes must land at different times
        AllDifferent(x),

        # the separation time required between any two planes must be satisfied:
        [NoOverlap(origins=[x[i], x[j]], lengths=[separations[i][j], separations[j][i]]) for i, j in combinations(range(nPlanes), 2)]
    )

    if not variant():
        satisfy(
            # computing earlinesses of planes
            [e[i] == max(0, target[i] - x[i]) for i in range(nPlanes)],

            # computing tardinesses of planes
            [t[i] == max(0, x[i] - target[i]) for i in range(nPlanes)],

        )
    elif variant("table"):
        satisfy(
            # computing earlinesses and tardinesses of planes
            (x[i], e[i], t[i]) in {(v, max(0, target[i] - v), max(0, v - target[i])) for v in range(earliest[i], latest[i] + 1)} for i in range(nPlanes)
        )

    minimize(
        # minimizing the deviation cost
        e * early_penalties + t * late_penalties
    )
    if solver == 'choco':
        if restart == "GEOMETRIC":
            solve(solver=solver, options=f"-f -varh={varh} -valh={valh} -best -last -lc 1 -restarts [GEOMETRIC,{restartsequence},{geocoef},50000,true]") # -restarts [GEOMETRIC,500,0,50000,true]
        elif restart == "luby":
            solve(solver=solver, options=f"-f -varh={varh} -valh={valh} -best -last -lc 1 -restarts [luby,{restartsequence},0,50000,true]")

    elif solver == 'ace':
        if restart == "GEOMETRIC":
            solve(solver=solver, options=f"-varh={varh} -valh={valh} -r_n={restartsequence} -ref="" ")
        elif restart == "luby":
            solve(solver=solver, options=f"-varh={varh} -valh={valh} -luby -r_n={restartsequence} -ref="" ")
    print("NSolution" , n_solutions())
    print("Objective" , bound())
    print("Status" , status())
    print("Solution" , solution())
    return n_solutions() , bound() , status() , solution()

aircraftlanding()

