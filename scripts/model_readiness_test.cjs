// Deterministic UI event/async regressions; no browser, Ollama or generation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');
const source = fs.readFileSync(process.argv[2] || path.join(__dirname, '../src/shake_bake/web/app.js'), 'utf8');
const A = {model:'fixture:local', digest:'a'.repeat(64)};
const B = {model:'fixture:other', digest:'b'.repeat(64)};
const C = {...A, digest:'c'.repeat(64)};
const deferred = () => {let resolve, reject; const promise = new Promise((a,b) => {resolve=a;reject=b;}); return {promise,resolve,reject};};
function metadata(item=A) {
  return {model:item.model, reported_digest:item.digest, runtime_version:'synthetic',
    reported_details:{quantization_level:'Q4_SYNTHETIC',parameter_size:'fixture'},
    reported_context_length:4096,reported_capabilities:['completion'],reported_thinking_can_disable:true,
    requested_configuration:{options:{num_ctx:4096,num_predict:256},deadline_seconds:10},observed_at:'2026-11-05T00:00:00Z'};
}
function harness() {
  class Element {
    constructor(value='') {this.value=value;this.dataset={};this.children=[];this.events={};this.checked=false;this.classList={toggle(){}};this._text='';}
    append(...items) {for(const item of items){item.parent=this;this.children.push(item);}if(this===elements.model&&!this.choice)this.choice=this.children[0];}
    replaceChildren(...items) {this.children=[];this.choice=null;this._text='';this.append(...items);}
    addEventListener(name,handler) {this.events[name]=handler;}
    get options() {return this.children;}
    get selectedOptions() {return this.choice?[this.choice]:[];}
    set selected(value) {if(value)this.parent.choice=this;}
    get textContent() {return this._text+this.children.map(x=>x.textContent).join(' ');}
    set textContent(value) {this.children=[];this._text=value;}
    setAttribute() {}
  }
  const elements={};
  const element=id=>elements[id] ||= new Element();
  const requests=[];
  let respond=async()=>({models:[]});
  const context={document:{getElementById:element,createElement:()=>new Element(),querySelectorAll:()=>[]},
    window:{},Option:function(label,value){const e=new Element(value);e.textContent=label;return e;},
    localStorage:{setItem(){},getItem(){return null;}},setTimeout(){},clearTimeout(){},setInterval(){},clearInterval(){},
    fetch:async(target,options)=>{requests.push({target,options});const data=await respond(target,options);return {ok:!data.error,json:async()=>data};}};
  vm.createContext(context);
  // Execute every real event handler, skipping only the unrelated polling/bootstrap entry point.
  assert.ok(source.includes(';initialize();'));
  vm.runInContext(source.replace(';initialize();',';'),context);
  element('local-ai').checked=true;element('ai-mode').value='trial';
  function choose(item,notify=true) {
    let option=elements.model.options.find(o=>o.value===item?.model&&o.dataset.digest===item?.digest);
    if(!option){option=new context.Option(item?.model||'Choose',item?.model||'');if(item)option.dataset.digest=item.digest;elements.model.append(option);}
    option.selected=true;if(notify)elements.model.events.change();
  }
  choose(A,false);vm.runInContext('state={allow_candidate_trials:true};connected=true;modelView();',context);
  return {elements,requests,choose,respond(fn){respond=fn;},fire(id){return element(id).events.click();},
    selection(){return JSON.parse(vm.runInContext('JSON.stringify(selectedModel())',context));},
    text(id){return element(id).textContent;},toggle(on){element('local-ai').checked=on;vm.runInContext('modelView()',context);}};
}
async function checked(h) {h.respond(async()=>metadata(h.selection()));await h.fire('check-model');assert.match(h.text('model-facts'),/Q4_SYNTHETIC/);}
function cleared(h) {assert.doesNotMatch(h.text('model-facts'),/Q4_SYNTHETIC|completion|Reported digest|Checking selected/);}
function inventory(items) {return {state:'connected',models:items.map(m=>({name:m.model,digest:m.digest}))};}

