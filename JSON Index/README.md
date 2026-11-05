# Annotation directory

## Multimodal benchmark

The benchmark has 1429 records in 89 JSONL batches, each paired with one image under `Multimodal/`.

| Task | Easy | Medium | Hard | Total | Batches |
|---|---:|---:|---:|---:|---:|
| Device control | 76 | 593 | 366 | 1035 | 64 |
| Network topology | 38 | 222 | 134 | 394 | 25 |
| Total | 114 | 815 | 500 | 1429 | 89 |

## Benchmark indexes

### Device control

| Difficulty | Batches | Samples | ID range | Index |
|---|---:|---:|---|---|
| easy | 4 | 76 | dev_easy_0001–dev_easy_0076 | [easy-index.json](easy-index.json) |
| medium | 37 | 593 | dev_medium_0001–dev_medium_0593 | [medium_index.json](medium_index.json) |
| hard | 23 | 366 | dev_hard_0001–dev_hard_0366 | [hard_index.json](hard_index.json) |
| Total | 64 | 1035 | | |

JSONL batches are in `JSON Index/device_control_<difficulty>_v<batch>/`; images are in `Multimodal/apparatus_<difficulty>/`. The 1035 indexed records are the benchmark samples; historical excluded images are not additional samples.

### Network topology

| Difficulty | Batches | Samples | Index |
|---|---:|---:|---|
| easy | 2 | 38 | [network_easy_index.json](network_easy_index.json) |
| medium | 14 | 222 | [network_medium_index.json](network_medium_index.json) |
| hard | 9 | 134 | [network_hard_index.json](network_hard_index.json) |
| Total | 25 | 394 | |

JSONL batches are in `JSON Index/network_topology_<difficulty>_v<batch>/`; images are in `Multimodal/network_<difficulty>/`. The labels contain 13,700 bus rows and 14,097 branch rows, including parallel circuits.

## Shared record format and paths

Each batch directory contains its JSONL file and a README describing the batch count and ID range. Index paths and record image paths resolve from the dataset root. The easy control index is named `easy-index.json`; the other five indexes use underscores. Use the explicit `jsonl` and image paths, not legacy image ordinals or reconstructed filenames. Index `start_image` and `end_image` are explicit paths; `start_image_no` and `end_image_no` are historical selection ordinals. Index `generated_at` values are original index creation times.

Each JSONL line has `id`, `image`, `conversations` and `annotations`. Parse the assistant's conversation value as JSON to obtain the answer. The top-level `annotations` object contains input prompts in `en`, `es`, `ar`, `fr` and `ru`; it does not contain five translated answers. See the [project overview](../README.md) and the [evaluation guide](../Scripts/LLM%20Evaluation/README.md) for loader behavior and scoring limitations.

## Device-control answers

Each translated prompt starts with `<image>` followed by a real newline after JSON decoding. JSONL records themselves occupy one physical line. The original human prompt is Chinese. The translations in `annotations` are input prompts, not translated answer objects.

Control answers contain `task`, `difficulty`, `control_units`, `inputs`, `states`, `outputs`, `differential_equations`, `algebraic_equations`, and `notes`. English notes define variables, parameters and helper functions, including necessary model conventions and domains. State entries may represent vectors, indexed memories or alternative models; array length alone is not scalar model order.

Keep `JSON Index`, `Multimodal`, and `Scripts` together when moving the package. Offline checks and scoring require Python and PyYAML; API inference uses an explicitly configured OpenAI-compatible vision endpoint described in the evaluation guide. Difficulty groups are not train/validation/test splits; shared source papers and system families need grouping for independent evaluation. A complete per-image source/permission manifest is not included in this package. Record the dataset version or file hashes used in an evaluation.

## Network answer format

The assistant value is a JSON string whose parsed object contains only `Bus` and `Network` arrays. Preserve table order.

`Bus` retains these 21 fields:

```text
Bus, Type, Base (kV), B (pu), G (pu), V, Theta,
PG, QG, PL, QL, Qmin, Qmax, Pmin, Pmax,
Vmin, Vmax, Area No., ACorDCorIC, Apparatus, Number
```

`Network` retains these five fields:

```text
FromBus, ToBus, R (pu), X (pu), Turn
```

- Integer fields: `Bus`, `Type`, `Area No.`, `Apparatus`, `Number`, `FromBus`, `ToBus`. `ACorDCorIC` is a string; all other fields above are floating-point numbers.
- Bus IDs are sample-local; each endpoint references a bus in the same sample. `Type` is 1 = PQ, 2 = PV, 3 = reference/slack.
- `Base (kV)` is voltage base; `B (pu)` and `G (pu)` are shunts. `V`, `Vmin`, `Vmax` are per-unit voltages; `Theta` is in degrees under the transfer-script convention.
- `PG/QG` and `PL/QL` are per-unit generation/load; `Qmin/Qmax` reactive limits. **`Pmin/Pmax` multiply `PG`**. For negative PG, handle the ordering of resulting numerical bounds explicitly.
- `Area No.`, `ACorDCorIC`, `Apparatus`, `Number` are area/domain/device-link fields. Zero links do not establish absence of physical devices.
- `R (pu)`, `X (pu)` are branch impedances and `Turn` the stored transformer/tap ratio. A universal power base or tap orientation is not established.
- Keep every parallel branch row. Endpoint order alone does not establish power-flow direction.

### Interpretation limits

The two-table representation is a simplified network equivalent. It does not encode all switching, protection, phase details or converter ports. Some numerical entries are estimated assignments permitted by the prompts, without per-value provenance flags; they are not fully reconstructed power-flow ground truth. A universal 100 MVA base is not established.

### Offline checks

From the dataset root with Python 3.10 or newer:

```text
python -B "Scripts/LLM Evaluation/evaluate.py" check
python -B -m unittest discover -s "Scripts/LLM Evaluation/tests" -v
```

The evaluator uses Python and PyYAML to validate both tasks: paths, answer schemas, numbers, bus references, counts and index coverage. `--root` selects another complete package. These structural checks do not establish electrical correctness or image permissions.

The `minegrid-paper-v1` scorer preserves parallel-branch multiplicity. Network scores compare bus/edge recovery, bus types and matched-branch R/X/Turn; other stored bus parameters are schema-checked but not scored. Task 3 uses a separate external-case entry point and the `minegrid-edit-minimal-v1` metric with structural validity only; its cases are not included in these indexes. A perfect score measures agreement under the documented structural and lexical metrics, not full electrical correctness. See the [evaluation guide](../Scripts/LLM%20Evaluation/README.md) for runtime configuration.

## Model references and supplementary text data

[Alpaca Data](../Multimodal/Alpaca%20Data/README.md) now contains two distinct kinds of material:

- **Apparatus model references:** 16 HTML pages covering 14 device families and 46 configurations, including a directory and model conventions. These are model descriptions, not instruction JSON records or a bundled simulator.
- **Supplementary text instructions:** 335556 instruction records in 32001 JSON files: Network has 32000 files / 335517 records; General Knowledge retains one example file / 39 records. Each file is a JSON array with a different schema from the image-paired benchmark JSONL.

Both are excluded from the 1429-record multimodal totals, the six batch indexes and the multimodal evaluator.
