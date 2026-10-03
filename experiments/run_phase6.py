from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import csv,json
from sparse_gatelevel_grover import run_gatelevel_demo
from finite_shot_analysis import run as run_finite
from component_noise import run as run_noise

def main():
    demos=[
        run_gatelevel_demo(8,0,1,1024,2026),
        run_gatelevel_demo(8,0,2,1024,2027),
    ]
    with open("GATELEVEL_GROVER_DEMO.json","w") as f:
        json.dump(demos,f,indent=2)

    fs=run_finite()
    with open("FINITE_SHOT_1024.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(fs[0]))
        w.writeheader(); w.writerows(fs)

    noise=run_noise()
    with open("COMPONENT_NOISE.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(noise[0]))
        w.writeheader(); w.writerows(noise)

    print("GATE-LEVEL GROVER:")
    print(json.dumps(demos,indent=2))
    print("\nFINITE SHOT:")
    for r in fs: print(r)
    print("\nCOMPONENT NOISE:")
    for r in noise: print(r)

if __name__=="__main__":
    main()
