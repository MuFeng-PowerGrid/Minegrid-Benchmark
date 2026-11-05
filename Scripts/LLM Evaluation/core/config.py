"""Explicit configuration contract"""
import os
import re
from pathlib import Path
import yaml


def read_yaml(path):
    class UniqueLoader(yaml.SafeLoader):
        pass
    def mapping(loader, node):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node)
            if key in result:
                raise ValueError('Duplicate YAML key: ' + str(key))
            result[key] = loader.construct_object(value_node)
        return result
    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    obj = yaml.load(Path(path).read_text('utf-8-sig'), Loader=UniqueLoader)
    if not isinstance(obj, dict):
        raise ValueError('Configuration must be a mapping')
    return obj


def runtime(path, root_override=None):
    cfg = read_yaml(path)
    expected = {'dataset_root', 'tasks', 'difficulties', 'language', 'max_samples_per_group', 'timeout_seconds', 'retries', 'retry_wait_seconds'}
    if set(cfg) != expected:
        raise ValueError('Runtime config fields differ: ' + str(set(cfg) ^ expected))
    for key, choices in [('tasks', {'device_control', 'network_topology'}), ('difficulties', {'easy', 'medium', 'hard'})]:
        values = cfg[key]
        if not isinstance(values, list) or not values or len(set(values)) != len(values) or not set(values) <= choices:
            raise ValueError('Invalid ' + key)
    if cfg['language'] not in ('original', 'en', 'es', 'ar', 'fr', 'ru'):
        raise ValueError('Invalid language')
    for key in ('max_samples_per_group', 'retries'):
        if type(cfg[key]) is not int or cfg[key] < 0:
            raise ValueError(key + ' must be a nonnegative integer')
    import math
    for key in ('timeout_seconds', 'retry_wait_seconds'):
        v = cfg[key]
        if type(v) not in (int, float) or not math.isfinite(v) or v < 0 or (key == 'timeout_seconds' and v == 0):
            raise ValueError('Invalid ' + key)
    root = Path(root_override).resolve() if root_override else (Path(path).resolve().parent / cfg['dataset_root']).resolve()
    cfg['dataset_root'] = str(root)
    return cfg


def models(path):
    cfg = read_yaml(path)
    if set(cfg) != {'models'} or not isinstance(cfg['models'], list) or not cfg['models']:
        raise ValueError('Expected nonempty models list')
    def expand(value):
        def env(match):
            result = os.environ.get(match[1], '')
            if not result:
                raise ValueError('Missing environment variable: ' + match[1])
            return result
        return re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}', env, value)
    names = set()
    for m in cfg['models']:
        if not isinstance(m, dict) or set(m) != {'name', 'base_url', 'model', 'api_key_env', 'request_options'}:
            raise ValueError('Model fields differ')
        for key in ('name', 'base_url', 'model', 'api_key_env'):
            if not isinstance(m[key], str) or not m[key].strip():
                raise ValueError('Empty model field: ' + key)
            m[key] = expand(m[key]) if key != 'api_key_env' else m[key]
        if m['name'] in names:
            raise ValueError('Duplicate model name')
        names.add(m['name'])
        from urllib.parse import urlsplit
        url = urlsplit(m['base_url'])
        if url.scheme not in ('http', 'https') or not url.netloc or url.username or url.password or url.query or url.fragment:
            raise ValueError('Invalid base_url (credentials/query are not allowed)')
        opts = m['request_options']
        if not isinstance(opts, dict) or set(opts) & {'model', 'messages', 'stream', 'api_key', 'authorization'}:
            raise ValueError('Invalid/reserved request_options')
        if 'max_tokens' in opts and 'max_completion_tokens' in opts:
            raise ValueError('Choose one token limit parameter')
        import json
        json.dumps(opts, allow_nan=False)
    return cfg['models']
