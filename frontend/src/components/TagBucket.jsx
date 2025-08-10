import { useEffect, useMemo, useState } from "react";
import { usePromptStore } from "../store";

export default function TagBucket({ bucket, title, context=[] }) {
  const { tagsByBucket, loadBucket, selected, toggleTag, clearBucket } = usePromptStore();
  const [q, setQ] = useState("");
  const tags = tagsByBucket[bucket] || [];
  const chosen = selected[bucket] || new Set();

  useEffect(()=>{ loadBucket(bucket, context); }, [bucket, JSON.stringify(context)]);

  const filtered = useMemo(()=>{
    const n = q.trim().toLowerCase();
    const arr = tags.slice(0, 500);
    return n ? arr.filter(t=>t.toLowerCase().includes(n)).slice(0,200) : arr.slice(0,200);
  }, [tags, q]);

  return (
    <div className="bucket">
      <div className="bucket-header">
        <h3>{title} <span className="muted">({chosen.size})</span></h3>
        <input className="search" placeholder="Rechercher…" value={q} onChange={e=>setQ(e.target.value)} />
        <button className="clear" onClick={()=>clearBucket(bucket)}>Vider</button>
      </div>
      <div className="tags">
        {filtered.map(tag=>{
          const active = chosen.has(tag);
          return (
            <button key={tag} className={`tag ${active?"active":""}`} onClick={()=>toggleTag(bucket, tag)} title={tag}>
              {tag}
            </button>
          );
        })}
        {filtered.length===0 && <div className="empty">Aucun tag</div>}
      </div>
    </div>
  );
}