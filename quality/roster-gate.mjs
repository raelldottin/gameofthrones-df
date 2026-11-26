// Pure deterministic domain validation; no I/O or dependencies.
function validate(b,r){
 const e=[],ck=(ok,id)=>{if(!ok)e.push(id)},int=(v,min,max=Number.MAX_SAFE_INTEGER)=>Number.isSafeInteger(v)&&v>=min&&v<=max,eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b),seteq=(a,b)=>a.length===b.length&&new Set(a).size===a.length&&a.every(x=>b.includes(x));
 const p=b.p.updates,s=b.s.dragons,m=b.m.marches,pm=new Map(p.map(x=>[x.name,x])),sm=new Map(s.map(x=>[x.name,x]));
 ck(p.length===r.count&&pm.size===p.length,"roster.identity");
 ck(s.length===r.count&&sm.size===s.length&&seteq([...pm.keys()],[...sm.keys()]),"season.identity");
 ck(seteq([...pm.keys()],Object.keys(r.affinity)),"roster.census");
 ck([b.p,b.s,b.m].every(x=>x.observed_date===r.date),"snapshot.date");
 for(const x of [b.p,b.s])ck(x.source_screenshots.length===r.screens&&new Set(x.source_screenshots).size===r.screens,"source.census");
 const allowed=new Set(["name","owned","stars","relics_toward_next_star","habits","class","command","temperament","verified_on","source_screenshot","command_and_habit_reference","confirming_screenshots","command_verification"]);
 for(const x of p){
  ck(Object.keys(x).every(k=>allowed.has(k)),"roster.persistent_boundary");
  ck(x.owned===true&&int(x.stars,1,10),"roster.star_range");
  const q=x.relics_toward_next_star;ck(q&&int(q.current,0)&&int(q.required,1)&&q.current<q.required,"roster.relic_range");
  ck(x.habits.length<=Math.floor(x.stars/2)&&x.habits.every(h=>int(h.level,1,5)),"roster.habit_gate");
  ck([x.source_screenshot,...(x.confirming_screenshots??[])].every(n=>b.p.source_screenshots.includes(n)),"source.profile");
 }
 for(const x of s){
  ck(int(x.level,1)&&int(x.displayed_power,0)&&int(x.displayed_troop_capacity,0),"season.stats");
  ck(int(x.energy.current,0)&&int(x.energy.maximum,1),"season.energy");
  ck(b.s.source_screenshots.includes(x.source_screenshot),"source.profile");
 }
 for(const [n,a] of Object.entries(r.anchors)){
  const x=pm.get(n);ck(x&&eq([x.stars,x.relics_toward_next_star.current,x.habits.map(h=>h.level)],a),"golden.profile");
 }
 ck(m.length===10&&seteq(m.map(x=>x.march),[1,2,3,4,5,6,7,8,9,10]),"march.count");
 const assigned=[],commanders=[];
 for(const x of m){
  const ns=[x.left,x.vanguard,x.right];assigned.push(...ns);if(x.commander_candidate)commanders.push(x.commander_candidate);
  const known=ns.every(n=>pm.has(n)&&sm.has(n));
  ck(new Set(ns).size===3&&known,"march.members");
  ck(ns.every(n=>r.affinity[n]?.includes(x.troop_type)),"march.affinity");
  ck(x.positive_affinity_verified_from_profile===true,"march.affinity_claim");
  if(known){
   ck(eq(x.stars,ns.map(n=>pm.get(n).stars)),"march.stars");
   ck(eq(x.reign_levels_observed,ns.map(n=>sm.get(n).level)),"march.levels");
   ck(x.displayed_troop_capacity_sum===ns.reduce((v,n)=>v+sm.get(n).displayed_troop_capacity,0),"march.capacity");
   ck(x.displayed_power_sum===ns.reduce((v,n)=>v+sm.get(n).displayed_power,0),"march.power");
  }
 }
 ck(assigned.length===30&&new Set(assigned).size===30,"march.unique");
 ck(seteq(b.m.bench,[...pm.keys()].filter(n=>!assigned.includes(n))),"march.bench");
 ck(new Set(commanders).size===commanders.length,"march.commander_unique");
 const a=b.m.deployment.initial_five_marches;ck(b.m.deployment.simultaneously_active_army_limit===5&&a.length<=5&&new Set(a).size===a.length&&a.every(n=>m.some(x=>x.march===n)),"march.active_limit");
 return [...new Set(e)];
}
export { validate };
