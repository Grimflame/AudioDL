import { useState, useMemo } from "react";
import { usePromptStore } from "../store";
const SUGGEST=["blurry","lowres","bad_anatomy","extra_limbs","deformed","oversaturated","jpeg_artifacts"];

export default function NegativePanel(){
  const { negative, toggleNegative } = usePromptStore();
  const [q,setQ]=useState("");
  const list=useMemo(()=>{
    const n=q.trim().toLowerCase();
    return n? SUGGEST.filter(t=>t.includes(n)) : SUGGEST;
  },[q]);
  return (
    <section className="panel">
      <h3>Négatives</h3>
      <input className="search" placeholder="Rechercher…" value={q} onChange={e=>setQ(e.target.value)} />
      <div className="negatives">
        {list.map(t=>(
          <button key={t} className={`tag ${negative.has(t)?'active':''}`} onClick={()=>toggleNegative(t)}>{t}</button>
        ))}
      </div>
    </section>
  );
}
