# Local Qiskit setup — IBM account NOT required

## Recommended isolated environment

### Windows / PowerShell

```powershell
py -3.12 -m venv warp-qiskit
.\warp-qiskit\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install "qiskit~=2.5.0" "qiskit-aer==0.17.2" numpy scipy matplotlib
```

### Linux / WSL

```bash
python3 -m venv warp-qiskit
source warp-qiskit/bin/activate
python -m pip install --upgrade pip
pip install "qiskit~=2.5.0" "qiskit-aer==0.17.2" numpy scipy matplotlib
```

That is enough for local circuit construction and Aer simulation.

## IBM access is optional

Only install the cloud client if you want IBM hardware or IBM cloud services:

```bash
pip install qiskit-ibm-runtime
```

For local testing, IBM's current runtime client supports a local channel and
does not require authentication.

For real IBM QPUs you need an IBM Cloud / IBM Quantum account, an API key,
and an accessible service instance.

## What to run first

```bash
python qiskit_local_components.py
```

This builds the verified 4-qubit Sb0 and 8-qubit S-XOR circuits locally and
runs their truth tables with Aer.  These small modules are the appropriate
place to begin real-hardware experiments if you later choose to use an IBM
QPU.

Do NOT try to run the full 381--637 qubit WARP Grover oracle on current
hardware merely to imitate the Mini-AES paper.  Our paper should state clearly
that full-WARP execution is a fault-tolerant resource-estimation target.
