// Local-only integration check; never inject authentication headers in production.
import assert from 'node:assert/strict';
const base='http://localhost:3000';
const body={title:'LOCAL TEST '+Date.now(),source:'test fixture',notes:'private QA',observed:{sandalwood_white:2,agarwood:1},published:false};
async function post(owner,origin=base){return fetch(base+'/api/restorations',{method:'POST',headers:{'content-type':'application/json',origin,...(owner?{'oai-authenticated-user-id':owner}:{})},body:JSON.stringify(body)});}
assert.equal((await post()).status,401);
assert.equal((await post('local-qa-A','https://wrong.example')).status,403);
const saved=await post('local-qa-A');assert.equal(saved.status,201);const {id}=await saved.json();
const list=async owner=>(await(await fetch(base+'/api/restorations',{headers:owner?{'oai-authenticated-user-id':owner}:{}})).json()).records;
assert.ok((await list('local-qa-A')).some(e=>e.id===id));
assert.ok(!(await list('local-qa-B')).some(e=>e.id===id));
assert.ok(!(await list()).some(e=>e.id===id));
assert.deepEqual(await(await fetch(base+'/api/entries')).json(),[]);
console.log('PASS: durable local save/read, private owner isolation, anonymous rejection, origin rejection, legacy privacy.');
