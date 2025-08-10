import time, requests
from typing import List, Dict
from config import DANBOORU_BASE, USER_AGENT

def _get(path: str, params: dict, retries=3, backoff=0.6):
    last = None
    for i in range(retries):
        try:
            r = requests.get(f"{DANBOORU_BASE}{path}", params=params, timeout=30, headers={"User-Agent": USER_AGENT})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            time.sleep(backoff * (i+1))
    raise last

def fetch_tags(category=0, limit=100, page=1) -> List[Dict]:
    data = _get("/tags.json", {
        "search[category]": category,
        "search[order]": "count",
        "search[post_count_gt]": 0,
        "limit": limit,
        "page": page
    })
    return [{"name": t["name"], "post_count": t.get("post_count", 0), "category": t.get("category", 0)} for t in data]

def fetch_tag_aliases(limit=1000, page=1) -> List[Dict]:
    data = _get("/tag_aliases.json", {"limit": limit, "page": page})
    return [{"antecedent_name": a["antecedent_name"], "consequent_name": a["consequent_name"]} for a in data]

def fetch_tag_implications(limit=1000, page=1) -> List[Dict]:
    data = _get("/tag_implications.json", {"limit": limit, "page": page})
    return [{"antecedent_name": i["antecedent_name"], "consequent_name": i["consequent_name"]} for i in data]
