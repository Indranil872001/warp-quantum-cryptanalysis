"""
OPTIONAL small-component IBM-hardware runner.

This is NOT needed for the paper's core results.
Use it only if you choose to obtain small-module hardware measurements.

Requires:
    pip install qiskit-ibm-runtime

Credentials must be configured by the user through the IBM Quantum Platform.
Do not place API keys in source code.
"""

def main():
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError:
        raise SystemExit("Install qiskit-ibm-runtime first.")

    service=QiskitRuntimeService()
    backends=service.backends(simulator=False,operational=True)
    if not backends:
        raise SystemExit("No accessible operational QPU found.")
    for b in backends:
        print(b.name)

if __name__=="__main__":
    main()
