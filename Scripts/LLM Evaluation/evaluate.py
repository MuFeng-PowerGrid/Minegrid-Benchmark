"""Check the dataset, run model inference, or score saved predictions."""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from core import client, config, data, scoring

HERE = Path(__file__).resolve().parent


def select(samples, cfg):
    counts = collections.Counter()
    selected = []
    for s in samples:
        key = (s['task'], s['difficulty'])
        if s['task'] not in cfg['tasks'] or s['difficulty'] not in cfg['difficulties']:
            continue
        if cfg['max_samples_per_group'] and counts[key] >= cfg['max_samples_per_group']:
            continue
        counts[key] += 1
        selected.append(s)
    if not selected:
        raise ValueError('No selected samples')
    return selected


def summary(rows):
    groups = collections.defaultdict(list)
    for row in rows:
        domain = row['domain'] if row['task'] == 'parameter_edit' else ''
        groups[(row['model'], row['model_id'], row['task'], row['difficulty'], domain)].append(row)
    result = []
    for key, group in sorted(groups.items()):
        count = len(group)
        parsed = sum(row.get('parseable', row.get('pure_json', row.get('prediction') is not None)) is True for row in group)
        latencies = [row['total_latency_ms'] for row in group
                     if scoring._finite(row.get('total_latency_ms')) and row['total_latency_ms'] >= 0]
        item = {'model': key[0], 'model_id': key[1], 'task': key[2], 'difficulty': key[3], 'count': count,
                'metric_version': group[0]['metrics'].get('metric_version', scoring.VERSION), 'mean_score': sum(row['metrics']['score'] for row in group) / count,
                'schema_valid_count': sum(row['metrics']['schema_valid'] for row in group),
                'parse_rate': parsed / count, 'latency_count': len(latencies),
                'mean_latency_seconds': sum(latencies) / count / 1000 if len(latencies) == count else None,
                'error_count': sum(bool(row.get('error')) for row in group)}
        if key[2] == 'parameter_edit':
            item.update(domain=key[4], validity_scope='structure_only')
        metrics = sorted(set.intersection(*(set(row['metrics']) for row in group)))
        for name in metrics:
            if name not in ('score', 'schema_valid') and all(scoring._finite(row['metrics'][name]) for row in group):
                item['mean_' + name] = sum(row['metrics'][name] for row in group) / count
        result.append(item)
    return result


def task_summary(groups):
    tasks = collections.defaultdict(dict)
    for group in groups:
        key = (group['model'], group['model_id'], group['task'])
        bucket = (group['domain'], group['difficulty']) if group['task'] == 'parameter_edit' else group['difficulty']
        if bucket in tasks[key]:
            raise ValueError('Duplicate summary group')
        tasks[key][bucket] = group
    result = []
    for key, buckets in sorted(tasks.items()):
        editing = key[2] == 'parameter_edit'
        expected = {(domain, d) for domain in data.TASKS for d in data.DIFFICULTIES} if editing else set(data.DIFFICULTIES)
        complete = set(buckets) == expected
        item = {'model': key[0], 'model_id': key[1], 'task': key[2],
                'metric_version': scoring.EDIT_VERSION if editing else scoring.VERSION,
                'difficulties': sorted({row['difficulty'] for row in buckets.values()}), 'complete_difficulties': complete,
                'macro_score': sum(row['mean_score'] for row in buckets.values()) / len(expected) if complete else None}
        if editing:
            item.update(buckets=[{'domain': domain, 'difficulty': d} for domain, d in sorted(buckets)],
                        validity_scope='structure_only')
        result.append(item)
    return result


def load_edit_cases(path):
    content = Path(path).read_bytes()
    samples, seen = [], set()
    for line in content.decode('utf-8-sig').splitlines():
        if not line.strip():
            continue
        row = scoring.parse_json(line)
        required = {'sample_id', 'domain', 'difficulty', 'baseline', 'reference', 'target_paths'}
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError('Edit cases require exactly: ' + ', '.join(sorted(required)))
        sid = row['sample_id']
        if not isinstance(sid, str) or not sid.strip() or sid in seen:
            raise ValueError('Empty or duplicate edit sample_id')
        if row['domain'] not in data.TASKS or row['difficulty'] not in data.DIFFICULTIES:
            raise ValueError('Invalid edit domain or difficulty')
        scoring.validate_edit_case(row['baseline'], row['reference'], row['target_paths'])
        seen.add(sid)
        samples.append({**row, 'id': sid, 'task': 'parameter_edit'})
    if not samples:
        raise ValueError('No edit cases')
    return samples, {str(Path(path).resolve()): hashlib.sha256(content).hexdigest()}


