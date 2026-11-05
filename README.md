<!-- This README is one language at a time. Other versions are linked below. -->

**English** · [中文](docs/readme/README.zh.md) · [Français](docs/readme/README.fr.md) · [Español](docs/readme/README.es.md) · [Русский](docs/readme/README.ru.md) · [العربية](docs/readme/README.ar.md)

<p align="center">
  <img src="docs/assets/logo_brand.png" width="760" alt="MINEGRID — Power System Made Simple">
</p>

# MINEGRID

### From power-system models to multimodal reasoning

MINEGRID brings together detailed nonlinear device descriptions, image–annotation pairs, and supplementary network instructions. Use the model library to develop a small research simulator, and use the multimodal benchmark to study how vision-language models understand control diagrams and electrical networks.

## Explore the collection

- **[Typical apparatus](Multimodal/Alpaca%20Data/Apparatus/index.html)** — 14 device families · 46 configurations · HTML model descriptions
- **[Multimodal benchmark](JSON%20Index/README.md)** — 1,429 image–annotation pairs · 2 tasks · 3 difficulty levels
- **[Supplementary instructions](Multimodal/Alpaca%20Data/README.md)** — Network instruction data and one general-knowledge example file

## Typical apparatus: modeling coverage

Each device page describes states, parameters, inputs/outputs, differential and algebraic equations, nonlinear limits, and modeling assumptions. Detailed configurations and alternative control modes are documented separately. These HTML files are model references, not a bundled executable simulator.

| Device | Modeling coverage | Configurations |
|---|---|---|
| [Detailed synchronous generator](Multimodal/Alpaca%20Data/Apparatus/sg.html) | Six-winding electromagnetic dynamics, rotor motion, governor, excitation, PSS, and configuration-dependent saturation/limits. | 3 |
| [Grid-forming VSG](Multimodal/Alpaca%20Data/Apparatus/gfm_vsg.html) | Virtual inertia and damping, power/voltage regulation, voltage/current loops, LCL filter, DC link, actuator limits and anti-windup. | 4 |
| [Grid-forming droop](Multimodal/Alpaca%20Data/Apparatus/gfm_droop.html) | Power filtering, P–f and voltage/reactive-power control, inner loops, LCL and DC-link dynamics; sequence-control variants. | 3 |
| [Grid-forming matching](Multimodal/Alpaca%20Data/Apparatus/gfm_matching.html) | DC-voltage-based synchronization, energy balance, voltage/current regulation, filter and actuator dynamics. | 3 |
| [Grid-forming dVOC](Multimodal/Alpaca%20Data/Apparatus/gfm_dvoc.html) | Oscillator amplitude/phase dynamics, power regulation, electrical dynamics, inner loops and nonlinear limits. | 3 |
| [Grid-following PQ](Multimodal/Alpaca%20Data/Apparatus/gfl_pq.html) | PLL synchronization, active/reactive-power loops, current regulation, LCL/DC link, fault ride-through and power recovery. | 4 |
| [Grid-following PU](Multimodal/Alpaca%20Data/Apparatus/gfl_pu.html) | PLL, active-power and AC-voltage regulation, current loops, electrical dynamics and fault-support variants. | 4 |
| [Grid-forming DFIG wind turbine](Multimodal/Alpaca%20Data/Apparatus/gfm_dfig.html) | Aerodynamics, two-mass drivetrain, machine fluxes, converter controls, DC link, pitch, crowbar/chopper and fault support. | 2 |
| [Grid-following DFIG wind turbine](Multimodal/Alpaca%20Data/Apparatus/gfl_dfig.html) | Wind/drivetrain and induction-machine dynamics, rotor/grid-side PLL and controls, pitch, crowbar and fault recovery. | 2 |
| [Grid-forming PMSG wind turbine](Multimodal/Alpaca%20Data/Apparatus/gfm_pmsg.html) | Permanent-magnet machine, mechanical dynamics, back-to-back converters and DC link; VSG or matching control, pitch and fault support. | 4 |
| [Grid-following PMSG wind turbine](Multimodal/Alpaca%20Data/Apparatus/gfl_pmsg.html) | Machine-side speed/current control, grid-side PLL and DC-voltage regulation, electromagnetic dynamics, pitch and fault recovery. | 2 |
| [Data center load](Multimodal/Alpaca%20Data/Apparatus/data_center.html) | AFE–UPS–VSI–PSU supply chain, equivalent computing load, measurement/actuator dynamics and backup-battery energy. | 2 |
| [Induction motor](Multimodal/Alpaca%20Data/Apparatus/induction_motor.html) | Stator/rotor fluxes, mechanical speed, load torque, voltage measurement, thermal indicator and undervoltage protection. | 2 |
| [AC/DC interlinking converter](Multimodal/Alpaca%20Data/Apparatus/ic.html) | AC/DC energy exchange, PLL, filter and DC-side dynamics; PQ, EQ, PU and EU modes with sequence-control variants. | 8 |

