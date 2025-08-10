import { create } from "zustand";
import { apiGet, apiPost } from "./api";

const BUCKETS = ["subject","subject_detail","pose_frame","mood_light_style","environment","fx_action"];

export const usePromptStore = create((set, get)=>({
  buckets: BUCKETS,
  tagsByBucket:{},
  selected: Object.fromEntries(BUCKETS.map(b=>[b,new Set()])),
  weights:{},
  negative:new Set(),
  seed:"",
  prompt:"",
  negative_prompt:"",

  setSeed:(v)=>set({seed:v}),
  setWeight:(tag,w)=>set(s=>({weights:{...s.weights,[tag]:w}})),
  toggleNegative:(tag)=>set(s=>{const n=new Set(s.negative);n.has(tag)?n.delete(tag):n.add(tag);return{negative:n};}),

  loadBucket: async (bucket, context=[])=>{
    const { seed } = get();
    const ctx = context.join(",");
    const data = await apiGet(`/tags?bucket=${bucket}&context=${encodeURIComponent(ctx)}&seed=${encodeURIComponent(seed||"")}`);
    set(s=>({tagsByBucket:{...s.tagsByBucket,[bucket]:data.tags}}));
  },

  toggleTag:(bucket,tag)=>set(s=>{
    const next=new Set(s.selected[bucket]);
    next.has(tag)?next.delete(tag):next.add(tag);
    return {selected:{...s.selected,[bucket]:next}};
  }),

  clearBucket:(bucket)=>set(s=>({selected:{...s.selected,[bucket]:new Set()}})),

  generatePrompt: async ()=>{
    const {buckets,selected,weights,seed,negative}=get();
    const selections=Object.fromEntries(buckets.map(b=>[b,Array.from(selected[b])]));
    const body={selections,weights,negative:Array.from(negative),seed};
    const res=await apiPost("/generate",body);
    set({prompt:res.prompt,negative_prompt:res.negative_prompt});
    return res;
  }
}));
