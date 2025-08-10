from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from config import DISPLAY_CAP_PER_BUCKET
from cache import fetch_or_cache, canonicalize, expand_implications
from mapping import map_tag_to_bucket
from rules import apply_caps_and_rules
from smart_sort import smart_sort
import json, hashlib

app = FastAPI(title="SD Prompt App - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class GenerateReq(BaseModel):
    selections: Dict[str, List[str]] = Field(default_factory=dict)
    weights: Dict[str, float] = Field(default_factory=dict)
    negative: List[str] = Field(default_factory=list)
    seed: Optional[str] = None

class GenerateResp(BaseModel):
    prompt: str
    negative_prompt: str

def _rot(lst: List[str], seed: Optional[str]) -> List[str]:
    if not seed or not lst: return lst
    h = int(hashlib.sha256(str(seed).encode()).hexdigest()[:8], 16)
    k = h % len(lst)
    return lst[k:] + lst[:k]

@app.get("/presets")
def presets():
    with open("presets.json","r",encoding="utf-8") as f:
        return json.load(f)

@app.get("/tags")
def get_tags(
    bucket: str = Query("subject"),
    seed: Optional[str] = Query(None),
    context: Optional[str] = Query(None)
):
    category_map = {
        "subject": 0, "subject_detail": 0, "pose_frame": 0,
        "mood_light_style": 0, "environment": 0, "fx_action": 0
    }
    tags = fetch_or_cache(bucket, category_map.get(bucket,0), limit=100)
    ctx_list = [s.strip() for s in (context or "").split(",") if s and s.strip()]
    tags_sorted = smart_sort(tags, context=ctx_list)
    names = [t["name"] for t in tags_sorted][:DISPLAY_CAP_PER_BUCKET]
    # rotation légère à l’affichage pour varier la liste si seed fournie
    names = _rot(names, seed)
    return {"tags": names}

@app.post("/generate", response_model=GenerateResp)
def generate(req: GenerateReq):
    # 1) Canonicalisation
    selections = {b: [] for b in ("subject","subject_detail","pose_frame","mood_light_style","environment","fx_action")}
    for b, arr in (req.selections or {}).items():
        for t in arr:
            selections.setdefault(b, []).append(canonicalize(t))

    # 2) Implications globales puis re-bucket
    flat = []
    for arr in selections.values(): flat.extend(arr)
    flat = expand_implications(flat)
    selections = {b: [] for b in selections.keys()}
    for t in flat:
        b = map_tag_to_bucket(t, 0)
        selections[b].append(t)

    # 3) Rotation déterministe PAR BUCKET avant caps/règles
    for b in selections:
        selections[b] = _rot(selections[b], req.seed)

    # 4) Caps + règles + ordre final
    order = ["subject","subject_detail","pose_frame","mood_light_style","environment","fx_action"]
    final = []
    for b in order:
        final.extend(apply_caps_and_rules(b, selections.get(b, [])))

    # 5) Poids
    out, seen = [], set()
    for t in final:
        if t in seen: continue
        seen.add(t)
        w = req.weights.get(t, 1.0)
        out.append(f"{t}:({w})" if isinstance(w,(int,float)) and abs(w-1.0)>1e-6 else t)

    # 6) Negative
    neg_seen, neg = [], []
    for n in (req.negative or []):
        c = canonicalize(n)
        if c not in neg_seen: neg.append(c); neg_seen.add(c)

    return GenerateResp(prompt=", ".join(out), negative_prompt=", ".join(neg))