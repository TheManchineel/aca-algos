# Advanced Computer Architectures (ACA) Algorithms

This repository contains reference Python implementations of various algorithms explored in the ACA (*Advanced Computer Architectures*) or HPPS (*High Performance Processors and Systems*) course at *Politecnico di Milano*, as delivered by Prof. Santambrogio in A.Y. 2025/2026.

The main goal is aid in the study and understanding of the algorithms, as well as validate exercise solutions for exam preparation.

To run the code, simply run `python3 -m <algorithm_name>.py <algorithm_name>_in1.txt`.

Refer to the existing input files for the expected format. Most algorithms are parametrized and thus allow for input files with different parameters (more cache lines, CPUs, execution units, etc.)

## Implemented Algorithms:

 * `mesi` (MESI protocol for cache coherence, simulate state evolution given initial state and operations)
 * `mesi_inverse` (MESI protocol, inverse exercises where you need to find possible operations given cache state transitions)