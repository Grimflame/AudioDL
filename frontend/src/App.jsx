import { useMemo } from "react";
import "./app.css";
import TagBucket from "./components/TagBucket";
import PromptBar from "./components/PromptBar";
import NegativePanel from "./components/NegativePanel";
import { usePromptStore } from "./store";

export default function App(){
  const { buckets, selected, setWeight, weights } = usePromptStore();

  const context = useMemo(()=>{
    const ctx=[];
    for(const b of buckets){
      for(const t of Array.from(selected[b]||[])){ ctx.push(`${b}:${t}`); }
    }
    return ctx;
  },[buckets,selected]);

  return (
    <div className="app">
      <header className="header">
        <h1>Stable Diffusion Prompt Creator</h1>
        <p className="muted">Génère un prompt structuré, tri intelligent via Danbooru.</p>
      </header>

      <main className="grid">
        <TagBucket bucket="subject" title="Sujet principal" context={context}/>
        <TagBucket bucket="subject_detail" title="Détails du sujet" context={context}/>
        <TagBucket bucket="pose_frame" title="Position & cadrage" context={context}/>
        <TagBucket bucket="mood_light_style" title="Ambiance & style" context={context}/>
        <TagBucket bucket="environment" title="Environnement" context={context}/>
        <TagBucket bucket="fx_action" title="Effets & actions" context={context}/>
      </main>

      <section className="panel">
        <h3>Poids (facultatifs)</h3>
        <div className="weights">
          {buckets.flatMap(b=>Array.from(selected[b]||[]).map(tag=>(
            <div key={`${b}:${tag}`} className="weight-item small">
              <span className="pill">{tag}</span>
              <div className="stepper">
                <button onClick={()=>setWeight(tag, Math.max(0.8,(weights[tag]||1.0)-0.05))}>−</button>
                <input type="number" step="0.05" min="0.8" max="1.2"
                  value={(weights[tag]??1.0).toFixed(2)}
                  onChange={e=>setWeight(tag, parseFloat(e.target.value)||1.0)} />
                <button onClick={()=>setWeight(tag, Math.min(1.2,(weights[tag]||1.0)+0.05))}>+</button>
              </div>
            </div>
          )))}
        </div>
      </section>

      <NegativePanel />
      <PromptBar />
    </div>
  );
}