[Device directory](Multimodal/Alpaca%20Data/Apparatus/index.html) · [Model conventions](Multimodal/Alpaca%20Data/Apparatus/model_conventions.html)

## Multimodal benchmark

| Task | Easy | Medium | Hard | Total | JSONL batches |
|---|---|---|---|---|---|
| Device control | 76 | 593 | 366 | 1035 | 64 |
| Network topology | 38 | 222 | 134 | 394 | 25 |
| Total | 114 | 815 | 500 | 1429 | 89 |

Counts are calculated from the current release. The 1,429 samples are paired with 1,429 referenced images in 89 JSONL batches. Difficulty categories are not train/validation/test splits.

| Supplementary collection | Files | Instruction records |
|---|---|---|
| Network (JSON) | 32000 | 335517 |
| General Knowledge (JSON example) | 1 | 39 |

Supplementary instruction records are separate from the image-paired benchmark. Apparatus now contains 16 HTML pages, including the directory and model conventions; General Knowledge contains one example file.

## A visual tour

Nine representative examples per task and difficulty, arranged in compact 3 × 3 contact sheets. Device control occupies one row and network topology the next, with Easy, Medium and Hard side by side. Click a sheet to view it at full resolution; sample IDs are retained for traceability.

### Device control

| Easy | Medium | Hard |
|---|---|---|
| [![Device control · Easy](docs/assets/apparatus_easy.png)](docs/assets/apparatus_easy.png) | [![Device control · Medium](docs/assets/apparatus_medium.png)](docs/assets/apparatus_medium.png) | [![Device control · Hard](docs/assets/apparatus_hard.png)](docs/assets/apparatus_hard.png) |

### Network topology

| Easy | Medium | Hard |
|---|---|---|
| [![Network topology · Easy](docs/assets/network_easy.png)](docs/assets/network_easy.png) | [![Network topology · Medium](docs/assets/network_medium.png)](docs/assets/network_medium.png) | [![Network topology · Hard](docs/assets/network_hard.png)](docs/assets/network_hard.png) |

## Build a small power-system simulator

Use the HTML models as specifications for a compact, initial-scale power-system modeling and simulation tool: extract a common device interface; preserve units, reference frames and limits; assemble device equations with network constraints; then implement initialization, time integration and event handling. This supports prototyping and LLM-assisted model implementation, followed by independent engineering validation.

### Dynamic alignment with PSCAD and PowerFactory

