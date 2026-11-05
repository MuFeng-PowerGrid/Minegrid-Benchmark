# Model references and supplementary instruction data

This collection is separate from the 1429 image-paired records in the [multimodal benchmark](../../JSON%20Index/README.md).

## Typical apparatus model references

[Apparatus](Apparatus/index.html) contains 16 HTML pages: one directory, one [model-conventions page](Apparatus/model_conventions.html), and 14 device-family pages covering 46 configurations. Each family page describes model states, parameters, inputs/outputs, equations, nonlinear limits and assumptions. These HTML files are reference material for implementing power-system models; this directory does not include a runnable simulation package or apparatus instruction JSON files.

## Supplementary Alpaca-style text collection

| Directory | JSON files | Instruction records |
|---|---:|---:|
| Network | 32000 | 335517 |
| General Knowledge | 1 | 39 |
| Total | 32001 | 335556 |

General Knowledge retains one example file, `Power_System_Stability_And_Control_by_Prabha_Kundur.json`.

Each JSON file is an array. Each element has `instruction`, `input` and `output` fields. Load an entire file with a JSON parser; do not interpret each physical line as an independent JSONL record. These records do not use the benchmark's `id`, `image`, `conversations` or five-language `annotations` contract.

This directory is not referenced by the six multimodal indexes and is not loaded by the multimodal evaluation loader. Its record totals are not additional device-control or network-topology image samples, and the directory names do not define benchmark difficulty groups or train/test splits.

The counts describe the files shipped here. They do not establish image correspondence, semantic correctness, source permissions or independence from evaluation data. The legacy [transfer helper](../../Scripts/Data%20Transfer/network_Transfer.py) uses a different sectioned JSON input and random subsampling; it is not a direct round-trip converter for this collection. See the [scripts guide](../../Scripts/README.md) for its requirements and limits.