def offline_records(path, samples):
    rows = [scoring.parse_json(x) for x in Path(path).read_text('utf-8-sig').splitlines() if x.strip()]
    gold = {s['id']: s for s in samples}
    seen, identities = set(), {}
    for row in rows:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k] for k in ('model', 'model_id', 'sample_id')) or 'prediction' not in row:
            raise ValueError('Prediction rows require model, model_id, sample_id and prediction')
        key = (row['model'], row['sample_id'])
        if row['sample_id'] not in gold or key in seen:
            raise ValueError('Unknown or duplicate prediction sample')
        if row['model'] in identities and identities[row['model']] != row['model_id']:
            raise ValueError('A model name refers to multiple model IDs')
        if row.get('bus_mapping') is not None:
            sample = gold[row['sample_id']]
            if sample['task'] != 'network_topology':
                raise ValueError('bus_mapping is only valid for network predictions')
            predicted = row['prediction'] if isinstance(row['prediction'], dict) else {}
            scoring._mapping(row['bus_mapping'], scoring._buses(predicted), scoring._buses(sample['label']))
        identities[row['model']] = row['model_id']; seen.add(key)
    if not rows or any({sid for m, sid in seen if m == name} != set(gold) for name in identities):
        raise ValueError('Each model must cover every selected sample exactly once; use prediction: null for failures')
    return rows


def execute(args):
    editing = args.command == 'score-edit'
    if editing:
        cfg = {'cases': str(Path(args.cases).resolve())}
        samples, hashes = load_edit_cases(args.cases)
        selected = samples
    else:
        cfg = config.runtime(args.config, args.root)
        samples, hashes = data.load(cfg['dataset_root'], cfg['language'])
        selected = select(samples, cfg)
    version = scoring.EDIT_VERSION if editing else scoring.VERSION
    counts = collections.Counter(s['task'] + '/' + s['difficulty'] for s in samples)
    if args.command == 'check':
        return {'status': 'ok', 'total': len(samples), 'selected': len(selected), 'counts': dict(counts), 'metric_version': scoring.VERSION}
    models = config.models(args.models) if args.command == 'run' else []
    for m in models:
        if not os.environ.get(m['api_key_env']):
            raise ValueError('Missing API key environment variable: ' + m['api_key_env'])
    pending = offline_records(args.predictions, selected) if args.command in ('score', 'score-edit') else None
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError('Output directory must not already exist')
    root = None if editing else Path(cfg['dataset_root']).resolve()
    if root is not None and any(output.is_relative_to(root / name) for name in ('JSON Index', 'Multimodal')):
        raise ValueError('Output must not be inside the data directories')
    output.mkdir(parents=True)
    metadata = {'metric_version': version, 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'runtime': cfg, 'models': models, 'selected_ids': [s['id'] for s in selected],
                'dataset_sha256': hashes, 'code_sha256': {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'evaluate.py', *sorted((HERE/'core').glob('*.py'))]},
                'status': 'running'}
    if pending is not None:
        metadata['predictions_sha256'] = hashlib.sha256(Path(args.predictions).read_bytes()).hexdigest()
    def save_meta():
        (output/'meta.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False), 'utf-8')
    save_meta()
    gold = {s['id']: s for s in selected}
    def live_rows():
        for m in models:
            for s in selected:
                yield {'model': m['name'], 'sample_id': s['id'], **client.call(m, s, root, cfg)}
    scored = []
    with (output/'records.jsonl').open('w', encoding='utf-8') as stream:
        for row in pending if pending is not None else live_rows():
            s = gold[row['sample_id']]
            metrics = (scoring.score_edit(row['prediction'], s['baseline'], s['reference'], s['target_paths']) if editing
                       else scoring.score(row['prediction'], s['label'], s['task'], bus_mapping=row.get('bus_mapping')))
            result = {**row, 'task': s['task'], 'difficulty': s['difficulty'], 'metrics': metrics}
            if editing:
                result['domain'] = s['domain']
            # The reference answer is always loaded locally, never trusted from a predictions file.
            stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n'); stream.flush()
            scored.append(result)
    summaries = summary(scored)
    (output/'summary.json').write_text(json.dumps(summaries, indent=2, ensure_ascii=False), 'utf-8')
    (output/'task_summary.json').write_text(json.dumps(task_summary(summaries), indent=2, ensure_ascii=False), 'utf-8')
    metadata['status'] = 'complete'; metadata['record_count'] = len(scored); save_meta()
    return {'status': 'ok', 'output': str(output), 'records': len(scored), 'metric_version': version}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    edit = sub.add_parser('score-edit', help='Score external parameter-edit predictions; validity checks structure only')
    edit.add_argument('--cases', required=True,
                      help='JSONL: sample_id, domain (device_control/network_topology), difficulty, baseline, reference, target_paths (JSON Pointer leaves)')
    edit.add_argument('--predictions', required=True, help='JSONL: model, model_id, sample_id, prediction')
    edit.add_argument('--output', required=True, help='New output directory')
    for command in ('check', 'run', 'score'):
        p = sub.add_parser(command)
        p.add_argument('--config', type=Path, default=HERE/'configs/default.yaml')
        p.add_argument('--root', type=Path, help='Override the dataset root')
        if command != 'check':
            p.add_argument('--output', required=True, help='New output directory; existing directories are rejected')
        if command == 'run':
            p.add_argument('--models', type=Path, default=HERE/'configs/models.yaml')
        if command == 'score':
            p.add_argument('--predictions', required=True)
    try:
        print(json.dumps(execute(parser.parse_args()), ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print('Evaluation failed: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
