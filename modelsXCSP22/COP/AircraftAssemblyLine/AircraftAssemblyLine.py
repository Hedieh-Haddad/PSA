"""
This problem has been proposed by Stephanie Roussel from ONERA (Toulouse), and comes from an aircraft manufacturer.
The objective is to schedule tasks on an aircraft assembly line in order to minimize the overall number of operators required on the line.
The schedule must satisfy several operational constraints, the main ones of which are as follows:
- tasks are assigned on a unique workstation (on which specific machines are available);
- the takt-time, i.e. the duration during which the aircraft stays on each workstation, must be respected;
- capacity of aircraft zones in which operators perform the tasks must never be exceeded;
- zones can be neutralized by some tasks, i.e. it is not possible to work in those zones during the tasks execution.

This PyCSP3 model has been co-developed by teams of ONERA and CRIL.

Examples of Execution:
  python AircraftAssemblyLine.py -data=1-178-00-0.json -dataparser=AircraftAssemblyLine_Converter.py
"""
from pycsp3 import *

def AircraftAssemblyLine():
    with open('datavarval.txt', 'r') as f:
        varh = f.readline().strip()
        valh = f.readline().strip()
        phase = f.readline().strip()
        solver = f.readline().strip()
    takt, areas, stations, tasks, tasksPerMachine, precedences = data
    nAreas, nStations, nTasks, nMachines = len(areas), len(stations), len(tasks), len(tasksPerMachine)

    areaCapacities, areaTasks = zip(*areas)  # number of operators who can work, and tasks per area
    stationMachines, stationMaxOperators = zip(*stations)
    durations, operators, usedAreaRooms, neutralizedAreas = zip(*tasks)
    usedAreas = [set(j for j in range(nAreas) if usedAreaRooms[i][j] > 0) for i in range(nTasks)]


    def station_of_task(i):
        r = next((j for j in range(nMachines) if i in tasksPerMachine[j]), -1)
        return -1 if r == -1 else next(j for j in range(nStations) if stationMachines[j][r] == 1)


    stationOfTasks = [station_of_task(i) for i in range(nTasks)]  # station of the ith task (-1 if can be everywhere)

    # x[i] is the starting time of the ith task
    x = VarArray(size=nTasks, dom=range(takt * nStations + 1))

    # z[j] is the number of operators at the jth station
    z = VarArray(size=nStations, dom=lambda i: range(stationMaxOperators[i] + 1))

    satisfy(
        # respecting the final deadline
        [x[i] + durations[i] <= takt * nStations for i in range(nTasks)],

        # ensuring that tasks start and finish in the same station
        [(x[i] // takt) == ((x[i] + max(0, durations[i] - 1)) // takt) for i in range(nTasks) if durations[i] != 0],

        # ensuring that tasks are put on the right stations (wrt needed machines)
        [(x[i] // takt) == stationOfTasks[i] for i in range(nTasks) if stationOfTasks[i] != -1],

        # respecting precedence relations
        [x[i] + durations[i] <= x[j] for (i, j) in precedences],

        # respecting limit capacities of areas
        [Cumulative(tasks=[(x[t], durations[t], usedAreaRooms[t][i]) for t in areaTasks[i]]) <= areaCapacities[i] for i in range(nAreas) if len(areaTasks[i]) > 1],

        # computing/restricting the number of operators at each station
        [Cumulative(tasks=[(x[t], durations[t], operators[t] * (x[t] // takt == j)) for t in range(nTasks)]) <= z[j] for j in range(nStations)],

        # no overlap (is there a better way to handle that?)
        [NoOverlap(tasks=[(x[i], durations[i]), (x[j], durations[j])]) for i in range(nTasks) for j in range(nTasks) if i != j and
         len(usedAreas[i].intersection(neutralizedAreas[j])) > 0],

        # avoiding tasks using the same machine to overlap
        [NoOverlap(tasks=[(x[j], durations[j]) for j in tasksPerMachine[i]]) for i in range(nMachines) if len(tasksPerMachine[i]) > 1]
    )

    minimize(
        # minimizing the number of operators
        Sum(z)
    )
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


AircraftAssemblyLine()

