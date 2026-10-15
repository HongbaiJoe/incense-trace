import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {reconstruct} from '../tmp/research-engine.mjs';
const fixtures=JSON.parse(fs.readFileSync(new URL('../app/data/model-fixtures.json',import.meta.url)));
test('browser inference matches eight Python predictions to 1e-10',()=>{
  for(const f of fixtures){const actual=reconstruct(f.observed);assert.equal(actual.total,f.expected.selected_count);
    assert.deepEqual(Object.keys(actual.composition).sort(),Object.keys(f.expected.composition).sort());
    for(const [k,v] of Object.entries(actual.composition))assert.ok(Math.abs(v-f.expected.composition[k])<1e-10, k);
    assert.ok(Math.abs(Object.values(actual.composition).reduce((a,b)=>a+b,0)-1)<1e-12);
  }
});
test('validates inputs and fixed constraints',()=>{
  assert.throws(()=>reconstruct({unknown:1}));assert.throws(()=>reconstruct({}));
  const obs=fixtures[0].observed;const r=reconstruct(obs,6,.4);
  assert.equal(r.total,6);assert.ok(Math.abs(Object.keys(obs).reduce((s,k)=>s+r.composition[k],0)-.4)<1e-12);
  assert.throws(()=>reconstruct(obs,1));assert.throws(()=>reconstruct(obs,6,1));
});
