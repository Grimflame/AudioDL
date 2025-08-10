const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function j(res){ if(!res.ok) throw new Error(await res.text()); return res.json(); }

export async function apiGet(path){ return j(await fetch(BASE+path)); }
export async function apiPost(path, body){
  return j(await fetch(BASE+path, { method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(body) }));
}