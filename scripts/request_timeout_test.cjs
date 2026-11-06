// Virtual deadlines exercise the real API adapter, including a stalled body.
// The browser suite separately verifies actual fetch cancellation and UI recovery.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {test}=require('node:test');
const source=fs.readFileSync(process.argv[2]||path.join(__dirname,'../src/shake_bake/web/app.js'),'utf8');
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
function harness(transport){
  const timers=new Map(),requests=[];let clock=0,sequence=0;
  const context={document:{getElementById:()=>({})},window:{},localStorage:{getItem:()=>null},AbortController,
    setTimeout(fn,delay){const id=++sequence;timers.set(id,{at:clock+delay,fn});return id;},
    clearTimeout(id){timers.delete(id);},
    fetch(target,options){requests.push({target,options});return transport(options.signal);}};
  vm.createContext(context);vm.runInContext(source.slice(0,source.indexOf('function renderCatalog')),context);
  return {requests,timers,call:()=>vm.runInContext('api("/api/start",{project_id:"demo",request:"Exact request",task_kind:"code",ai_mode:"off"})',context),
    advance(ms){clock+=ms;for(const [id,timer]of timers)if(timer.at<=clock){timers.delete(id);timer.fn();}}};
}
function stalled(signal){return new Promise((resolve,reject)=>signal?.addEventListener('abort',()=>reject(new Error('aborted')),{once:true}));}
for(const phase of ['headers','body'])test(`request deadline aborts stalled ${phase} without retrying or claiming the job stopped`,async()=>{
  const bodySeen=deferred();
  const h=harness(signal=>phase==='headers'?stalled(signal):Promise.resolve({ok:true,status:202,json(){bodySeen.resolve();return stalled(signal);}}));
  const operation=h.call();let failure;operation.catch(error=>{failure=error;});
  if(phase==='body')await bodySeen.promise;
  h.advance(14999);assert.equal(h.requests[0].options.signal?.aborted,false);
  h.advance(1);
  await assert.rejects(operation,error=>error.code==='request_timeout'&&error.uncertain===true&&/timed out/.test(error.message));
  assert.equal(h.requests[0].options.signal.aborted,true);assert.equal(h.requests.length,1);assert.equal(h.timers.size,0);
  assert.doesNotMatch(failure.message,/job (stopped|cancelled)/i);
});
test('successful request clears its deadline and preserves the exact payload',async()=>{
  const h=harness(async()=>({ok:true,status:202,json:async()=>({task_id:'a'.repeat(32)})}));
  const result=await h.call();assert.equal(result.job_id,'a'.repeat(32));
  assert.deepEqual(JSON.parse(h.requests[0].options.body),{project_id:'demo',task:'Exact request',task_kind:'code'});
  assert.equal(h.timers.size,0);h.advance(20000);assert.equal(h.requests[0].options.signal.aborted,false);
});
test('unreadable acknowledgement remains uncertain and clears its deadline',async()=>{
  const h=harness(async()=>({ok:true,status:202,json:async()=>{throw new SyntaxError('partial JSON');}}));
  await assert.rejects(h.call(),error=>error.code==='unreadable_response'&&error.uncertain===true&&/HTTP 202/.test(error.message));
  assert.equal(h.timers.size,0);assert.equal(h.requests.length,1);
});
test('explicit service refusal retains its code while server timeouts remain uncertain',async()=>{
  for(const [code,uncertain]of [['project_not_permitted',false],['workbench_request_timeout',true]]){
    const h=harness(async()=>({ok:false,status:400,json:async()=>({error:code})}));
    await assert.rejects(h.call(),error=>error.code===code&&Boolean(error.uncertain)===uncertain);
    assert.equal(h.timers.size,0);assert.equal(h.requests.length,1);
  }
});
test('missing or invalid task handles trigger recovery instead of leaving an unpollable active job',async()=>{
  for(const value of [null,[],{}, {task_id:'../state'}, {task_id:123}, {task_id:['a'.repeat(32)]}]){
    const h=harness(async()=>({ok:true,status:202,json:async()=>value}));
    await assert.rejects(h.call(),error=>error.code==='unreadable_response'&&error.uncertain===true);
    assert.equal(h.timers.size,0);assert.equal(h.requests.length,1);
  }
});
