"""Explicit OpenAI-compatible Chat Completions HTTP transport. No provider guessing."""
import base64
import json
import mimetypes
import os
import time
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from .scoring import parse_json


def call(model, sample, root, cfg):
    key = os.environ.get(model['api_key_env'], '')
    if not key:
        raise ValueError('Missing API key environment variable: ' + model['api_key_env'])
    image = Path(root) / sample['image']
    mime = mimetypes.guess_type(image.name)[0] or 'application/octet-stream'
    uri = 'data:' + mime + ';base64,' + base64.b64encode(image.read_bytes()).decode('ascii')
    body = {'model': model['model'], 'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': sample['prompt']}, {'type': 'image_url', 'image_url': {'url': uri}}]}], **model['request_options']}
    request = Request(model['base_url'].rstrip('/') + '/chat/completions',
                      data=json.dumps(body, allow_nan=False).encode('utf-8'),
                      headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    start = time.perf_counter()
    result = {'raw_text': '', 'prediction': None, 'pure_json': False, 'parseable': False, 'error': None, 'attempts': 0,
              'model_id': model['model'], 'response_model_id': None, 'finish_reason': None}
    for attempt in range(cfg['retries'] + 1):
        result['attempts'] += 1
        retry = False
        try:
            with urlopen(request, timeout=cfg['timeout_seconds']) as response:
                payload = parse_json(response.read().decode('utf-8'))
            choice = payload['choices'][0]
            content = choice['message']['content']
            if not isinstance(content, str):
                raise ValueError('Expected string response content')
            result.update(raw_text=content, finish_reason=choice.get('finish_reason'), response_model_id=payload.get('model'))
            try:
                prediction = parse_json(content)
                result['parseable'] = True
                if not isinstance(prediction, dict):
                    raise ValueError('Answer is not an object')
                result.update(prediction=prediction, pure_json=True)
            except (ValueError, TypeError):
                result['error'] = 'Response is not a standalone JSON object'
            break
        except HTTPError as exc:
            result['error'] = 'HTTP ' + str(exc.code)
            retry = exc.code in (408, 429) or 500 <= exc.code < 600
            exc.close()
        except (URLError, TimeoutError, ConnectionError, HTTPException):
            result['error'] = 'Connection failure or timeout'
            retry = True
        except (ValueError, KeyError, IndexError, TypeError):
            result['error'] = 'Invalid API response structure'
        if not retry or attempt == cfg['retries']:
            break
        time.sleep(cfg['retry_wait_seconds'])
        result['error'] = None
    result['total_latency_ms'] = (time.perf_counter() - start) * 1000
    return result
