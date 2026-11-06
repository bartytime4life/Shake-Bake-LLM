// Real DOM/events with the bundled synthetic demo and injected HTTP failures/delays.
// No personal browser profile, Ollama, cloud host, or inspected user project.
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {waitForServer} = require('./browser_server.cjs');
const {chromium} = require('playwright');
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const env={...process.env};
if(process.argv[2])delete env.PYTHONPATH;else env.PYTHONPATH=path.join(__dirname,'../src');
const server=spawn(process.argv[2]||'python3',['-u','-c',
  'from shake_bake.gui import Controller, DEMO, WorkbenchServer\nc=Controller({"starter-demo":DEMO})\nc.call("settings", {"enabled":False})\ns=WorkbenchServer(("127.0.0.1",0),c)\nprint(s.server_port,flush=True)\ntry: s.serve_forever()\nexcept KeyboardInterrupt: pass\nfinally: s.server_close(); c.close()'],{env,stdio:['ignore','pipe','inherit']});
let browser,baseURL,passed=0;
const rendered=page=>page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
async function prepare(page,request){
  await page.locator('#request').fill(request);await page.locator('#prepare').click();
  await page.waitForFunction(text=>document.querySelector('#original-request').textContent===text,request);
  await page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
  await page.waitForFunction(text=>[...document.querySelectorAll('#recent-list strong')].some(el=>el.textContent===text),request);
}
async function scenario(label,run,{startupFailure=false,preview=null}={}){
  const context=await browser.newContext({reducedMotion:'reduce'}),page=await context.newPage();
  page.setDefaultTimeout(10000);
  if(preview)await context.addInitScript(value=>{window.__SB_RECORDED_PREVIEW__=value;},preview);
  const h={page,enabled:true,policyEnabled:true,failState:startupFailure,failSettings:false,loseSettings:false,
    settingsWait:null,settingsSeen:deferred(),stateWait:null,stateSeen:deferred(),tasks:0,apiCalls:0,releases:[]};
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await context.route('**/api/**',async route=>{
    h.apiCalls++;const url=new URL(route.request().url());
    if(url.pathname==='/api/tasks'&&route.request().method()==='POST')h.tasks++;
    await route.fallback();
  });
  await context.route('**/api/state',async route=>{
    h.apiCalls++;
    if(h.failState){await route.fulfill({status:503,body:''});return;}
    const response=await route.fetch(),value=await response.json();
    const result={...value,local_ai_enabled:h.enabled,policy:{...value.policy,enabled:h.policyEnabled}};
    const wait=h.stateWait;h.stateWait=null;
    if(wait){h.stateSeen.resolve();await wait.promise;}
    await route.fulfill(h.failOldState&&wait?{status:503,json:{error:'synthetic_old_failure'}}:{json:result});
  });
  await context.route('**/api/settings',async route=>{
    h.apiCalls++;h.settingsSeen.resolve();
    if(h.settingsWait)await h.settingsWait.promise;
    if(h.failSettings){await route.fulfill({status:503,json:{error:'synthetic_write_failure'}});return;}
    h.enabled=h.policyEnabled&&route.request().postDataJSON().enabled;
    if(h.loseSettings){await route.abort('failed');return;}
    await route.fulfill({json:{enabled:h.enabled}});
  });
  h.defer=()=>{const wait=deferred();h.releases.push(wait);return wait;};
  try{
    await page.goto(baseURL);
    await page.waitForFunction(()=>document.querySelector('#version').textContent.includes('v0.')||!document.querySelector('#notice').hidden);
    await run(h);assert.deepEqual(errors,[]);passed++;console.log('PASS '+label);
  }finally{h.releases.forEach(wait=>wait.resolve());await context.close();}
}
(async()=>{
  baseURL=await waitForServer(server);
  browser=await chromium.launch({headless:true,...(process.env.SB_CHROMIUM_EXECUTABLE?{executablePath:process.env.SB_CHROMIUM_EXECUTABLE}:{})});
  console.log('Chromium '+browser.version());
  await scenario('pending Local AI change blocks task submission until confirmed',async h=>{
    h.settingsWait=h.defer();await h.page.locator('#local-ai').uncheck();await h.settingsSeen.promise;
    for(const id of ['prepare','local-ai','refresh-models','check-model'])assert.equal(await h.page.locator('#'+id).isDisabled(),true,id);
    assert.match(await h.page.locator('#progress').innerText(),/Confirming Local AI/);
    await h.page.locator('#task-form').dispatchEvent('submit');assert.equal(h.tasks,0);
    h.settingsWait.resolve();await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#local-ai').isChecked(),false);
  });
  await scenario('failed setting restores the confirmed service value',async h=>{
    h.failSettings=true;await h.page.locator('#local-ai').uncheck();
    await h.page.waitForFunction(()=>!document.querySelector('#local-ai').disabled);
    assert.equal(await h.page.locator('#local-ai').isChecked(),true);
    assert.match(await h.page.locator('#notice').innerText(),/not confirmed/);
  });
  await scenario('lost setting response reconciles a change the service actually applied',async h=>{
    h.loseSettings=true;await h.page.locator('#local-ai').uncheck();
    await h.page.waitForFunction(()=>!document.querySelector('#local-ai').disabled);
    assert.equal(await h.page.locator('#local-ai').isChecked(),false);
    assert.equal(await h.page.locator('#prepare').isEnabled(),true);
  });
  await scenario('policy refusal displays the effective disabled setting',async h=>{
    await h.page.locator('#local-ai').uncheck();await h.page.waitForFunction(()=>!document.querySelector('#local-ai').disabled);
    h.policyEnabled=false;await h.page.locator('#local-ai').check();
    await h.page.waitForFunction(()=>document.querySelector('#local-ai').disabled&&!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#local-ai').isChecked(),false);
    assert.match(await h.page.locator('#notice').innerText(),/disabled in this launch configuration/);
  });
  await scenario('unconfirmed setting and unavailable state block new work until retry',async h=>{
    await prepare(h.page,'Find coverage before a synthetic disconnect.');
    const captured=await h.page.locator('#handoff-text').inputValue();
    h.failSettings=true;h.failState=true;await h.page.locator('#local-ai').uncheck();
    await h.page.waitForFunction(()=>!document.querySelector('#retry-connection').hidden);
    assert.equal(await h.page.locator('#prepare').isDisabled(),true);
    assert.equal(await h.page.locator('#copy').isEnabled(),true);assert.equal(await h.page.locator('#download').isEnabled(),true);
    await h.page.locator('#request').fill('My unchanged recovery draft');
    h.failState=false;h.enabled=false;await h.page.locator('#retry-connection').click();
    await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#local-ai').isChecked(),false);
    assert.equal(await h.page.locator('#request').inputValue(),'My unchanged recovery draft');
    assert.equal(await h.page.locator('#handoff-text').inputValue(),captured);
  });
  await scenario('initial non-JSON outage has an actionable retry',async h=>{
    assert.equal(await h.page.locator('#prepare').isDisabled(),true);
    assert.match(await h.page.locator('#notice').innerText(),/HTTP 503/);
    h.failState=false;await h.page.locator('#retry-connection').click();
    await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
  },{startupFailure:true});
  for(const failure of [false,true])await scenario(`late state ${failure?'failure':'success'} cannot undo a confirmed toggle`,async h=>{
    h.stateWait=h.defer();h.failOldState=failure;await h.stateSeen.promise;
    const held=h.releases[0];await h.page.locator('#local-ai').uncheck();
    await h.page.waitForFunction(()=>!document.querySelector('#local-ai').disabled);
    const response=h.page.waitForResponse(r=>r.url().endsWith('/api/state'));
    held.resolve();await (await response).finished();await rendered(h.page);
    assert.equal(await h.page.locator('#local-ai').isChecked(),false);
    assert.equal(await h.page.locator('#prepare').isEnabled(),true);
  });
  for(const outcome of ['success','failure'])for(const next of ['selection','task'])await scenario(`late history ${outcome} cannot replace a newer ${next}`,async h=>{
    const first=`Find coverage: older ${outcome} ${next}`,second=`Find coverage: newer ${outcome} ${next}`;
    await prepare(h.page,first);await prepare(h.page,second);
    const held=h.defer(),seen=deferred();let once=true;
    await h.page.route('**/api/tasks/*',async route=>{
      const response=await route.fetch(),value=await response.json();
      if(once){once=false;seen.resolve();await held.promise;await route.fulfill(outcome==='failure'?{status:400,json:{error:'unknown_or_expired_task'}}:{json:value});}
      else await route.fulfill({json:value});
    });
    await h.page.getByRole('button',{name:new RegExp(first)}).click();await seen.promise;
    const expected=next==='selection'?second:`Find coverage: latest task ${outcome}`;
    if(next==='selection')await h.page.getByRole('button',{name:new RegExp(second)}).click();else await prepare(h.page,expected);
    await h.page.waitForFunction(text=>document.querySelector('#original-request').textContent===text,expected);
    const response=h.page.waitForResponse(r=>/\/api\/tasks\//.test(r.url()));held.resolve();await (await response).finished();await rendered(h.page);
    assert.equal(await h.page.locator('#original-request').textContent(),expected);
    assert.doesNotMatch(await h.page.locator('#notice').innerText(),/unknown_or_expired_task/);
  });
  let recorded;
  await scenario('phone history, keyboard source scrolling and feedback stay usable',async h=>{
    await h.page.setViewportSize({width:390,height:844});
    await prepare(h.page,'Find the executable slice coverage guard for keyboard review.');
    await h.page.locator('#history-nav').click();await h.page.locator('#history-nav').click();
    assert.equal(await h.page.locator('#recent-section').isVisible(),true);
    await h.page.locator('#recent-list button').first().focus();await h.page.keyboard.press('Enter');
    await h.page.waitForFunction(()=>document.activeElement.id==='brief-title');
    assert.equal(await h.page.locator('#recent-section').isVisible(),false);
    assert.equal(await h.page.locator('#workspace-nav').getAttribute('aria-pressed'),'true');
    const source=h.page.locator('.source pre').first();await source.focus();await h.page.keyboard.press('ArrowRight');
    await h.page.waitForFunction(()=>document.querySelector('.source pre').scrollLeft>0);
    const notice=await h.page.locator('#notice').boundingBox(),action=await h.page.locator('.action-row').boundingBox();
    assert.ok(notice.y>=action.y+action.height,'Feedback must not overlay action buttons');
    for(const width of [320,390,600,850,851,1024,1440]){
      await h.page.setViewportSize({width,height:900});
      assert.equal(await h.page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`page overflow at ${width}px`);
    }
    const state=await (await h.page.request.get(baseURL+'/api/state')).json();
    const result=await (await h.page.request.get(baseURL+'/api/tasks/'+state.recent[0].task_id)).json();
    recorded={state,result};
  });
  await scenario('recorded preview disables work and keeps evidence export',async h=>{
    for(const id of ['prepare','stop','local-ai','refresh-models','check-computer','check-model'])assert.equal(await h.page.locator('#'+id).isDisabled(),true,id);
    assert.equal(await h.page.locator('#copy').isEnabled(),true);assert.equal(await h.page.locator('#download').isEnabled(),true);
    await h.page.locator('#task-form').dispatchEvent('submit');assert.equal(h.apiCalls,0);
  },{preview:recorded});
  console.log(`${passed} workbench Chromium scenarios passed; these use synthetic source and do not qualify real models or all browsers.`);
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.kill('SIGINT');});
