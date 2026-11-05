"""Strict index-driven loading"""
import hashlib
from pathlib import Path, PurePosixPath
from .scoring import parse_json, validate

TASKS = ('device_control', 'network_topology')
DIFFICULTIES = ('easy', 'medium', 'hard')


def local_file(root, name):
    if not isinstance(name, str) or '\\' in name or ':' in name:
        raise ValueError('Expected a root-relative POSIX path')
    path = PurePosixPath(name)
    target = (root / path).resolve()
    if path.is_absolute() or '..' in path.parts or not target.is_relative_to(root) or not target.is_file():
        raise ValueError('Missing or invalid dataset path: ' + name)
    return target


def load(root, language='original'):
    root = Path(root).resolve()
    samples, hashes, seen_ids, seen_images, indexed = [], {}, set(), set(), set()
    if language not in ('original', 'en', 'es', 'ar', 'fr', 'ru'):
        raise ValueError('Unsupported prompt language')
    def read(path):
        content = path.read_bytes()
        hashes[path.relative_to(root).as_posix()] = hashlib.sha256(content).hexdigest()
        return content.decode('utf-8-sig')
    for task in TASKS:
        prefix = 'device_control' if task == 'device_control' else 'network_topology'
        for difficulty in DIFFICULTIES:
            name = ('easy-index.json' if difficulty == 'easy' else difficulty + '_index.json') if task == 'device_control' else 'network_' + difficulty + '_index.json'
            index = parse_json(read(local_file(root, 'JSON Index/' + name)))
            expected_task = 'device_control_dae_index' if task == 'device_control' else 'network_topology_index'
            if index.get('split') != difficulty or index.get('task') != expected_task:
                raise ValueError('Index task/difficulty mismatch: ' + name)
            count = 0
            for batch in index['batches']:
                p = local_file(root, batch['jsonl'])
                expected = f"JSON Index/{batch['batch']}/{batch['batch']}.jsonl"
                if batch['jsonl'] != expected or not batch['batch'].startswith(f'{prefix}_{difficulty}_v') or p in indexed:
                    raise ValueError('Invalid or repeated indexed batch')
                indexed.add(p)
                rows = [parse_json(line) for line in read(p).splitlines() if line.strip()]
                if not rows or len(rows) != batch['sample_count'] or (rows[0]['id'], rows[-1]['id']) != (batch['start_id'], batch['end_id']) or (rows[0]['image'], rows[-1]['image']) != (batch['start_image'], batch['end_image']):
                    raise ValueError('Batch count/endpoints differ: ' + str(p))
                for row in rows:
                    sid, image = row['id'], row['image']
                    id_prefix = 'dev' if task == 'device_control' else 'net'
                    image_prefix = 'apparatus' if task == 'device_control' else 'network'
                    if not isinstance(sid, str) or not sid.startswith(f'{id_prefix}_{difficulty}_') or sid in seen_ids or image in seen_images or not image.startswith(f'Multimodal/{image_prefix}_{difficulty}/'):
                        raise ValueError('Invalid or duplicate sample ID/image')
                    seen_ids.add(sid); seen_images.add(image)
                    image_file = local_file(root, image)
                    hashes[image] = hashlib.sha256(image_file.read_bytes()).hexdigest()
                    human = [c['value'] for c in row['conversations'] if c.get('from') == 'human']
                    answers = [c['value'] for c in row['conversations'] if c.get('from') == 'gpt']
                    if len(human) != 1 or len(answers) != 1 or not all(isinstance(v, str) for v in human + answers):
                        raise ValueError(sid + ': expected one human prompt and one string answer')
                    label = parse_json(answers[0]); validate(label, task)
                    if task == 'device_control' and label['difficulty'] != difficulty:
                        raise ValueError(sid + ': label difficulty mismatch')
                    prompt = human[0] if language == 'original' else row['annotations'][language]
                    if not isinstance(prompt, str) or not prompt.startswith('<image>\n'):
                        raise ValueError(sid + ': invalid prompt')
                    samples.append(dict(id=sid, image=image, prompt=prompt, label=label, task=task, difficulty=difficulty))
                count += len(rows)
            if count != index['total_samples'] or len(index['batches']) != index['total_batches']:
                raise ValueError('Index totals differ: ' + name)
    actual = {p.resolve() for prefix in TASKS for p in (root/'JSON Index').glob(prefix + '_*/*.jsonl')}
    if indexed != actual:
        raise ValueError('Indexes do not cover the annotation files exactly')
    return samples, hashes
