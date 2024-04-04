"""
See Problem 069 on CSPLib
    
"""

from pycsp3 import *

def NursingWorkload():
    with open('datavarval.txt', 'r') as f:
        varh = f.readline().strip()
        valh = f.readline().strip()
        phase = f.readline().strip()
        solver = f.readline().strip()
        restart = f.readline().strip()
        restartsequence = f.readline().strip()
        geocoef = f.readline().strip()

    nNurses, minPatientsPerNurse, maxPatientsPerNurse, maxWorkloadPerNurse, demands = data
    patients = [(i, demand) for i, t in enumerate(demands) for demand in t]
    nPatients, nZones = len(patients), len(demands)

    lb = sum(sorted([demand for i, t in enumerate(demands) for demand in t])[:minPatientsPerNurse])

    # p[i] is the nurse assigned to the ith patient
    p = VarArray(size=nPatients, dom=range(nNurses))

    # w[k] is the workload of the kth nurse
    w = VarArray(size=nNurses, dom=range(lb, maxWorkloadPerNurse + 1))

    satisfy(
        Cardinality(p, occurrences={k: range(minPatientsPerNurse, maxPatientsPerNurse + 1) for k in range(nNurses)}),

        [p[i] != p[j] for i, j in combinations(range(nPatients), 2) if patients[i][0] != patients[j][0]],

        [w[k] == Sum(c * (p[i] == k) for i, (_, c) in enumerate(patients)) for k in range(nNurses)],

        # tag(symmetry-breaking)
        [p[z] == z for z in range(nZones)],

        Increasing(w)
    )

    minimize(
        Sum(w[k] * w[k] for k in range(nNurses))
    )

    if solver == 'choco':
        if restart == "GEOMETRIC":
            solve(solver=solver,
                  options=f"-f -varh={varh} -valh={valh} -best -last -lc 1 -restarts [GEOMETRIC,{restartsequence},{geocoef},50000,true]")  # -restarts [GEOMETRIC,500,0,50000,true]
        elif restart == "luby":
            solve(solver=solver,
                  options=f"-f -varh={varh} -valh={valh} -best -last -lc 1 -restarts [luby,{restartsequence},0,50000,true]")

    elif solver == 'ace':
        if restart == "GEOMETRIC":
            solve(solver=solver, options=f"-varh={varh} -valh={valh} -r_n={restartsequence} -ref="" ")
        elif restart == "luby":
            solve(solver=solver, options=f"-varh={varh} -valh={valh} -luby -r_n={restartsequence} -ref="" ")
    print("NSolution", n_solutions())
    print("Objective", bound())
    print("Status", status())
    print("Solution", solution())
    return n_solutions(), bound(), status(), solution()


NursingWorkload()