# Spatio-Temporal Modeling and Software-Based Mitigation of Crosstalk in Quantum Computing

This repository contains the software implementation for generating a time-dependent crosstalk model on Noisy Intermediate-Scale Quantum (NISQ) devices, alongside our "Smart Staggering" software-based mitigation strategy.

## Repository Structure  
* `src/`: Core logic containing the custom Qiskit `UltimateCrosstalkModel` (integrating distance decay and coherent phase errors), circuit generators, and scheduling strategies.  
* `experiments/`: Evaluation scripts to benchmark Hellinger vs. State fidelity, plot the invisible "Information Gap," and calculate the normalized execution cost of our Smart Staggering method.

## Installation  
```bash  
git clone https://github.com/Mao3831/Quantum_CT_SoftwareMitigation.git
cd Quantum_CT_SoftwareMitigation  
pip install -r requirements.txt  
```
