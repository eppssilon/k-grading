import os
import time
import requests

BASE = "https://api.myanimelist.net/v2"
CLIENT_ID = os.environ.get("MAL_CLIENT_ID")
if not CLIENT_ID:
    raise RuntimeError("MAL_CLIENT_ID is not set. Use setx and open a new terminal after.")

HEADERS = {"X-MAL-CLIENT-ID": CLIENT_ID}
MIN_INTERVAL = 1.0
_last_call = 0.0

def get_json(path, params=None, max_tries=5):
    global _last_call
    for attempt in range(max_tries):
        wait = MIN_INTERVAL - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()

        resp = requests.get(BASE + path, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429, 500, 502, 503, 504):
            backoff = 2 ** attempt
            print(f"{resp.status_code} on {path}, retrying in {backoff}s")
            time.sleep(backoff)
            continue
        print("Error body:", resp.text)
        resp.raise_for_status()
    raise RuntimeError(f"Gave up on {path} after {max_tries} tries")
