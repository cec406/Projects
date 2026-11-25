"""Check staged model availability and inference without a cloud provider."""
import argparse
import json
from urllib.request import ProxyHandler, Request, build_opener

BASE = 'http://127.0.0.1:11434'


def check(model):
    opener = build_opener(ProxyHandler({}))
    with opener.open(BASE + '/v1/models', timeout=10) as response:
        models = {entry['id'] for entry in json.load(response)['data']}
    if model not in models:
        raise ValueError(f'{model} is not staged; local catalog: {sorted(models)}')
    payload = {'model': model, 'messages': [{'role': 'user', 'content':
        'Write one sentence for the next shift: Bay 2 inspection complete; replacement filter pending.'}],
        'stream': False}
    request = Request(BASE + '/v1/chat/completions', json.dumps(payload).encode(),
                      {'Content-Type': 'application/json'})
    with opener.open(request, timeout=120) as response:
        text = json.load(response)['choices'][0]['message']['content']
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Local model returned no assistant text')
    return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='qwen3:4b')
    try:
        print(check(parser.parse_args().model))
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        parser.exit(1, f'Local inference check failed: {error}\n')