test('direct name/digest changes and clearing selection revoke displayed metadata and acknowledgement',async()=>{
  for(const replacement of [B,C,null]){const h=harness();await checked(h);h.elements['trial-ack'].checked=true;h.choose(replacement);cleared(h);assert.equal(h.elements['trial-ack'].checked,false);}
});
for(const [name,items] of [['unchanged',[A,B]],['changed digest',[C,B]],['disappeared',[B]],['empty',[]]]) {
  test(`refresh ${name} clears immediately and keeps the explicit pin`,async()=>{
    const h=harness();await checked(h);const wait=deferred();h.respond(()=>wait.promise);
    const refresh=h.fire('refresh-models');cleared(h);assert.equal(h.elements['check-model'].disabled,true);
    assert.match(h.text('readiness-status'),/Refreshing inventory/);
    const count=h.requests.length;await h.fire('check-model');assert.equal(h.requests.length,count);
    wait.resolve(inventory(items));await refresh;cleared(h);assert.deepEqual(h.selection(),A);
    assert.match(h.text('readiness-status'),/Inventory refreshed/);
    if(!items.includes(A))assert.match(h.text('model-identity'),/unavailable or changed/);
    if(items.includes(C)){h.choose(C);cleared(h);await checked(h);assert.match(h.text('model-facts'),new RegExp(C.digest));}
  });
}
test('failed inventory clears facts, preserves pin, marks availability unknown and permits retry',async()=>{
  const h=harness();await checked(h);h.respond(async()=>{throw new Error('synthetic offline');});
  await h.fire('refresh-models');cleared(h);assert.deepEqual(h.selection(),A);assert.match(h.text('readiness-status'),/Inventory unavailable/);
  assert.match(h.text('model-identity'),/inventory unavailable/);assert.equal(h.elements['refresh-models'].disabled,false);
  await checked(h);
});
test('refresh response respects a user selection made while inventory is pending',async()=>{
  const h=harness();const wait=deferred();h.respond(()=>wait.promise);const refresh=h.fire('refresh-models');h.choose(B);
  wait.resolve(inventory([A,B]));await refresh;assert.deepEqual(h.selection(),B);cleared(h);
});
test('HTTP-success unavailable/paused inventories are not treated as connected empty inventories',async()=>{
  for(const state of ['unavailable','paused']){
    const h=harness();await checked(h);h.respond(async()=>({state,models:[]}));await h.fire('refresh-models');
    cleared(h);assert.match(h.text('readiness-status'),/Inventory unavailable/);assert.deepEqual(h.selection(),A);
  }
});
for(const outcome of ['success','failure']) {
  for(const mutation of ['name','digest','clear','A/B/A','refresh unchanged','refresh replace','refresh disappear','refresh fail','refresh remove/return','off/on']) {
    test(`late ${outcome} cannot restore metadata after ${mutation}`,async()=>{
      const h=harness();const wait=deferred();h.respond(()=>wait.promise);const check=h.fire('check-model');
      if(mutation==='name')h.choose(B);
      else if(mutation==='digest')h.choose(C);
      else if(mutation==='clear')h.choose(null);
      else if(mutation==='A/B/A'){h.choose(B);h.choose(A);}
      else if(mutation==='off/on'){h.toggle(false);h.toggle(true);}
      else {
        h.respond(async()=>{if(mutation==='refresh fail')throw new Error('offline');return inventory(mutation==='refresh replace'?[C]:mutation.includes('disappear')||mutation.includes('remove')?[]:[A]);});
        await h.fire('refresh-models');
        if(mutation==='refresh remove/return'){h.respond(async()=>inventory([A]));await h.fire('refresh-models');}
      }
      const before=h.text('readiness-status');
      if(outcome==='success')wait.resolve(metadata());else wait.reject(new Error('obsolete failure'));
      await check;cleared(h);assert.equal(h.text('readiness-status'),before);assert.equal(h.elements['check-model'].disabled,!h.selection().model);
      h.choose(A);await checked(h);
    });
  }
}
test('pending readiness cannot publish while inventory itself is still pending',async()=>{
  const h=harness(),checkWait=deferred(),inventoryWait=deferred();
  h.respond(target=>target==='/api/model-check'?checkWait.promise:inventoryWait.promise);
  const check=h.fire('check-model'),refresh=h.fire('refresh-models');checkWait.resolve(metadata());await check;
  cleared(h);assert.equal(h.elements['check-model'].disabled,true);inventoryWait.resolve(inventory([A]));await refresh;cleared(h);
});
test('Local AI off makes no inventory or model request',async()=>{
  const h=harness();h.toggle(false);await h.fire('refresh-models');await h.fire('check-model');assert.equal(h.requests.length,0);
});
