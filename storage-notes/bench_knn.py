"""KNN throughput of the compute node, measured on the INSTALLED search path.

Calls protea_method.knn_search._search_numpy with synthetic arrays of the exact
production shape rather than reimplementing the kernel, so what is timed is the
code a worker would run. No database and no server load: the point is a ratio
between two machines, and a ratio does not need the real vectors. Both machines
running this file compare directly.
"""
import os, sys, time
import numpy as np

N_REF, DIM, K = 528_294, 1280, 30
rng = np.random.default_rng(0)

n_q = int(sys.argv[1])
import protea_method.knn_search as KS

R = rng.standard_normal((N_REF, DIM), dtype=np.float32)
Q = rng.standard_normal((n_q, DIM), dtype=np.float32)
acc = [f"P{i}" for i in range(N_REF)]

t0 = time.perf_counter()
out = KS._search_numpy(Q, R, acc, K, distance_threshold=None, metric="cosine")
dt = time.perf_counter() - t0

assert len(out) == n_q and len(out[0]) == K
print(f"  consultas {n_q:>7,}  ->  {dt:8.2f} s   {n_q/dt:8.1f} consultas/s")
