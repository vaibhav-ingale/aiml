import json

import requests

url = "http://localhost:8008/v1/chat/completions"
headers = {
    "Authorization": "Bearer llmgw-W-OZiZlYmVFkIaweZmr0C852r1lrtd89",
    "Content-Type": "application/json",
}
payload = {
    "model": "openai/gpt-oss-20b",
    "stream": True,
    "messages": [{"role": "user", "content": "Count to 1000."}],
}

try:
    with requests.post(url, headers=headers, data=json.dumps(payload), stream=True, timeout=60) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data: "):
                line = line[6:]
            if line == "[DONE]":
                break
            print(line)
except requests.exceptions.ChunkedEncodingError as exc:
    print(f"Stream closed unexpectedly: {exc}")
except requests.exceptions.RequestException as exc:
    print(f"Request failed: {exc}")
