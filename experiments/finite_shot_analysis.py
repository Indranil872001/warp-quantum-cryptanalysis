"""
Finite-shot analysis aligned with the uploaded Mini-AES paper but using the
exact Grover formula and exact binomial tail probabilities.

For u=8 unknown bits:
  N=256, M=1, shots=1024.

We report:
- exact success probability p_k;
- expected marked-key count S p_k;
- standard deviation sqrt(S p (1-p));
- 95% normal-approximation count interval (for readability);
- exact probability that the observed marked-key count reaches threshold T=100.

This lets us reproduce the paper's "count threshold" style without confusing
it with a reduction in asymptotic Grover query complexity.
"""

import math,csv
from scipy.stats import binom
from partial_key_grover import closed_form_success

N=256
M=1
S=1024
T=100

def run():
    rows=[]
    for k in range(0,13):
        p=closed_form_success(N,M,k)
        mu=S*p
        sd=math.sqrt(S*p*(1-p))
        # P(C >= T)
        tail=float(binom.sf(T-1,S,p))
        rows.append({
            "iterations":k,
            "success_probability":p,
            "expected_count":mu,
            "count_sd":sd,
            "approx95_low":max(0,mu-1.96*sd),
            "approx95_high":min(S,mu+1.96*sd),
            "prob_count_ge_100":tail,
        })
    return rows

if __name__=="__main__":
    rows=run()
    with open("FINITE_SHOT_1024.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    for r in rows: print(r)
    first=next(r for r in rows if r["expected_count"]>=T)
    print("First k with expected count >=100:",first["iterations"])
