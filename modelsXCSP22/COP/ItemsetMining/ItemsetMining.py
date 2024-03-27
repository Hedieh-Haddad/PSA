"""
Minizinc 2011, 2012 (k1 and k2 only differ from: K=1 or K=2) and 2013
"""

from pycsp3 import *

def ItemsetMining():
    with open('datavarval.txt', 'r') as f:
        varh = f.readline().strip()
        valh = f.readline().strip()
        phase = f.readline().strip()
        solver = f.readline().strip()

    nItems, positiveExamples, negativeExamples, k = data
    nPos, nNeg = len(positiveExamples), len(negativeExamples)

    # precomputing three auxiliary complementary sets
    pComp = [[i for i in range(nItems) if i not in t] for t in positiveExamples]  # complementary
    nComp = [[i for i in range(nItems) if i not in t] for t in negativeExamples]
    citm = [[t for t in range(nPos) if i not in positiveExamples[t]] for i in range(nItems)]

    if k == 1:
        x = VarArray(size=[nItems], dom={0, 1})

        tp = VarArray(size=[nPos], dom={0, 1})
        tn = VarArray(size=[nNeg], dom={0, 1})

        if not variant():
            satisfy(
                [tp[t] == (Count(x[i] for i in pComp[t]) <= 0) for t in range(nPos) if len(pComp[t]) > 0],
                [tn[t] == (Count(x[i] for i in nComp[t]) <= 0) for t in range(nNeg) if len(nComp[t]) > 0],
                [x[i] == (Count(tp[t] for t in citm[i]) <= 0) for i in range(nItems) if len(citm[i]) > 0]
            )
        elif variant("table"):
            def table(r):
                return [tuple([1, *(0 for _ in range(r))])] + [tuple([0, *(1 if j == i else ANY for j in range(r))]) for i in range(r)]


            satisfy(
                [(tp[t], [x[i] for i in pComp[t]]) in table(len(pComp[t])) for t in range(nPos) if len(pComp[t]) > 0],
                [(tn[t], [x[i] for i in nComp[t]]) in table(len(nComp[t])) for t in range(nNeg) if len(nComp[t]) > 0],
                [(x[i], [tp[t] for t in citm[i]]) in table(len(citm[i])) for i in range(nItems) if len(citm[i]) > 0]
            )

        maximize(
            Sum(tp) - Sum(tn)
        )

    else:
        x = VarArray(size=[k, nItems], dom={0, 1})

        tp = VarArray(size=[k, nPos], dom={0, 1})
        tn = VarArray(size=[k, nNeg], dom={0, 1})

        jtp = VarArray(size=nPos, dom={0, 1})
        jtn = VarArray(size=nNeg, dom={0, 1})

        satisfy(
            [tp[d, t] == (Count(x[d, i] for i in pComp[t]) <= 0) for d in range(k) for t in range(nPos) if len(pComp[t]) > 0],
            [tn[d, t] == (Count(x[d, i] for i in nComp[t]) <= 0) for d in range(k) for t in range(nNeg) if len(nComp[t]) > 0],
            [x[d, i] == (Count(tp[d, t] for t in citm[i]) <= 0) for d in range(k) for i in range(nItems) if len(citm[i]) > 0],

            [jtp[t] == tp[0][t] | tp[1][t] for t in range(nPos)],
            [jtn[t] == tn[0][t] | tn[1][t] for t in range(nNeg)],

            # tag(symmetry-breaking)
            [
                LexIncreasing(tp, strict=True),
                LexIncreasing(tn, strict=True)
            ]
        )

        maximize(
            Sum(jtp) - Sum(jtn)
        )

    """ Comments
    0) BE CAREFUL: strict LexIncreasing discards some better solutions; this should be less or equal in a flawless model
    1) using Count instead of Sum seems more efficient (because of the domain size of the auxiliary variables?)
    2) using starred tables instead of Count is not efficient    
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

ItemsetMining()