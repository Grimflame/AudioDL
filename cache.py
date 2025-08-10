import sqlite3, time
from typing import List, Dict, Tuple
from danbooru import fetch_tags, fetch_tag_aliases, fetch_tag_implications
from config import OFFLINE

DB_FILE = "tags_cache.db"
TTL = 24 * 3600  # 24h

def _conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS tags (
            bucket TEXT, name TEXT, post_count INTEGER, category INTEGER, fetched_at INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS tag_aliases (
            antecedent_name TEXT PRIMARY KEY, consequent_name TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS tag_implications (
            antecedent_name TEXT, consequent_name TEXT
        )""")
        c.execute("""CREATE INDEX IF NOT EXISTS idx_tags_bucket ON tags(bucket)""")

def _stale(rows):
    if not rows: return True
    ts = rows[0][-1]
    return (int(time.time()) - ts) > TTL

def _save_tags(bucket, items: List[Dict]):
    now = int(time.time())
    with _conn() as c:
        c.execute("DELETE FROM tags WHERE bucket=?", (bucket,))
        c.executemany("INSERT INTO tags(bucket,name,post_count,category,fetched_at) VALUES(?,?,?,?,?)",
                      [(bucket, t["name"], t["post_count"], t["category"], now) for t in items])

def _load_tags(bucket) -> List[Tuple]:
    with _conn() as c:
        return c.execute("SELECT name,post_count,category,fetched_at FROM tags WHERE bucket=? ORDER BY post_count DESC", (bucket,)).fetchall()

def _refresh_aliases_implications():
    # fetch all pages until empty
    with _conn() as c:
        c.execute("DELETE FROM tag_aliases")
        page = 1
        while True:
            batch = fetch_tag_aliases(page=page)
            if not batch: break
            c.executemany("INSERT OR REPLACE INTO tag_aliases(antecedent_name,consequent_name) VALUES(?,?)",
                          [(b["antecedent_name"], b["consequent_name"]) for b in batch])
            page += 1
        c.execute("DELETE FROM tag_implications")
        page = 1
        while True:
            batch = fetch_tag_implications(page=page)
            if not batch: break
            c.executemany("INSERT INTO tag_implications(antecedent_name,consequent_name) VALUES(?,?)",
                          [(b["antecedent_name"], b["consequent_name"]) for b in batch])
            page += 1

def canonicalize(name: str) -> str:
    with _conn() as c:
        row = c.execute("SELECT consequent_name FROM tag_aliases WHERE antecedent_name=?", (name,)).fetchone()
    return row[0] if row else name

def expand_implications(tags: List[str]) -> List[str]:
    out = set(tags)
    with _conn() as c:
        for t in list(out):
            rows = c.execute("SELECT consequent_name FROM tag_implications WHERE antecedent_name=?", (t,)).fetchall()
            for r in rows:
                out.add(r[0])
    return list(out)

def fetch_or_cache(bucket: str, category: int, limit=100) -> List[Dict]:
    init_db()
    rows = _load_tags(bucket)
    if not rows or _stale(rows):
        if OFFLINE and rows:
            # offline: renvoyer vieux cache si dispo
            pass
        else:
            # refresh tags
            page = 1
            acc = []
            while len(acc) < limit:
                batch = fetch_tags(category=category, limit=min(100, limit - len(acc)), page=page)
                if not batch: break
                acc.extend(batch); page += 1
            _save_tags(bucket, acc)
            _refresh_aliases_implications()
            rows = _load_tags(bucket)
    return [{"name": r[0], "post_count": r[1], "category": r[2]} for r in rows]