When high-fidelity dynamic alignment with models in PSCAD, PowerFactory or similar software is required, use the TypicalApparatus descriptions as a structural starting point. The methods in [Guo and Shi (2024)](https://doi.org/10.1109/CIEEC60922.2024.10583352) and [Shi, Guo et al. (2026)](https://doi.org/10.1109/TSTE.2025.3621702) provide a basis for identifying explicit analytical model equations from transient data and physical constraints, using model identification and symbolic regression.

Keep units, reference frames and boundary conditions consistent with the reference model. Validate generalization on operating points and disturbances that were not used for identification, comparing the resulting transient responses with those of the reference software. Related implementation code is available in [DSIPS — Dynamic Sparse Identification of Power System](https://github.com/gdg1999/DSIPS).

## Prompt examples

### 1 · Turn a device description into a component

```text
Use the attached MINEGRID grid-forming VSG HTML model as the specification. First list every state, algebraic variable, input, output, parameter, unit and reference frame. Then design a component interface for f(x,z,u;p), g(x,z,u;p) and terminal current injection. Preserve every documented limiter and anti-windup term. Separate supplied values from missing information; do not invent parameters. Provide the implementation plan and equation-to-code mapping before writing code.
```

### 2 · Assemble an initial-scale dynamic simulator

```text
Using the attached synchronous-generator, GFM, GFL and load descriptions, design a three-bus research simulator. Define a common base, network equations, device interfaces and consistent initialization. Add a small load-change event, state/current/voltage recording, residual checks and a step-size convergence study. List every extra network parameter or assumption that is not provided by the documents. Clearly distinguish implemented functions from unverified behavior.
```

## Evaluate VLMs and investigate their mechanisms

- Capability evaluation: control-block recognition, feedback-sign reasoning, state identification and DAE derivation; bus/branch extraction, connectivity and table reconstruction for network diagrams.
- Mechanism research: controlled prompt-language, resolution, occlusion and symbol-placement experiments; error taxonomy for perception versus physical reasoning; attention/activation analysis when model internals are accessible.
- Evaluation protocol: retain held-out answers, fix the task and difficulty distribution, compare structured outputs and physical consistency, and group shared papers or system families to reduce source leakage. Exact text matching alone is insufficient for equivalent equations.

## Data layout and annotation format

```text
JSON Index/
├── device_control_*/      # JSONL
└── network_topology_*/     # JSONL
Multimodal/
├── Alpaca Data/
│   ├── Apparatus/          # HTML
│   ├── Network/            # JSON
│   └── General Knowledge/  # JSON
├── apparatus_{easy,medium,hard}/
└── network_{easy,medium,hard}/
Scripts/
docs/
├── assets/
└── readme/
```

Each benchmark JSONL record contains id, image, conversations and annotations. Image paths resolve from the repository root. Parse the assistant conversation value a second time as JSON to obtain the answer. The original human prompt is Chinese; annotations provides prompts in en, es, ar, fr and ru. The six README languages do not imply six independently translated answer sets. Supplementary JSON files are arrays of instruction/input/output records.

[Annotation guide](JSON%20Index/README.md) · [Evaluation guide](Scripts/LLM%20Evaluation/README.md)

## Citation

If this resource supports your work, please cite the related paper:

D. Guo, S. Li, X. Shi, S. Jiang, G. Konstantinou and Y. Cao, "A Large Language Model-Based Framework for Automated Dynamic Simulation of Power Systems," in *IEEE Transactions on Smart Grid*, doi: [10.1109/TSG.2026.3731592](https://doi.org/10.1109/TSG.2026.3731592).

```bibtex
@article{guo2026automated,
  author  = {Guo, D. and Li, S. and Shi, X. and Jiang, S. and Konstantinou, G. and Cao, Y.},
  title   = {A Large Language Model-Based Framework for Automated Dynamic Simulation of Power Systems},
  journal = {IEEE Transactions on Smart Grid},
  year    = {2026},
  doi     = {10.1109/TSG.2026.3731592}
}
```

Related methods for transient-data model identification and physics-constrained aggregation:

1. D. Guo and X. Shi, "Model Identification of Grid-following System for Stability Evaluation with Transient Data," *2024 IEEE 7th International Electrical and Energy Conference (CIEEC)*, Harbin, China, 2024, pp. 01–06, doi: [10.1109/CIEEC60922.2024.10583352](https://doi.org/10.1109/CIEEC60922.2024.10583352).

2. X. Shi, D. Guo *et al*., "Physical-Informed Detailed Aggregation of Wind Farm Based on Symbolic Regression: Structure, Solution and Generalizability," in *IEEE Transactions on Sustainable Energy*, vol. 17, no. 2, pp. 1511–1524, April 2026, doi: [10.1109/TSTE.2025.3621702](https://doi.org/10.1109/TSTE.2025.3621702).

```bibtex
@inproceedings{guo2024identification,
  author    = {Guo, D. and Shi, X.},
  title     = {Model Identification of Grid-following System for Stability Evaluation with Transient Data},
  booktitle = {2024 IEEE 7th International Electrical and Energy Conference (CIEEC)},
  address   = {Harbin, China},
  year      = {2024},
  pages     = {01--06},
  doi       = {10.1109/CIEEC60922.2024.10583352}
}

@article{shi2026aggregation,
  author  = {Shi, X. and Guo, D. and others},
  title   = {Physical-Informed Detailed Aggregation of Wind Farm Based on Symbolic Regression: Structure, Solution and Generalizability},
  journal = {IEEE Transactions on Sustainable Energy},
  volume  = {17},
  number  = {2},
  pages   = {1511--1524},
  month   = apr,
  year    = {2026},
  doi     = {10.1109/TSTE.2025.3621702}
}
```

## Minegrid website

**Minegrid website: under testing and maintenance…**
