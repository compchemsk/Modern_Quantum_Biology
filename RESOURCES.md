# 📚 Books, reviews, software & people

Background for the [BioQubit Atlas](https://compchemsk.github.io/Modern_Quantum_Biology/): what to read to get into the field, the tools used to simulate it, and where the community meets. Generated from `config/resources.yaml` — edit that file, not this one.

> 🧭 **Suggested path for a newcomer**
> 1. *Life on the Edge* — the big picture, in a weekend.
> 2. Hore & Mouritsen (2016), then Rodgers & Hore (2009) — the radical-pair mechanism properly.
> 3. Kim et al. (2021) and Cao et al. (2020) — the state of the whole field.
> 4. Breuer & Petruccione, chapters 3–4 — the open-quantum-systems tools you will actually use.
> 5. Then the Biological qubits section of the Atlas.

## Books

### Getting oriented

| Book | Why read it |
|---|---|
| J. McFadden & J. Al-Khalili, ***Life on the Edge: The Coming of Age of Quantum Biology*** (2014) | Readable tour of tunnelling, photosynthesis, the avian compass and more. The best first book. |
| M. Mohseni, Y. Omar, G. S. Engel & M. B. Plenio (eds.), ***Quantum Effects in Biology***, Cambridge University Press (2014) | Graduate-level edited volume; chapters on radical pairs, energy transfer and decoherence by the people who did the work. |
| E. Schrödinger, ***What Is Life?*** (1944) | The historical starting point the field still quotes. |

### Spin chemistry & magnetic resonance

| Book | Why read it |
|---|---|
| H. Hayashi, ***Introduction to Dynamic Spin Chemistry***, World Scientific (2004) | Compact textbook on radical-pair spin dynamics and magnetic field effects, including biochemical reactions. |
| A. Schweiger & G. Jeschke, ***Principles of Pulse Electron Paramagnetic Resonance***, Oxford University Press (2001) | The reference for spin Hamiltonians and pulse sequences — essential for ODMR-type protein-qubit work. |
| J. A. Weil & J. R. Bolton, ***Electron Paramagnetic Resonance: Elementary Theory and Practical Applications***, Wiley (2007) | Gentler EPR introduction; good for hyperfine and g-tensor basics. |
| M. H. Levitt, ***Spin Dynamics: Basics of Nuclear Magnetic Resonance***, Wiley (2008) | Spin operators, density matrices and relaxation, directly reusable for radical pairs and nuclear-spin problems. |

### Open quantum systems & quantum information

| Book | Why read it |
|---|---|
| H.-P. Breuer & F. Petruccione, ***The Theory of Open Quantum Systems***, Oxford University Press (2002) | Master equations, Lindblad and Redfield theory, decoherence — the core for any ‘does coherence survive in a protein?’ question. |
| M. A. Nielsen & I. L. Chuang, ***Quantum Computation and Quantum Information***, Cambridge University Press (2010) | Qubits, gates, fidelity and entanglement — the language protein-qubit papers borrow. |
| U. Weiss, ***Quantum Dissipative Systems***, World Scientific (2012) | Spin–boson model and system–bath theory in depth. |

## Landmark reviews & papers

| Reference | One line |
|---|---|
| P. J. Hore & H. Mouritsen, Annu. Rev. Biophys. 45, 299–344 (2016), “The radical-pair mechanism of magnetoreception”. [doi:10.1146/annurev-biophys-032116-094545](https://doi.org/10.1146/annurev-biophys-032116-094545) | The standard review of the avian compass. |
| C. T. Rodgers & P. J. Hore, PNAS 106, 353–360 (2009), “Chemical magnetoreception in birds: the radical pair mechanism”. [doi:10.1073/pnas.0711968106](https://doi.org/10.1073/pnas.0711968106) | Clear physical introduction to radical-pair magnetosensitivity. |
| T. Ritz, S. Adem & K. Schulten, Biophys. J. 78, 707–718 (2000), “A model for photoreceptor-based magnetoreception in birds”. [doi:10.1016/S0006-3495(00)76629-X](https://doi.org/10.1016/S0006-3495(00)76629-X) | Proposed cryptochrome as the compass molecule. |
| K. Schulten, C. E. Swenberg & A. Weller, Z. Phys. Chem. NF 111, 1–5 (1978), “A biomagnetic sensory mechanism based on magnetic field modulated coherent electron spin motion”. | Where the radical-pair compass idea began. |
| U. E. Steiner & T. Ulrich, Chem. Rev. 89, 51–147 (1989), “Magnetic field effects in chemical kinetics and related phenomena”. [doi:10.1021/cr00091a003](https://doi.org/10.1021/cr00091a003) | Encyclopaedic foundation of spin chemistry. |
| K. Maeda et al., Nature 453, 387–390 (2008), “Chemical compass model of avian magnetoreception”. [doi:10.1038/nature06834](https://doi.org/10.1038/nature06834) | First demonstration that a molecule can sense the direction of an Earth-strength field. |
| N. Lambert et al., Nat. Phys. 9, 10–18 (2013), “Quantum biology”. [doi:10.1038/nphys2474](https://doi.org/10.1038/nphys2474) | Influential field-wide review. |
| J. Cao et al., Sci. Adv. 6, eaaz4888 (2020), “Quantum biology revisited”. [doi:10.1126/sciadv.aaz4888](https://doi.org/10.1126/sciadv.aaz4888) | Critical reassessment of what is and isn't established. |
| Y. Kim et al., Quantum Rep. 3, 80–126 (2021), “Quantum biology: an update and perspective”. [doi:10.3390/quantum3010006](https://doi.org/10.3390/quantum3010006) | Broad open-access survey: enzymes, photosynthesis, spins, DNA, fluorescent proteins. |
| I. K. Kominis, Phys. Rev. E 80, 056115 (2009), “Quantum Zeno effect explains magnetic-sensitive radical-ion-pair reactions”. [doi:10.1103/PhysRevE.80.056115](https://doi.org/10.1103/PhysRevE.80.056115) | The open-quantum-systems view of radical-pair recombination. |

## Software

| Tool | What it does |
|---|---|
| **[RadicalPy](https://github.com/Spin-Chemistry-Labs/radicalpy)** | Object-oriented Python framework for radical-pair spin dynamics: Hamiltonians, relaxation, kinetics, MARY curves. pip install radicalpy |
| **[MolSpin](https://molspin.eu)** | General spin-dynamics package from the Solov'yov group, for large radical-pair systems. Nielsen & Solov'yov, J. Chem. Phys. 151, 194105 (2019). |
| **[EasySpin](https://easyspin.org)** | MATLAB toolbox for simulating EPR spectra; the field standard. Stoll & Schweiger, J. Magn. Reson. 178, 42–55 (2006). |
| **[QuTiP](https://qutip.org)** | Python toolbox for open quantum systems: master equations, trajectories, pulse control. Johansson, Nation & Nori, Comput. Phys. Commun. 184, 1234 (2013). |
| **[ORCA](https://orcaforum.kofo.mpg.de)** | Quantum-chemistry package widely used for hyperfine and g-tensors of flavin and tryptophan radicals. |

## Community

| | |
|---|---|
| **[Quantum Biology Institute](https://www.quantumbiology.org/)** | Research and community organisation co-founded by C. D. Aiello. |
| **Leverhulme Quantum Biology Doctoral Training Centre** | University of Surrey doctoral centre behind the Kim et al. (2021) review. |
| **[Spin Chemistry Community](https://github.com/Spin-Chemistry-Labs/radicalpy)** | Discord community run by the RadicalPy developers (invite on their page). |
