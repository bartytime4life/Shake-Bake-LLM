// File-launch behavior in an isolated JavaScript VM, not browser acceptance.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {test}=require('node:test');
const source=fs.readFileSync(process.argv[2]||path.join(__dirname,'../src/shake_bake/web/app.js'),'utf8');

function harness({preview=null,initialize=true}={}){
  const elements={},calls={fetch:0,read:0,write:0,interval:0,timeout:0};
  const el=id=>elements[id]||=(
    {hidden:id==='file-launch',textContent:'',events:{},classList:{toggle(){}},
      setAttribute(){},addEventListener(name,fn){this.events[name]=fn;}}
  );
  const context={window:{location:{protocol:'file:'},__SB_RECORDED_PREVIEW__:preview},
    document:{getElementById:el,querySelectorAll:()=>[]},
    localStorage:{getItem(){calls.read++;return null;},setItem(){calls.write++;}},
    fetch(){calls.fetch++;throw new Error('Unexpected network request');},
    setInterval(){calls.interval++;},clearInterval(){},setTimeout(){calls.timeout++;},clearTimeout(){}};
  vm.createContext(context);
  vm.runInContext(initialize?source:source.replace(';initialize();',';'),context);
  return {el,calls,context};
}

test('opening the page file shows launch guidance without requests, storage or polling',async()=>{
  const h=harness();await vm.runInContext('initialize()',h.context);
  assert.equal(h.el('file-launch').hidden,false);
  assert.equal(h.el('workbench-shell').hidden,true);
  assert.equal(h.el('skip-workspace').hidden,true);
  assert.equal(h.el('prepare').disabled,true);
  assert.doesNotMatch(h.el('connection-status').textContent,/Connecting/);
  h.el('request').events.input();
  assert.deepEqual(h.calls,{fetch:0,read:0,write:0,interval:0,timeout:0});
});

test('file-page API calls cannot start tasks or save preferences',async()=>{
  const h=harness();
  for(const endpoint of ['/api/state','/api/start','/api/preferences']){
    await assert.rejects(vm.runInContext(`api(${JSON.stringify(endpoint)}, {})`,h.context),/running local workbench/);
  }
  assert.deepEqual(h.calls,{fetch:0,read:0,write:0,interval:0,timeout:0});
});

test('an embedded recorded preview still reads its synthetic state on a file origin',async()=>{
  const preview={state:{version:'test',projects:[{id:'starter-demo'}],recent:[],local_ai_enabled:false,policy:{enabled:false}}};
  const h=harness({preview,initialize:false});
  const state=await vm.runInContext('api("/api/state")',h.context);
  assert.equal(state.projects[0],'starter-demo');assert.equal(state.local_ai_paused,true);
  await vm.runInContext('api("/api/preferences", {})',h.context);
  assert.equal(h.calls.fetch,0);assert.equal(h.calls.write,0);assert.equal(h.calls.interval,0);
});
