from collections import defaultdict

BUCKET_CAPS = {
    "subject": 1,
    "subject_detail": 6,
    "pose_frame": 2,
    "mood_light_style": 3,
    "environment": 2,
    "fx_action": 2
}

MUTUAL_EXCLUDE = defaultdict(list)
MUTUAL_EXCLUDE["mood_light_style"].extend([("night","day"), ("sunset","midday")])
MUTUAL_EXCLUDE["environment"].extend([("indoor","outdoor")])
MUTUAL_EXCLUDE["subject_detail"].extend([("short_hair","long_hair"), ("blue_eyes","red_eyes")])

def apply_caps_and_rules(bucket: str, tags: list[str]) -> list[str]:
    # dédup en conservant l'ordre
    seen, ordered = set(), []
    for t in tags:
        if t not in seen:
            ordered.append(t); seen.add(t)
    # cap
    cap = BUCKET_CAPS.get(bucket, len(ordered))
    ordered = ordered[:cap]
    # conflits
    pairs = MUTUAL_EXCLUDE.get(bucket, [])
    to_drop = set()
    s = set(ordered)
    for a,b in pairs:
        if a in s and b in s:
            # on garde le premier apparu dans 'ordered'
            ai = ordered.index(a)
            bi = ordered.index(b)
            to_drop.add(b if ai < bi else a)
    return [t for t in ordered if t not in to_drop]