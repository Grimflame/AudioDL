import { useState } from "react";
import { usePromptStore } from "../store";

export default function PromptBar(){
  const { seed, setSeed, prompt, negative_prompt, generatePrompt } = usePromptStore();
  const [busy,setBusy]=useState(false);

  const copy=async(text)=>{ if(!text) return; await navigator.clipboard.writeText(text); };

  const onGenerate=async()=>{
    setBusy(true);
    try{
      const res=await generatePrompt();
      await copy(res.prompt);
    } finally { setBusy(false); }
  };

  return (
    <div className="promptbar">
      <div className="controls">
        <input className="seed" placeholder="Seed (optionnel)" value={seed} onChange={e=>setSeed(e.target.value)} />
        <button className="generate" onClick={onGenerate} disabled={busy}>{busy?"Génération…":"Générer & Copier"}</button>
        <button className="copy" onClick={()=>copy(negative_prompt)} disabled={!negative_prompt}>Copier Negative</button>
      </div>
      <textarea className="output" value={prompt} readOnly placeholder="Prompt positif…" />
      <textarea className="output" value={negative_prompt} readOnly placeholder="Negative prompt…" />
    </div>
  );
}
