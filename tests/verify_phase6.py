from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'experiments'))

import json
from sparse_gatelevel_grover import (
    quantum_gate_encrypt_hex, run_gatelevel_demo,
    KEY_HEX,P1_HEX,C1_HEX,P2_HEX,C2_HEX
)
from finite_shot_analysis import run as run_finite
from component_noise import run as run_noise

def main():
    assert quantum_gate_encrypt_hex(KEY_HEX,P1_HEX)==C1_HEX
    assert quantum_gate_encrypt_hex(KEY_HEX,P2_HEX)==C2_HEX
    print("PASS: gate-level 41-round encryption matches both official pairs")

    d1=run_gatelevel_demo(8,0,1,1024,2026)
    d2=run_gatelevel_demo(8,0,2,1024,2027)
    assert d1["M"]==1 and d2["M"]==1
    assert d1["true_candidate"] in d1["marked"]
    assert d2["true_candidate"] in d2["marked"]
    assert abs(d1["success_numeric"]-d1["success_theory"])<1e-12
    assert abs(d2["success_numeric"]-d2["success_theory"])<1e-12
    print("PASS: exact sparse gate-oracle Grover recovery for one and two pairs")

    rows=run_finite()
    assert rows[3]["expected_count"] >= 100
    assert rows[2]["expected_count"] < 100
    print("PASS: finite-shot threshold crossing occurs first at k=3")

    nr=run_noise(seed=7)
    assert all(0 <= r["success"] <= 1 for r in nr)
    print("PASS: component-noise experiment generated valid probabilities")

if __name__=="__main__":
    main()
