import json
from typing import List, Dict

with open("quality_filters.json","r",encoding="utf-8") as f:
    QF = json.load(f)
with open("context_rules.json","r",encoding="utf-8") as f:
    CONTEXT = json.load(f)

def smart_sort(tags: List[Dict], context: list[str] | None = None) -> List[Dict]:
    banned = set(QF.get("banned", []))
    wl = set(QF.get("whitelist", []))
    ctx = set(context or [])
    filtered = []
    for t in tags:
        n = t["name"]
        if n in banned: 
            continue
        if wl and n not in wl and len(wl) > 0:
            # si une whitelist est fournie et non vide, on peut filtrer ici, sinon on ignore
            pass
        filtered.append(dict(t))
    # Boost contextuel simple
    boosts: dict[str,int] = {}
    for c in ctx:
        key = c
        # c peut être "bucket:tag" déjà formé par le front, sinon on booste juste par le tag
        if key in CONTEXT:
            for candidate in CONTEXT[key]:
                boosts[candidate] = boosts.get(candidate, 0) + 3
        # Boost direct par tag si présent
        boosts[c] = boosts.get(c, 0) + 1
    for t in filtered:
        t["post_count"] = int(t.get("post_count",0)) + boosts.get(t["name"], 0)
    filtered.sort(key=lambda x: x["post_count"], reverse=True)
    return filtered