// Real Chromium DOM/events with synthetic HTTP metadata and explicit async barriers.
// Optional argument: isolated installed Python; default uses source. No real model runs.
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {waitForServer} = require('./browser_server.cjs');
const {chromium} = require('playwright');
const A={name:'fixture:a',digest:'a'.repeat(64)},B={name:'fixture:b',digest:'b'.repeat(64)},C={...A,digest:'c'.repeat(64)};
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const env={...process.env};
if(process.argv[2])delete env.PYTHONPATH;else env.PYTHONPATH=path.join(__dirname,'../src');
const server=spawn(process.argv[2]||'python3',['-u','-c',
  'from shake_bake.gui import Controller, DEMO, WorkbenchServer\nc=Controller({"starter-demo":DEMO},allow_trials=True)\ns=WorkbenchServer(("127.0.0.1",0),c)\nprint(s.server_port,flush=True)\ntry: s.serve_forever()\nexcept KeyboardInterrupt: pass\nfinally: s.server_close(); c.close()'],{env,stdio:['ignore','pipe','inherit']});
let browser;
let passed=0;
async function scenario(label,run){
  const context=await browser.newContext(),page=await context.newPage();
  const h={page,items:[A,B],unavailable:false,hold:false,fail:false,waiting:deferred(),release:deferred(),enabled:true};
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await context.route('**/api/state',async route=>{const r=await route.fetch();const value=await r.json();await route.fulfill({json:{...value,local_ai_enabled:h.enabled}});});
  await context.route('**/api/settings',async route=>{h.enabled=route.request().postDataJSON().enabled;await route.fulfill({json:{enabled:h.enabled}});});
  await context.route('**/api/inventory',route=>route.fulfill({json:{state:h.unavailable?'unavailable':'connected',models:h.unavailable?[]:h.items}}));
  await context.route('**/api/model-check',async route=>{
    const selection=route.request().postDataJSON(),fail=h.fail;h.waiting.resolve();if(h.hold)await h.release.promise;
    await route.fulfill({status:fail?400:200,json:fail?{error:'synthetic_unavailable'}:{model:selection.model,reported_digest:selection.digest,runtime_version:'synthetic-browser',reported_details:{quantization_level:'Q4_SYNTHETIC'},reported_context_length:4096,reported_capabilities:['completion'],reported_thinking_can_disable:true,requested_configuration:{options:{num_ctx:4096,num_predict:256},deadline_seconds:10},observed_at:'2026-11-05T00:00:00Z'}});
  });
  h.refresh=async()=>{await page.locator('#refresh-models').click();await page.waitForFunction(()=>!document.querySelector('#refresh-models').disabled);};
  h.choose=async(item)=>{const options=await page.locator('#model option').evaluateAll(options=>options.map(o=>({model:o.value,digest:o.dataset.digest})));const index=item?options.findIndex(o=>o.model===item.name&&o.digest===item.digest):0;assert.ok(index>=0);await page.locator('#model').selectOption({index});};
  h.check=async()=>{await page.locator('#check-model').click();await page.waitForFunction(()=>!document.querySelector('#check-model').disabled);assert.match(await page.locator('#model-facts').innerText(),/Q4_SYNTHETIC/);};
  h.cleared=async()=>assert.doesNotMatch(await page.locator('#model-facts').innerText(),/Q4_SYNTHETIC|Reported digest|Checking selected/);
  try{
    await page.goto(baseURL);await page.locator('#choose-source-brief').click();await page.waitForFunction(()=>document.querySelector('#version').textContent.includes('v0.'));
    await page.locator('#task-options > summary').click();
    await page.locator('#model-details-toggle').click();await page.locator('#ai-mode').selectOption('trial');
    await page.getByText('This computer & selected model',{exact:true}).click();
    await h.refresh();await h.choose(A);await run(h);assert.deepEqual(errors,[]);passed++;console.log('PASS '+label);
  }finally{
    h.release.resolve();
    // The page keeps polling /api/state; detach routes before closing so an
    // in-flight handler cannot reject with a disposed response after a pass.
    await context.unrouteAll({behavior:'ignoreErrors'});
    await context.close();
  }
}
let baseURL;
(async()=>{
  baseURL=await waitForServer(server);
  browser=await chromium.launch({headless:true,...(process.env.SB_CHROMIUM_EXECUTABLE?{executablePath:process.env.SB_CHROMIUM_EXECUTABLE}:{})});console.log('Chromium '+browser.version());
  await scenario('direct name change and empty selection',async h=>{await h.check();await h.choose(B);await h.cleared();await h.check();await h.choose(null);await h.cleared();});
  await scenario('replacement keeps exact pin until explicit digest selection',async h=>{
    await h.check();h.items=[C,B];await h.refresh();await h.cleared();assert.match(await h.page.locator('#model-identity').innerText(),/unavailable or changed/);
    assert.equal(await h.page.locator('#model option:checked').getAttribute('data-digest'),A.digest);
    await h.choose(C);await h.cleared();await h.check();assert.match(await h.page.locator('#model-facts').innerText(),new RegExp(C.digest));
  });
  for(const kind of ['remove','empty','unavailable'])await scenario(kind+' clears previous metadata',async h=>{await h.check();h.items=kind==='remove'?[B]:[];h.unavailable=kind==='unavailable';await h.refresh();await h.cleared();if(h.unavailable)assert.match(await h.page.locator('#readiness-status').innerText(),/Inventory unavailable/);});
  for(const fail of [false,true])for(const kind of ['replace','remove','unavailable','A/B/A'])await scenario(`late ${fail?'failure':'success'} after ${kind}`,async h=>{
    h.hold=true;h.fail=fail;await h.page.locator('#check-model').click();await h.waiting.promise;
    if(kind==='A/B/A'){await h.choose(B);await h.choose(A);}else{h.items=kind==='replace'?[C,B]:[B];h.unavailable=kind==='unavailable';await h.refresh();}
    await h.cleared();const status=await h.page.locator('#readiness-status').innerText();h.release.resolve();
    await h.page.waitForFunction(()=>!document.querySelector('#check-model').disabled);await h.cleared();assert.equal(await h.page.locator('#readiness-status').innerText(),status);
    h.hold=false;h.fail=false;h.unavailable=false;h.items=[A,B];await h.refresh();await h.choose(A);await h.check();
  });
  await scenario('Local AI off/on revokes pending check',async h=>{
    h.hold=true;await h.page.locator('#check-model').click();await h.waiting.promise;await h.page.locator('#local-ai').uncheck();await h.page.locator('#local-ai').check();h.release.resolve();
    await h.page.waitForFunction(()=>!document.querySelector('#check-model').disabled);await h.cleared();
  });
  console.log(`${passed} Chromium readiness scenarios passed; metadata is synthetic, accuracy is unqualified.`);
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.kill('SIGINT');});
