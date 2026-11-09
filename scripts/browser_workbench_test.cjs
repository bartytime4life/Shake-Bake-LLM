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
async function openOptions(page){
  if(!await page.locator('#task-options').evaluate(el=>el.open))await page.locator('#task-options > summary').click();
}
async function chooseKind(page,kind){
  await openOptions(page);await page.locator(`input[name="task-kind"][value="${kind}"]`).check();
}
async function setLocalAI(page,enabled){
  await openOptions(page);await page.locator('#local-ai').setChecked(enabled);
}
async function openHistory(page){
  if(!await page.locator('#recent-section').isVisible())await page.locator('#history-nav').click();
}
async function selectBrief(page,request){
  await openHistory(page);await page.getByRole('button',{name:new RegExp(request)}).click();
}
async function prepare(page,request){
  await page.locator('#request').fill(request);await page.locator('#prepare').click();
  await page.waitForFunction(text=>document.querySelector('#original-request').textContent===text,request);
  await page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
  await page.waitForFunction(text=>[...document.querySelectorAll('#recent-list strong')].some(el=>el.textContent===text),request);
}
async function scenario(label,run,{startupFailure=false,preview=null,setup=null,waitForStartup=true}={}){
  const context=await browser.newContext({reducedMotion:'reduce'}),page=await context.newPage();
  page.setDefaultTimeout(10000);
  if(preview)await context.addInitScript(value=>{window.__SB_RECORDED_PREVIEW__=value;},preview);
  const h={page,context,enabled:true,policyEnabled:true,failState:startupFailure,failSettings:false,loseSettings:false,
    settingsWait:null,settingsSeen:deferred(),stateWait:null,stateSeen:deferred(),tasks:0,apiCalls:0,releases:[],modelCalls:0,settingsCalls:0};
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  // The page polls /api/state every few seconds. A poll still in flight when a
  // finished scenario closes its context has its fetched response disposed; the
  // route handler then rejects after the assertions already passed. Only such
  // post-close failures are ignored; any error on an open page still fails the run.
  const guarded=handler=>async route=>{
    try{await handler(route);}
    catch(error){if(page.isClosed())return;throw error;}
  };
  await context.route('**/api/**',guarded(async route=>{
    h.apiCalls++;const url=new URL(route.request().url());
    if(url.pathname==='/api/tasks'&&route.request().method()==='POST')h.tasks++;
    if(['/api/inventory','/api/model-check'].includes(url.pathname))h.modelCalls++;
    await route.fallback();
  }));
  await context.route('**/api/state',guarded(async route=>{
    h.apiCalls++;
    if(h.failState){await route.fulfill({status:503,body:''});return;}
    const response=await route.fetch(),value=await response.json();
    const result={...value,local_ai_enabled:h.enabled,policy:{...value.policy,enabled:h.policyEnabled}};
    if(h.stateTransform)h.stateTransform(result);
    const wait=h.stateWait;h.stateWait=null;
    if(wait){h.stateSeen.resolve();await wait.promise;}
    await route.fulfill(h.failOldState&&wait?{status:503,json:{error:'synthetic_old_failure'}}:{json:result});
  }));
  await context.route('**/api/settings',guarded(async route=>{
    h.apiCalls++;h.settingsCalls++;h.settingsSeen.resolve();
    if(h.settingsWait)await h.settingsWait.promise;
    if(h.failSettings){await route.fulfill({status:503,json:{error:'synthetic_write_failure'}});return;}
    h.enabled=h.policyEnabled&&route.request().postDataJSON().enabled;
    if(h.loseSettings){await route.abort('failed');return;}
    await route.fulfill({json:{enabled:h.enabled}});
  }));
  h.defer=()=>{const wait=deferred();h.releases.push(wait);return wait;};
  try{
    if(setup)await setup(h);
    await page.goto(baseURL);
    if(waitForStartup)await page.waitForFunction(()=>document.querySelector('#version').textContent.includes('v0.')||!document.querySelector('#notice').hidden);
    await run(h);assert.deepEqual(errors,[]);passed++;console.log('PASS '+label);
  }finally{
    h.releases.forEach(wait=>wait.resolve());
    // Let response readers finish before closing the context disposes their bodies.
    await Promise.all(context.pages().map(page=>page.unrouteAll({behavior:'wait'})));
    await context.unrouteAll({behavior:'wait'});await context.close();
  }
}
(async()=>{
  baseURL=await waitForServer(server);
  browser=await chromium.launch({headless:true,...(process.env.SB_CHROMIUM_EXECUTABLE?{executablePath:process.env.SB_CHROMIUM_EXECUTABLE}:{})});
  console.log('Chromium '+browser.version());
  // The shared controller must still be empty for the first-visit assertions.
  await scenario('ordinary preparation needs no options or model setup',async h=>{
    await h.page.setViewportSize({width:390,height:844});
    assert.equal(await h.page.locator('#request').inputValue(),'');
    assert.equal(await h.page.locator('#project').inputValue(),'starter-demo');
    assert.equal(await h.page.locator('#task-options').evaluate(el=>el.open),false);
    assert.equal(await h.page.locator('#local-ai').isChecked(),false);
    assert.equal(await h.page.locator('#local-ai').isVisible(),false);
    for(const id of ['stop','brief-result','recent-section'])assert.equal(await h.page.locator('#'+id).isVisible(),false,id);
    const request='Find the executable slice coverage guard.';
    await prepare(h.page,request);
    assert.equal(h.tasks,1);assert.equal(h.settingsCalls,0);assert.equal(h.modelCalls,0);
    assert.equal(await h.page.locator('#task-options').evaluate(el=>el.open),false);
    assert.equal(await h.page.locator('#brief-result').isVisible(),true);
    assert.equal(await h.page.locator('#copy').isVisible(),true);
    assert.equal(await h.page.locator('#copy').isEnabled(),true);
    assert.equal(await h.page.locator('#stop').isVisible(),false);
    assert.equal(await h.page.locator('#handoff-copy').evaluate(el=>el.open),false);
    assert.equal(await h.page.locator('#evidence-section').evaluate(el=>el.open),false);
    assert.equal(JSON.parse((await h.page.locator('#handoff-text').inputValue()).split('\n').find(line=>line.startsWith('Request (JSON string): ')).slice('Request (JSON string): '.length)),request);
    assert.equal(await h.page.locator('#brief-title').evaluate(el=>document.activeElement===el),true);
    assert.equal(await h.page.locator('#result-status').getAttribute('role'),'status');
    assert.equal(await h.page.locator('#result-status').getAttribute('aria-live'),'polite');
    assert.match(await h.page.locator('#result-status').textContent(),/brief is ready/i);
    await h.page.keyboard.press('Tab');
    assert.equal(await h.page.locator('#copy').evaluate(el=>document.activeElement===el),true);
  },{setup:async h=>{h.enabled=false;}});
  await scenario('completion announces the captured result without stealing focus from the next draft',async h=>{
    const request='Find the executable slice coverage guard before writing the next draft.';
    const held=h.defer(),seen=deferred();let once=true;
    await h.page.route('**/api/tasks/*',async route=>{
      const response=await route.fetch(),value=await response.json();
      if(once&&value.state==='DONE'&&value.original_request===request){once=false;seen.resolve();await held.promise;}
      await route.fulfill({json:value});
    });
    await h.page.locator('#request').fill(request);await h.page.locator('#prepare').click();await seen.promise;
    assert.equal(await h.page.locator('#stop').isVisible(),true);
    assert.equal(await h.page.locator('#result-status').textContent(),'');
    const nextDraft='Keep typing this next request while the previous brief finishes.';
    await h.page.locator('#request').fill(nextDraft);
    const selection=await h.page.locator('#request').evaluate(el=>[el.selectionStart,el.selectionEnd]);
    held.resolve();
    await h.page.waitForFunction(text=>document.querySelector('#original-request').textContent===text,request);
    await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#request').evaluate(el=>document.activeElement===el),true);
    assert.equal(await h.page.locator('#request').inputValue(),nextDraft);
    assert.deepEqual(await h.page.locator('#request').evaluate(el=>[el.selectionStart,el.selectionEnd]),selection);
    assert.match(await h.page.locator('#result-status').textContent(),/brief is ready/i);
    assert.equal(await h.page.locator('#stop').isVisible(),false);
    assert.equal(JSON.parse((await h.page.locator('#handoff-text').inputValue()).split('\n').find(line=>line.startsWith('Request (JSON string): ')).slice('Request (JSON string): '.length)),request);
  });
  await scenario('a saved candidate trial reveals acknowledgement controls without starting work',async h=>{
    assert.equal(await h.page.locator('#local-ai').isChecked(),true);
    assert.equal(await h.page.locator('#ai-mode').inputValue(),'trial');
    await h.page.locator('#request').fill('Find the executable slice coverage guard.');
    if(await h.page.locator('#task-options').evaluate(el=>el.open))await h.page.locator('#task-options > summary').click();
    await h.page.locator('#prepare').click();
    assert.equal(h.tasks,0);assert.equal(h.modelCalls,0);assert.equal(h.settingsCalls,0);
    assert.equal(await h.page.locator('#task-options').evaluate(el=>el.open),true);
    assert.equal(await h.page.locator('#model-details').isVisible(),true);
    assert.equal(await h.page.locator('#model-details-toggle').getAttribute('aria-expanded'),'true');
    assert.equal(await h.page.locator('#trial-ack').isVisible(),true);
    assert.equal(await h.page.locator('#trial-ack').isChecked(),false);
    assert.match(await h.page.locator('#notice').innerText(),/acknowledge/);
  },{setup:async h=>{
    h.stateTransform=value=>{value.allow_candidate_trials=true;};
    await h.page.addInitScript(()=>localStorage.setItem('shake-bake-preferences',JSON.stringify({ai_mode:'trial',model:'fixture:local',digest:'a'.repeat(64)})));
  }});
  await scenario('collection limits remain visible while source review is collapsed',async h=>{
    await h.page.route('**/api/tasks/*',async route=>{
      const response=await route.fetch(),value=await response.json();
      if(value.state==='DONE'){value.cutoffs=['file_budget'];value.exclusions={permission_denied:1};}
      await route.fulfill({json:value});
    });
    await prepare(h.page,'Find the executable slice coverage guard with synthetic collection limits.');
    assert.equal(await h.page.locator('#evidence-section').evaluate(el=>el.open),false);
    assert.equal(await h.page.locator('#gaps-section').isVisible(),true);
    assert.equal(await h.page.locator('#collection-warning').isVisible(),true);
    assert.match(await h.page.locator('#collection-warning').innerText(),/file_budget/);
    assert.match(await h.page.locator('#collection-warning').innerText(),/permission_denied \(1\)/);
  });
  await scenario('source line numbering matches collector CR and Unicode boundaries without changing export',async h=>{
    const contents=['first\rsecond\r','third\u2028fourth\u0085fifth\u2029sixth\vseventh\fthen\x1cnext\x1dlast\x1eend\r\n'];
    await h.page.route('**/api/tasks/*',async route=>{
      const response=await route.fetch(),value=await response.json();
      if(value.state==='DONE')value.evidence.forEach((item,index)=>{
        item.text=contents[index];item.start_line=11;
        item.end_line=11+(index===0?1:8);
      });
      await route.fulfill({json:value});
    });
    await prepare(h.page,'Find executable slice coverage with synthetic alternate source line boundaries.');
    assert.deepEqual(await h.page.locator('.source').nth(0).locator('.line-number').allTextContents(),['11','12']);
    assert.deepEqual(await h.page.locator('.source').nth(0).locator('code').allTextContents(),['first','second']);
    assert.deepEqual(await h.page.locator('.source').nth(1).locator('.line-number').allTextContents(),['11','12','13','14','15','16','17','18','19']);
    assert.deepEqual(await h.page.locator('.source').nth(1).locator('code').allTextContents(),['third','fourth','fifth','sixth','seventh','then','next','last','end']);
    await h.page.locator('#handoff-copy > summary').click();
    const [download]=await Promise.all([h.page.waitForEvent('download'),h.page.locator('#download').click()]);
    const stream=await download.createReadStream(),chunks=[];
    for await(const chunk of stream)chunks.push(chunk);
    const source=JSON.parse(Buffer.concat(chunks).toString('utf8')).packet.evidence;
    assert.deepEqual(source.map(item=>item.text),contents);
    assert.deepEqual(source.map(item=>item.content),contents);
  });
  await scenario('restored draft keeps its own project and task type',async h=>{
    assert.equal(await h.page.locator('#request').inputValue(),'Preserve this synthetic search draft.');
    assert.equal(await h.page.locator('#project').inputValue(),'starter-demo');
    assert.equal(await h.page.locator('input[name="task-kind"]:checked').inputValue(),'search');
    assert.match(await h.page.locator('#draft-status').innerText(),/saved in this browser/i);
  },{setup:async h=>{
    h.stateTransform=value=>{value.projects.push({...value.projects[0],id:'another-demo'});};
    await h.page.addInitScript(()=>{
      localStorage.setItem('shake-bake-preferences',JSON.stringify({project_id:'another-demo',task_kind:'code'}));
      localStorage.setItem('sb-workbench-draft',JSON.stringify({task:'Preserve this synthetic search draft.',project:'starter-demo',kind:'search'}));
    });
  }});
  await scenario('missing draft project requires an explicit choice before submission',async h=>{
    assert.equal(await h.page.locator('#request').inputValue(),'Keep the request for the unavailable synthetic project.');
    assert.equal(await h.page.locator('#project').inputValue(),'');
    assert.equal(await h.page.locator('#prepare').isDisabled(),true);
    assert.match(await h.page.locator('#project-help').innerText(),/unavailable/);
    await h.page.locator('#task-form').dispatchEvent('submit');assert.equal(h.tasks,0);
    await h.page.locator('#project').selectOption('starter-demo');
    await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('input[name="task-kind"]:checked').inputValue(),'documents');
    assert.equal(await h.page.locator('#request').inputValue(),'Keep the request for the unavailable synthetic project.');
    assert.equal(await h.page.evaluate(()=>JSON.parse(localStorage.getItem('sb-workbench-draft')).project),'starter-demo');
  },{setup:async h=>{await h.page.addInitScript(()=>{
    localStorage.setItem('sb-workbench-draft',JSON.stringify({task:'Keep the request for the unavailable synthetic project.',project:'missing-demo',kind:'documents'}));
  });}});
  await scenario('typing during initial connection survives restoration even when saving fails',async h=>{
    await h.stateSeen.promise;
    await h.page.locator('#request').fill('New text typed while the connection is pending.');
    await chooseKind(h.page,'search');
    assert.match(await h.page.locator('#draft-status').innerText(),/this page/);
    h.releases[0].resolve();await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#request').inputValue(),'New text typed while the connection is pending.');
    assert.equal(await h.page.locator('input[name="task-kind"]:checked').inputValue(),'search');
    assert.match(await h.page.locator('#draft-status').innerText(),/could not be saved/);
    assert.equal(await h.page.evaluate(()=>JSON.parse(localStorage.getItem('sb-workbench-draft')).task),'Older synthetic draft.');
  },{waitForStartup:false,setup:async h=>{
    h.stateWait=h.defer();await h.page.addInitScript(()=>{
      localStorage.setItem('sb-workbench-draft',JSON.stringify({task:'Older synthetic draft.',project:'starter-demo',kind:'code'}));
      Storage.prototype.setItem=function(){throw new DOMException('Synthetic full storage','QuotaExceededError');};
    });
  }});
  await scenario('unknown saved task type requires an explicit supported choice',async h=>{
    assert.equal(await h.page.locator('#request').inputValue(),'Preserve the synthetic request with an unavailable task type.');
    assert.equal(await h.page.locator('#prepare').isDisabled(),true);
    assert.equal(await h.page.locator('input[name="task-kind"]:checked').count(),0);
    assert.match(await h.page.locator('#project-help').innerText(),/task type is unavailable/);
    assert.equal(await h.page.locator('#task-options').evaluate(el=>el.open),true);
    assert.equal(await h.page.getByText('Task type',{exact:true}).isVisible(),true);
    await h.page.locator('#task-form').dispatchEvent('submit');assert.equal(h.tasks,0);
    await h.page.locator('input[name="task-kind"][value="search"]').check();
    await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.evaluate(()=>JSON.parse(localStorage.getItem('sb-workbench-draft')).kind),'search');
  },{setup:async h=>{await h.page.addInitScript(()=>{
    localStorage.setItem('sb-workbench-draft',JSON.stringify({task:'Preserve the synthetic request with an unavailable task type.',project:'starter-demo',kind:'unsupported'}));
  });}});
  await scenario('storage failure is visible, recovery saves exact text, and reload retains the draft context',async h=>{
    await prepare(h.page,'Find coverage before editing the next draft.');
    const pin=await h.page.locator('#handoff-text').inputValue();
    await h.page.evaluate(()=>{window.originalStorageSet=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(key==='sb-workbench-draft')throw new DOMException('Synthetic full storage','QuotaExceededError');return window.originalStorageSet.call(this,key,value);};});
    const draft='  Exact synthetic draft: α <untrusted>\nKeep the final space. ';
    await h.page.locator('#request').fill(draft);await chooseKind(h.page,'documents');
    assert.match(await h.page.locator('#draft-status').innerText(),/could not be saved/);
    assert.equal(await h.page.locator('#handoff-text').inputValue(),pin);
    assert.equal(await h.page.locator('#copy').isEnabled(),true);
    await h.page.evaluate(()=>{Storage.prototype.setItem=window.originalStorageSet;});
    await h.page.locator('#request').dispatchEvent('input');
    assert.match(await h.page.locator('#draft-status').innerText(),/saved in this browser/);
    assert.equal(await h.page.evaluate(()=>JSON.parse(localStorage.getItem('sb-workbench-draft')).task),draft);
    await h.page.reload();await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#request').inputValue(),draft);
    assert.equal(await h.page.locator('input[name="task-kind"]:checked').inputValue(),'documents');
    assert.equal(await h.page.locator('#project').inputValue(),'starter-demo');
    assert.equal(await h.page.locator('#handoff-text').inputValue(),pin);
    if(process.env.SB_DRAFT_SCREENSHOT){await h.page.setViewportSize({width:390,height:844});await h.page.screenshot({path:process.env.SB_DRAFT_SCREENSHOT,fullPage:true});}
  });
  await scenario('draft opt-out removes storage, preserves current text and brief, and survives reload',async h=>{
    await prepare(h.page,'Find coverage before turning draft saving off.');
    const pin=await h.page.locator('#handoff-text').inputValue();
    await chooseKind(h.page,'documents');
    await h.page.locator('#save-draft').uncheck();
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-save-draft')),'off');
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
    assert.equal(await h.page.locator('#request').inputValue(),'Find coverage before turning draft saving off.');
    assert.equal(await h.page.locator('#handoff-text').inputValue(),pin);
    const unsaved='  Private synthetic draft: α <reference>\nKeep exact whitespace. ';
    await h.page.locator('#request').fill(unsaved);await chooseKind(h.page,'search');
    assert.equal(await h.page.locator('#request').inputValue(),unsaved);
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
    // Capture from the document top so offscreen fixed skip links stay outside
    // the full-page screenshot instead of appearing over scrolled content.
    if(process.env.SB_DRAFT_PRIVACY_SCREENSHOT||process.env.SB_DRAFT_PRIVACY_PHONE_SCREENSHOT)await h.page.locator('#workspace-nav').scrollIntoViewIfNeeded();
    if(process.env.SB_DRAFT_PRIVACY_SCREENSHOT){
      await h.page.setViewportSize({width:1280,height:900});
      await h.page.screenshot({path:process.env.SB_DRAFT_PRIVACY_SCREENSHOT,fullPage:true});
    }
    if(process.env.SB_DRAFT_PRIVACY_PHONE_SCREENSHOT){
      await h.page.setViewportSize({width:390,height:844});
      await h.page.screenshot({path:process.env.SB_DRAFT_PRIVACY_PHONE_SCREENSHOT,fullPage:true});
    }
    await h.page.reload();await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#save-draft').isChecked(),false);
    assert.equal(await h.page.locator('#request').inputValue(),'');
    assert.equal(await h.page.locator('input[name="task-kind"]:checked').inputValue(),'search');
    assert.equal(await h.page.locator('#handoff-text').inputValue(),pin);
    await h.page.locator('#request').fill('Only save after enabling again.');
    await openOptions(h.page);await h.page.locator('#save-draft').check();
    assert.equal(await h.page.evaluate(()=>JSON.parse(localStorage.getItem('sb-workbench-draft')).task),'Only save after enabling again.');
  });
  await scenario('saved opt-out ignores and removes a stale browser draft',async h=>{
    assert.equal(await h.page.locator('#save-draft').isChecked(),false);
    assert.equal(await h.page.locator('#request').inputValue(),'');
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
    assert.match(await h.page.locator('#draft-status').innerText(),/saving is off/i);
  },{setup:async h=>{await h.page.addInitScript(()=>{
    localStorage.setItem('sb-workbench-save-draft','off');
    localStorage.setItem('sb-workbench-draft',JSON.stringify({task:'Do not restore this stale synthetic draft.',project:'starter-demo',kind:'code'}));
  });}});
  await scenario('opting out during initial connection preserves new text without restoring an older draft',async h=>{
    await h.stateSeen.promise;
    await h.page.locator('#request').fill('Keep this new synthetic text while startup is pending.');
    await chooseKind(h.page,'search');await h.page.locator('#save-draft').uncheck();
    h.releases[0].resolve();await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#request').inputValue(),'Keep this new synthetic text while startup is pending.');
    assert.equal(await h.page.locator('input[name="task-kind"]:checked').inputValue(),'search');
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
    assert.equal(await h.page.locator('#save-draft').isChecked(),false);
  },{waitForStartup:false,setup:async h=>{
    h.stateWait=h.defer();await h.page.addInitScript(()=>localStorage.setItem('sb-workbench-draft',JSON.stringify({task:'Do not restore this older synthetic request.',project:'starter-demo',kind:'code'})));
  }});
  await scenario('another tab can opt out without erasing current text, including a delayed storage event',async h=>{
    const draft='Keep this synthetic request in memory across tab changes.';
    await h.page.locator('#request').fill(draft);
    const other=await h.context.newPage();await other.goto(baseURL);
    await other.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    await openOptions(other);await other.locator('#save-draft').uncheck();
    await h.page.waitForFunction(()=>!document.querySelector('#save-draft').checked);
    assert.equal(await h.page.locator('#request').inputValue(),draft);
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
    await other.locator('#save-draft').check();
    await h.page.waitForFunction(()=>document.querySelector('#save-draft').checked);
    await h.page.evaluate(()=>{window.blockDraftStorageEvents=true;});
    await other.locator('#save-draft').uncheck();
    assert.equal(await h.page.locator('#save-draft').isChecked(),true);
    await h.page.locator('#request').fill(draft+' New exact text.');
    assert.equal(await h.page.locator('#save-draft').isChecked(),false);
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
    assert.equal(await h.page.locator('#request').inputValue(),draft+' New exact text.');
    await h.page.evaluate(()=>{window.blockDraftStorageEvents=false;});
    await other.evaluate(()=>localStorage.clear());
    await h.page.waitForFunction(()=>document.querySelector('#draft-status').textContent.includes('cleared in another tab'));
    await h.page.locator('#request').fill(draft+' Keep saving off after storage clears.');
    assert.equal(await h.page.locator('#save-draft').isChecked(),false);
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
  },{setup:async h=>{await h.page.addInitScript(()=>window.addEventListener('storage',event=>{if(window.blockDraftStorageEvents)event.stopImmediatePropagation();}));}});
  await scenario('failed opt-out stays off in this page and reports unconfirmed removal and preference',async h=>{
    const original='Find coverage before a synthetic browser storage failure.';
    await h.page.locator('#request').fill(original);await openOptions(h.page);
    await h.page.evaluate(()=>{
      window.originalDraftSet=Storage.prototype.setItem;window.originalDraftRemove=Storage.prototype.removeItem;
      Storage.prototype.setItem=function(key,value){if(key==='sb-workbench-save-draft')throw new DOMException('Synthetic blocked setting','SecurityError');return window.originalDraftSet.call(this,key,value);};
      Storage.prototype.removeItem=function(key){if(key==='sb-workbench-draft')throw new DOMException('Synthetic blocked removal','SecurityError');return window.originalDraftRemove.call(this,key);};
    });
    await h.page.locator('#save-draft').uncheck();
    assert.equal(await h.page.locator('#save-draft').isChecked(),false);
    assert.match(await h.page.locator('#draft-status').innerText(),/could not confirm the saved choice or removal/i);
    await h.page.locator('#request').fill('New synthetic text must never overwrite the older draft.');
    assert.equal(await h.page.evaluate(()=>JSON.parse(localStorage.getItem('sb-workbench-draft')).task),original);
    await h.page.evaluate(()=>{Storage.prototype.setItem=window.originalDraftSet;Storage.prototype.removeItem=window.originalDraftRemove;});
    await h.page.locator('#request').dispatchEvent('input');
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-save-draft')),'off');
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
    assert.match(await h.page.locator('#draft-status').innerText(),/saving is off/i);
    await h.page.evaluate(()=>{Storage.prototype.setItem=function(key,value){if(key==='sb-workbench-save-draft')throw new DOMException('Synthetic blocked setting','SecurityError');return window.originalDraftSet.call(this,key,value);};});
    await h.page.locator('#save-draft').click();
    assert.equal(await h.page.locator('#save-draft').isChecked(),false);
    assert.match(await h.page.locator('#draft-status').innerText(),/could not be enabled/i);
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
  });
  await scenario('an opt-out between the preference check and task write cannot leave a saved draft',async h=>{
    await h.page.locator('#request').fill('A synthetic draft before the interleaved opt-out.');
    await h.page.evaluate(()=>{
      const originalSet=Storage.prototype.setItem;
      Storage.prototype.setItem=function(key,value){
        if(key==='sb-workbench-draft'){
          originalSet.call(this,'sb-workbench-save-draft','off');
          this.removeItem('sb-workbench-draft');
        }
        return originalSet.call(this,key,value);
      };
    });
    await h.page.locator('#request').fill('Keep this exact synthetic task only on the page.');
    assert.equal(await h.page.locator('#save-draft').isChecked(),false);
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
    assert.equal(await h.page.locator('#request').inputValue(),'Keep this exact synthetic task only on the page.');
  });
  await scenario('clear draft removes only task text and never recreates an empty saved record',async h=>{
    await prepare(h.page,'Find coverage before clearing the task draft.');
    const pin=await h.page.locator('#handoff-text').inputValue();
    await chooseKind(h.page,'documents');
    const preferences=await h.page.evaluate(()=>localStorage.getItem('shake-bake-preferences'));
    await h.page.evaluate(()=>{
      window.originalDraftRemove=Storage.prototype.removeItem;
      Storage.prototype.removeItem=function(key){if(key==='sb-workbench-draft')throw new DOMException('Synthetic blocked removal','SecurityError');return window.originalDraftRemove.call(this,key);};
    });
    await h.page.locator('#clear-draft').click();
    assert.equal(await h.page.locator('#request').inputValue(),'');
    assert.match(await h.page.locator('#draft-status').innerText(),/saved draft could not be removed/i);
    assert.equal(await h.page.evaluate(()=>JSON.parse(localStorage.getItem('sb-workbench-draft')).task),'Find coverage before clearing the task draft.');
    await h.page.evaluate(()=>{Storage.prototype.removeItem=window.originalDraftRemove;});
    await h.page.locator('#clear-draft').click();
    assert.equal(await h.page.locator('#request').inputValue(),'');
    assert.equal(await h.page.locator('#request').evaluate(el=>document.activeElement===el),true);
    assert.equal(await h.page.locator('#handoff-text').inputValue(),pin);
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('shake-bake-preferences')),preferences);
    assert.match(await h.page.locator('#draft-status').innerText(),/draft cleared/i);
    await chooseKind(h.page,'search');
    assert.equal(await h.page.evaluate(()=>localStorage.getItem('sb-workbench-draft')),null);
    await h.page.reload();await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#request').inputValue(),'');
    assert.equal(await h.page.locator('input[name="task-kind"]:checked').inputValue(),'search');
    assert.equal(await h.page.locator('#handoff-text').inputValue(),pin);
  });
  for(const outcome of ['success','failure'])for(const next of ['task','selection'])await scenario(`late startup brief ${outcome} cannot replace a newer ${next}`,async h=>{
    const older=`Find coverage: retained ${outcome} ${next}`,latest=`Find coverage: startup ${outcome} ${next}`;
    await prepare(h.page,older);await prepare(h.page,latest);
    const recent=(await (await h.page.request.get(baseURL+'/api/state')).json()).recent;
    const startup=recent.find(item=>item.task===latest),held=h.defer(),seen=deferred();let once=true;
    await h.page.route('**/api/tasks/*',async route=>{
      const response=await route.fetch(),value=await response.json();
      if(once&&value.task_id===startup.task_id){once=false;seen.resolve();await held.promise;await route.fulfill(outcome==='failure'?{status:400,json:{error:'unknown_or_expired_task'}}:{json:value});}
      else await route.fulfill({json:value});
    });
    await h.page.reload();await seen.promise;
    const expected=next==='selection'?older:`Find coverage: new task after startup ${outcome}`;
    if(next==='selection')await selectBrief(h.page,older);
    else{
      // A task-type change exposed the old startup race by enabling Prepare.
      // Hold the new acknowledgement until DONE so the pre-fix startup timer
      // delay cannot hide the stale-result regression behind a polling timeout.
      await h.page.route('**/api/tasks',async route=>{
        const response=await route.fetch(),started=await response.json();let result;
        for(let i=0;i<100;i++){
          result=await (await h.page.request.get(baseURL+'/api/tasks/'+started.task_id)).json();
          if(result.state!=='RUNNING')break;
          await new Promise(resolve=>setTimeout(resolve,10));
        }
        assert.equal(result.state,'DONE');await route.fulfill({response,json:started});
      });
      await chooseKind(h.page,'search');await prepare(h.page,expected);
    }
    await h.page.waitForFunction(text=>document.querySelector('#original-request').textContent===text,expected);
    const pin=await h.page.locator('#handoff-text').inputValue(),notice=await h.page.locator('#notice').innerText();
    const response=h.page.waitForResponse(r=>r.url().endsWith('/api/tasks/'+startup.task_id));held.resolve();await (await response).finished();await rendered(h.page);
    assert.equal(await h.page.locator('#original-request').textContent(),expected);
    assert.equal(await h.page.locator('#handoff-text').inputValue(),pin);
    assert.equal(await h.page.locator('#notice').innerText(),notice);
    assert.equal(await h.page.locator('#prepare').isEnabled(),true);
  });
  await scenario('pending startup brief leaves controls, history and active polling available',async h=>{
    const older='Find coverage: startup must not block new work.';
    await prepare(h.page,older);
    const startup=(await (await h.page.request.get(baseURL+'/api/state')).json()).recent[0];
    const held=h.defer(),seen=deferred();let once=true,polls=0;
    await h.page.route('**/api/tasks/*',async route=>{
      const response=await route.fetch(),value=await response.json();
      if(once&&value.task_id===startup.task_id){once=false;seen.resolve();await held.promise;await route.fulfill({json:value});return;}
      if(value.task_id!==startup.task_id){polls++;if(polls===1){await route.fulfill({json:{...value,state:'RUNNING'}});return;}}
      await route.fulfill({json:value});
    });
    await h.page.reload();await seen.promise;
    assert.equal(await h.page.locator('#prepare').isEnabled(),true);
    await openHistory(h.page);
    assert.equal(await h.page.getByRole('button',{name:new RegExp(older)}).count(),1);
    const request='Find coverage: finish new preparation while restoration waits.';
    await prepare(h.page,request);assert.ok(polls>=2,'New work must keep polling before the startup brief arrives');
    const response=h.page.waitForResponse(r=>r.url().endsWith('/api/tasks/'+startup.task_id));held.resolve();await (await response).finished();await rendered(h.page);
    assert.equal(await h.page.locator('#original-request').textContent(),request);
  });
  await scenario('stalled initial state times out and can retry without reloading',async h=>{
    await h.stateSeen.promise;await h.page.clock.fastForward(16000);
    await h.page.waitForFunction(()=>!document.querySelector('#retry-connection').hidden);
    assert.match(await h.page.locator('#notice').innerText(),/timed out/);
    h.stateWait=null;await h.page.locator('#retry-connection').click();
    await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(h.tasks,0);
  },{waitForStartup:false,setup:async h=>{await h.page.clock.install();h.stateWait=h.defer();}});
  await scenario('stalled setting times out, reconciles, and preserves the pinned brief and draft',async h=>{
    await prepare(h.page,'Find coverage before a stalled setting.');
    const captured=await h.page.locator('#handoff-text').inputValue();
    await h.page.locator('#request').fill('Keep this timeout recovery draft');
    h.settingsWait=h.defer();await setLocalAI(h.page,false);await h.settingsSeen.promise;
    await h.page.clock.fastForward(16000);
    await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#local-ai').isChecked(),true);
    assert.match(await h.page.locator('#notice').innerText(),/timed out/);
    assert.equal(await h.page.locator('#request').inputValue(),'Keep this timeout recovery draft');
    assert.equal(await h.page.locator('#handoff-text').inputValue(),captured);
  },{setup:async h=>{await h.page.clock.install();}});
  await scenario('lost accepted start response blocks duplicate submission until state is reconciled',async h=>{
    const request='Find coverage after a lost start acknowledgement.';
    const accepted=deferred();
    await h.page.route('**/api/tasks',async route=>{
      h.tasks++;const started=await (await route.fetch()).json();let result;
      // Exercise the completed-history path explicitly; a running job is resumed
      // automatically and can legitimately replace the start warning on completion.
      for(let i=0;i<100;i++){
        result=await (await h.page.request.get(baseURL+'/api/tasks/'+started.task_id)).json();
        if(result.state!=='RUNNING')break;
        await new Promise(resolve=>setTimeout(resolve,10));
      }
      assert.equal(result.state,'DONE');
      h.stateWait=h.defer();await route.abort('failed');accepted.resolve();
    });
    await h.page.locator('#request').fill(request);await h.page.locator('#prepare').click();await accepted.promise;
    await h.page.waitForFunction(()=>document.querySelector('#notice').classList.contains('error'));
    assert.equal(await h.page.locator('#prepare').isDisabled(),true);
    await h.page.locator('#task-form').dispatchEvent('submit');assert.equal(h.tasks,1);
    await h.stateSeen.promise;h.releases[0].resolve();
    await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    await h.page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Check Recent briefs'));
    assert.match(await h.page.locator('#notice').innerText(),/Check Recent briefs/);
    await selectBrief(h.page,request);
    await h.page.waitForFunction(text=>document.querySelector('#original-request').textContent===text,request);
    assert.equal(h.tasks,1);
  });
  await scenario('lost running start response resumes the retained job without repeating it',async h=>{
    let running=true,identifier;
    h.stateTransform=value=>{if(running)for(const item of value.recent)if(item.task_id===identifier)item.state='RUNNING';};
    await h.page.route('**/api/tasks/*',async route=>{
      const value=await (await route.fetch()).json();await route.fulfill({json:running?{...value,state:'RUNNING'}:value});
    });
    await h.page.route('**/api/tasks',async route=>{
      h.tasks++;identifier=(await (await route.fetch()).json()).task_id;await route.abort('failed');
    });
    const request='Find coverage after a lost running-task response.';
    await h.page.locator('#request').fill(request);await h.page.locator('#prepare').click();
    await h.page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Check Recent briefs'));
    assert.equal(await h.page.locator('#stop').isEnabled(),true);
    assert.equal(await h.page.locator('#prepare').isDisabled(),true);assert.equal(h.tasks,1);
    running=false;
    await h.page.waitForFunction(text=>document.querySelector('#original-request').textContent===text,request);
    await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);assert.equal(h.tasks,1);
  });
  await scenario('running job polling reconnects automatically after a transient failure',async h=>{
    let outage=true,running=true,reads=0;
    h.stateTransform=value=>{if(running)for(const item of value.recent)item.state='RUNNING';};
    await h.page.route('**/api/tasks/*',async route=>{
      reads++;if(outage){await route.abort('failed');return;}
      const value=await (await route.fetch()).json();
      await route.fulfill({json:running?{...value,state:'RUNNING'}:value});
    });
    await h.page.locator('#request').fill('Find coverage after a polling outage.');await h.page.locator('#prepare').click();
    await h.page.waitForFunction(()=>!document.querySelector('#retry-connection').hidden);
    outage=false;await h.page.waitForFunction(()=>document.querySelector('#retry-connection').hidden);
    assert.ok(reads>1);assert.equal(await h.page.locator('#prepare').isDisabled(),true);
    assert.equal(await h.page.locator('#stop').isEnabled(),true);
    running=false;await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#original-request').textContent(),'Find coverage after a polling outage.');
  });
  await scenario('pending Local AI change blocks task submission until confirmed',async h=>{
    h.settingsWait=h.defer();await setLocalAI(h.page,false);await h.settingsSeen.promise;
    for(const id of ['prepare','local-ai','refresh-models','check-model'])assert.equal(await h.page.locator('#'+id).isDisabled(),true,id);
    assert.match(await h.page.locator('#progress').innerText(),/Confirming Local AI/);
    await h.page.locator('#task-form').dispatchEvent('submit');assert.equal(h.tasks,0);
    h.settingsWait.resolve();await h.page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#local-ai').isChecked(),false);
  });
  await scenario('failed setting restores the confirmed service value',async h=>{
    h.failSettings=true;await setLocalAI(h.page,false);
    await h.page.waitForFunction(()=>!document.querySelector('#local-ai').disabled);
    assert.equal(await h.page.locator('#local-ai').isChecked(),true);
    assert.match(await h.page.locator('#notice').innerText(),/not confirmed/);
  });
  await scenario('lost setting response reconciles a change the service actually applied',async h=>{
    h.loseSettings=true;await setLocalAI(h.page,false);
    await h.page.waitForFunction(()=>!document.querySelector('#local-ai').disabled);
    assert.equal(await h.page.locator('#local-ai').isChecked(),false);
    assert.equal(await h.page.locator('#prepare').isEnabled(),true);
  });
  await scenario('policy refusal displays the effective disabled setting',async h=>{
    await setLocalAI(h.page,false);await h.page.waitForFunction(()=>!document.querySelector('#local-ai').disabled);
    h.policyEnabled=false;await setLocalAI(h.page,true);
    await h.page.waitForFunction(()=>document.querySelector('#local-ai').disabled&&!document.querySelector('#prepare').disabled);
    assert.equal(await h.page.locator('#local-ai').isChecked(),false);
    assert.match(await h.page.locator('#notice').innerText(),/disabled in this launch configuration/);
  });
  await scenario('unconfirmed setting and unavailable state block new work until retry',async h=>{
    await prepare(h.page,'Find coverage before a synthetic disconnect.');
    const captured=await h.page.locator('#handoff-text').inputValue();
    h.failSettings=true;h.failState=true;await setLocalAI(h.page,false);
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
    const held=h.releases[0];await setLocalAI(h.page,false);
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
    await selectBrief(h.page,first);await seen.promise;
    const expected=next==='selection'?second:`Find coverage: latest task ${outcome}`;
    if(next==='selection')await selectBrief(h.page,second);else await prepare(h.page,expected);
    await h.page.waitForFunction(text=>document.querySelector('#original-request').textContent===text,expected);
    const response=h.page.waitForResponse(r=>/\/api\/tasks\//.test(r.url()));held.resolve();await (await response).finished();await rendered(h.page);
    assert.equal(await h.page.locator('#original-request').textContent(),expected);
    assert.doesNotMatch(await h.page.locator('#notice').innerText(),/unknown_or_expired_task/);
  });
  let recorded;
  await scenario('phone history, keyboard source scrolling and feedback stay usable',async h=>{
    await h.page.setViewportSize({width:390,height:844});
    await prepare(h.page,'Find the executable slice coverage guard for keyboard review.');
    await h.page.locator('#history-nav').click();
    assert.equal(await h.page.locator('#recent-section').isVisible(),true);
    assert.equal(await h.page.locator('#history-nav').getAttribute('aria-expanded'),'true');
    await h.page.locator('#history-nav').click();
    assert.equal(await h.page.locator('#recent-section').isVisible(),false);
    await openHistory(h.page);
    await h.page.locator('#recent-list button').first().focus();await h.page.keyboard.press('Enter');
    await h.page.waitForFunction(()=>document.activeElement.id==='brief-title');
    assert.equal(await h.page.locator('#recent-section').isVisible(),false);
    assert.equal(await h.page.locator('#history-nav').getAttribute('aria-expanded'),'false');
    await h.page.locator('#evidence-section > summary').click();
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
    for(const id of ['prepare','stop','local-ai','refresh-models','check-computer','check-model','save-draft','clear-draft'])assert.equal(await h.page.locator('#'+id).isDisabled(),true,id);
    assert.equal(await h.page.locator('#copy').isEnabled(),true);assert.equal(await h.page.locator('#download').isEnabled(),true);
    const before=await h.page.evaluate(()=>JSON.stringify({...localStorage}));
    await h.page.locator('#save-draft').dispatchEvent('change');await h.page.locator('#clear-draft').dispatchEvent('click');
    assert.equal(await h.page.evaluate(()=>JSON.stringify({...localStorage})),before);
    await h.page.locator('#task-form').dispatchEvent('submit');assert.equal(h.apiCalls,0);
  },{preview:recorded});
  console.log(`${passed} workbench Chromium scenarios passed; these use synthetic source and do not qualify real models or all browsers.`);
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.kill('SIGINT');});
