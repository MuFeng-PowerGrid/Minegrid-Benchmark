# MINEGRID evaluation

A minimal evaluator for the 1,429 image-paired benchmark records: validate the package, call an OpenAI-compatible vision endpoint, and score predictions. An additional offline Task 3 entry point scores externally supplied parameter-edit cases; no Task 3 cases are bundled. It produces JSON/JSONL results. Apparatus HTML references and supplementary Alpaca instructions are outside this evaluation.

## Files

- `evaluate.py`: the check/run/score and external score-edit command-line entry point.
- `core/`: configuration, strict loading, HTTP transport and scoring.
- `configs/`: runtime selection and model connection settings.
- `tests/`: offline dataset and behavioral regression tests.

## Setup and commands

Use Python 3.10 or newer. From the dataset root:

```text
python -m pip install -r "Scripts/LLM Evaluation/requirements.txt"
python -B "Scripts/LLM Evaluation/evaluate.py" check
python -B -m unittest discover -s "Scripts/LLM Evaluation/tests" -v
```

The sole third-party dependency is PyYAML. No private project module, plotting library or external model SDK is required. Tests run offline; endpoint responses are simulated in transport tests.

Edit [configs/default.yaml](configs/default.yaml) to select tasks, difficulties and prompt language (`original`, `en`, `es`, `ar`, `fr`, `ru`). `original` uses the stored Chinese prompt. Zero `max_samples_per_group` selects all records; a positive value selects the first records in index order per task/difficulty, not a random sample. The check, run and score commands validate the full package before selecting records. The score-edit command reads only its external input files and does not use the runtime configuration or dataset loader. Configuration paths resolve relative to the config file, independently of the working directory; `--root` overrides the dataset root.

For inference, configure [configs/models.yaml](configs/models.yaml). Each model has a unique run name, the actual model ID, a base URL, an API-key environment-variable name, and explicit request options. The endpoint must support image input through Chat Completions. In PowerShell, set the following in your own environment:

```powershell
$env:MINEGRID_BASE_URL = "https://your-provider.example/v1"
$env:MINEGRID_MODEL = "your-vision-model-id"
$env:MINEGRID_API_KEY = "your-api-key"
python -B "Scripts/LLM Evaluation/evaluate.py" run --output "evaluation-results/run-001"
```

These values are placeholders. The evaluator appends `/chat/completions` to the base URL. Add supported generation parameters to `request_options`, for example `temperature`, `max_tokens` or `max_completion_tokens` (choose one token-limit parameter). An empty options mapping uses endpoint defaults; record explicit values for controlled comparisons. Provider-specific thinking settings are sent only when explicitly configured. Unsupported options are reported; they are not silently removed. API runs may incur charges.

HTTP 408/429/5xx and connection failures can be retried according to the runtime configuration. Invalid model output is scored once without another generation attempt. `attempts` and `total_latency_ms` include transport retries and retry waits. Requested and returned model IDs are recorded separately. API error bodies and API keys are not written to results.