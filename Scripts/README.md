# Scripts guide

These utilities have different input contracts. Only the evaluation loader reads the released image-paired JSONL benchmark directly.

| Location | Purpose and input | Runtime status |
|---|---|---|
| [LLM Evaluation](LLM%20Evaluation/README.md) | Validate and load the 1,429 image-paired benchmark records, run inference and score Tasks 1/2; score external Task 3 editing cases. | Offline checks and scoring require Python and PyYAML. Inference uses an explicitly configured OpenAI-compatible vision endpoint; see the evaluation guide. |
| [Data Generator/GridInitialization.py](Data%20Generator/GridInitialization.py) | Synthetic network generation and power-flow/Excel workflows. | Requires external `PowerflowAgent.ACDCPowerFlow`, `PowerflowAgent.Visualization` and `GridCreate.GridGenerator`, which are not included here, plus the imported scientific Python packages. It is not a standalone reconstruction of the released benchmark. |
| [Data Transfer/network_Transfer.py](Data%20Transfer/network_Transfer.py) | Convert a sectioned JSON object into Alpaca-style instruction/input/output arrays. | Legacy helper. Call `generate_json(source_file, n)` from a configured Python environment; its direct script entry has a placeholder source and omits the required `n` argument. |

The transfer helper accepts one JSON object containing section arrays, not benchmark JSONL or the outer `conversations` record. It randomly retains each item with probability one third and writes under `Database/jsondata/json<n>/` relative to the working directory. Existing output filenames may be overwritten. Its console message names a different legacy destination; the actual path is the one above. It is not a lossless conversion or a benchmark annotation updater.

The [supplementary Alpaca collection](../Multimodal/Alpaca%20Data/README.md) and the [multimodal benchmark](../README.md) are separate data products. The bundled generation/transfer helpers do not establish complete provenance or exact reproducibility of either collection.
