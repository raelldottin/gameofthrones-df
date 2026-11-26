import { readFileSync } from 'node:fs';
import { validate } from './roster-gate.mjs';
const read=path=>JSON.parse(readFileSync(new URL('../'+path,import.meta.url),'utf8'));
const b={p:read('player-state/dragon-update-2026-11-26.json'),s:read('player-state/dragon-reign-snapshot-2026-11-26.json'),m:read('armies/current-ten-marches-2026-11-26.json')};
const ref=read('quality/fixtures/2026-11-26.json');
const cases=[
["duplicate dragon","roster.identity",b=>b.p.updates[1].name=b.p.updates[0].name],
["missing seasonal dragon","season.identity",b=>b.s.dragons.pop()],
["seasonal level leaked","roster.persistent_boundary",b=>b.p.updates[0].level=23],
["invalid star rank","roster.star_range",b=>b.p.updates[0].stars=11],
["negative relics","roster.relic_range",b=>b.p.updates[0].relics_toward_next_star.current=-1],
["locked habit","roster.habit_gate",b=>b.p.updates.find(x=>x.name==="Vhagar").habits.push({name:"locked",level:1})],
["habit above maximum","roster.habit_gate",b=>b.p.updates[0].habits[0].level=6],
["golden mismatch","golden.profile",b=>b.p.updates.find(x=>x.name==="Jagadrix").stars=8],
["wrong affinity","march.affinity",b=>b.m.marches[0].troop_type="Spearmen"],
["reused dragon","march.unique",b=>b.m.marches[1].left=b.m.marches[0].left],
["stale stars","march.stars",b=>b.m.marches[0].stars[0]++],
["stale reign level","march.levels",b=>b.m.marches[0].reign_levels_observed[0]++],
["wrong capacity","march.capacity",b=>b.m.marches[0].displayed_troop_capacity_sum++],
["wrong power","march.power",b=>b.m.marches[0].displayed_power_sum++],
["wrong bench","march.bench",b=>b.m.bench.pop()],
["duplicate commander","march.commander_unique",b=>b.m.marches[1].commander_candidate=b.m.marches[0].commander_candidate],
["six active armies","march.active_limit",b=>b.m.deployment.initial_five_marches.push(6)],
["duplicate screenshot","source.census",b=>b.p.source_screenshots[1]=b.p.source_screenshots[0]],
["invalid energy","season.energy",b=>b.s.dragons[0].energy.current=-1],
["wrong date","snapshot.date",b=>b.s.observed_date="2026-11-25"],
["unknown confirmation screenshot","source.profile",b=>b.p.updates.find(x=>x.name==="Vhagar").confirming_screenshots.push("missing.jpeg")]
];
function benchmark(b,r,cases,validator){
 const baseline=validator(b,r);
 const results=cases.map(([name,expected,mutate])=>{const copy=JSON.parse(JSON.stringify(b));mutate(copy);return {name,expected,detected:validator(copy,r).includes(expected)}});
 return {baseline,results,killed:results.filter(x=>x.detected).length,total:results.length};
}
const report=benchmark(b,ref,cases,validate),negative=benchmark(b,ref,cases,()=>[]);
console.log(JSON.stringify({...report,negativeControl:negative.killed},null,2));
if(report.baseline.length||report.killed!==report.total||negative.killed!==0)process.exitCode=1;
