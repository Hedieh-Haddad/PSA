"""
This problem is about optimizing the scheduling of filter operations, commonly used in High-Level Synthesis.
This model has been originally written by Krzysztof Kuchcinski for the 2010, 2012, 2013 and 2016 Minizinc competitions.

See also the models in JaCop -- https://github.com/radsz/jacop/tree/develop/src/main/java/org/jacop/examples/fd/filters
"""

from pycsp3 import *

def Filters():
    with open('datavarval.txt', 'r') as f:
        varh = f.readline().strip()
        valh = f.readline().strip()
        phase = f.readline().strip()
        solver = f.readline().strip()
        restart = f.readline().strip()
        restartsequence = f.readline().strip()
        geocoef = f.readline().strip()

    del_add, del_mul, number_add, number_mul, last, add, dependencies = data
    nOperations = len(dependencies)

    d = [del_add if i in add else del_mul for i in range(nOperations)]
    mul = [i for i in range(nOperations) if i not in add]

    # t[i] is the starting time of the ith operation
    t = VarArray(size=nOperations, dom=range(101))

    # r[i] is the (index of the) operator used for the ith operation
    r = VarArray(size=nOperations, dom=lambda i: range(1, 1 + (number_add if i in add else number_mul)))

    satisfy(
        # respecting dependencies
        [t[i] + d[i] <= t[j] for i in range(nOperations) for j in dependencies[i]],

        # no overlap concerning add operations
        NoOverlap(origins=[(t[i], r[i]) for i in add], lengths=[(del_add, 1) for i in add]),

        # no overlap concerning mul operations
        NoOverlap(origins=[(t[i], r[i]) for i in mul], lengths=[(del_mul, 1) for i in mul])
    )

    minimize(
        # minimizing the ending time of last operations
        Maximum(t[i] + d[i] for i in last)
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

Filters()