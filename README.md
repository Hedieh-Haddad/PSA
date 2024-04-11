Hyperparameter Optimisation of Constraint Programming Solvers
=============================================================

# Requirements

```
pip install scikit-optimize pycsp3
```

# How to run?

```
python3 main.py --model ../benchmarks/mzn-challenge/2022/accap/accap.mzn --data ../benchmarks/mzn-challenge/2022/accap/accap_a4_f30_t15.json --solver choco --timeout 600 --hpo bayesian --rounds 30 --probing_ratio 0.2 --hyperparameters_search Block_Search
```