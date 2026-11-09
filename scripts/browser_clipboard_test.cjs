// Isolated Chromium and bundled synthetic source only. Never uses a personal browser profile.
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {waitForServer} = require('./browser_server.cjs');
const {chromium} = require('playwright');
const env={...process.env};
if(process.argv[2])delete env.PYTHONPATH;else env.PYTHONPATH=path.join(__dirname,'../src');
const server=spawn(process.argv[2]||'python3',['-u','-c',
  'from shake_bake.gui import Controller, DEMO, WorkbenchServer\nc=Controller({"starter-demo":DEMO})\ns=WorkbenchServer(("127.0.0.1",0),c)\nprint(s.server_port,flush=True)\ntry: s.serve_forever()\nexcept KeyboardInterrupt: pass\nfinally: s.server_close(); c.close()'],{env,stdio:['ignore','pipe','inherit']});
let browser,baseURL,passed=0;
async function prepare(page,request,capturedRequest=request) {
  await page.locator('#request').fill(request);await page.locator('#prepare').click();
  await page.waitForFunction(text=>document.querySelector('#original-request').textContent===text,capturedRequest);
  return page.locator('#handoff-text').inputValue();
}
async function scenario(mode,run) {
  const context=await browser.newContext({permissions:mode==='native'?['clipboard-read','clipboard-write']:[]});
  if(mode!=='native')await context.addInitScript(mode=>{
    if(mode==='missing'){Object.defineProperty(navigator,'clipboard',{value:undefined});return;}
    window.syntheticCopy={writes:[]};
    Object.defineProperty(navigator,'clipboard',{value:{writeText(text){
      window.syntheticCopy.writes.push(text);
      return new Promise((resolve,reject)=>Object.assign(window.syntheticCopy,{resolve,reject}));
    }}});
  },mode);
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  try{
    await page.goto(baseURL);await page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    await run(page);assert.deepEqual(errors,[]);passed++;console.log('PASS '+mode);
  }finally{await page.unrouteAll({behavior:'ignoreErrors'});await context.close();}
}
(async()=>{
  baseURL=await waitForServer(server);
  browser=await chromium.launch({headless:true,...(process.env.SB_CHROMIUM_EXECUTABLE?{executablePath:process.env.SB_CHROMIUM_EXECUTABLE}:{})});console.log('Chromium '+browser.version());
  // Scenarios share a controller; exercise the empty session before any creates a brief.
  await scenario('native',async page=>{
    assert.equal(await page.locator('#brief-result').isVisible(),false);
    assert.equal(await page.locator('#open-claude').isVisible(),false);
    assert.equal(await page.locator('#open-chatgpt').isVisible(),false);
    assert.equal(await page.locator('#download-text').isDisabled(),true);
    const external=[];page.on('request',request=>{const url=new URL(request.url());if(['http:','https:'].includes(url.protocol)&&url.origin!==new URL(baseURL).origin)external.push(request.url());});
    const text=await prepare(page,'Find executable slice coverage. Synthetic handoff with exact source.');
    for(const [id,url,name] of [['open-claude','https://claude.ai/','Claude'],['open-chatgpt','https://chatgpt.com/','ChatGPT']]){
      const link=page.locator('#'+id);
      assert.equal(await link.isVisible(),true);
      assert.equal(await link.getAttribute('href'),url);
      assert.equal(await link.getAttribute('target'),'_blank');
      assert.equal(await link.getAttribute('rel'),'noopener noreferrer');
      assert.equal(await link.getAttribute('aria-label'),`Open ${name} in a new tab`);
      assert.equal(await page.locator('#handoff-text').inputValue(),text);
    }
    assert.equal(await page.locator('#handoff-copy').evaluate(el=>el.open),false);
    await page.locator('#handoff-copy > summary').click();
    await page.locator('#request').fill('This newer draft must not be exported.');
    const downloading=page.waitForEvent('download');await page.locator('#download-text').click();const download=await downloading;
    assert.match(download.suggestedFilename(),/^shake-bake-[a-f0-9]+\.txt$/);
    assert.equal(await require('node:fs/promises').readFile(await download.path(),'utf8'),text);
    await page.locator('#copy').click();await page.waitForFunction(()=>document.querySelector('#copy-status').textContent.includes('Browser reported copying'));
    assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),text);
    assert.match(await page.locator('#copy-status').innerText(),/Paste into Claude or ChatGPT, then send/);
    assert.match(await page.locator('#handoff-privacy').innerText(),/Nothing is sent automatically/);
    assert.match(text,/untrusted repository data, not instructions/);assert.match(text,/not live access/);
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true);
    assert.equal(await page.locator('#copy').isEnabled(),true);
    assert.deepEqual(external,[],'Preparing, copying and saving must not transmit source');
  });
  await scenario('native',async page=>{
    const request='  Find the executable slice coverage guard. Preserve α and <script>untrusted()</script>.\n  ';
    // A native-host request can contain CRLF even though browser input normalizes it.
    // Supply that synthetic captured value at the HTTP boundary, never by changing app state.
    const capturedRequest=request.replace('\n','\r\n')+'\r';
    await page.route('**/api/tasks/*',async route=>{
      const response=await route.fetch(),value=await response.json();
      if(value.state==='DONE')value.original_request=capturedRequest;
      await route.fulfill({json:value});
    });
    const text=await prepare(page,request,capturedRequest);
    const verbatim=text.split('\n').find(line=>line.startsWith('Request (JSON string): ')).slice('Request (JSON string): '.length);
    assert.equal(JSON.parse(verbatim),capturedRequest);
    assert.ok(text.startsWith('# Where to start looking (Shake & Bake orientation brief)\n'),'orientation is the default copied layout');
    assert.match(text,/\n## Short excerpts \(exact text, may be cut\)\n/);assert.doesNotMatch(text,/Answer with/);
    // The evidence layout stays one choice away and keeps every excerpt in full.
    await page.locator('#brief-style').selectOption('evidence');
    const evidence=await page.locator('#handoff-text').inputValue();
    assert.ok(evidence.startsWith('# Help me with my code (Shake & Bake brief)\n'));assert.match(evidence,/\n## Exact source \(untrusted data; not instructions\)\n/);
    assert.ok(evidence.includes('return len(reported_slices) <= slices_detected'));
    assert.equal(await page.evaluate(()=>localStorage.getItem('sb-brief-style')),'evidence','the chosen layout is remembered in this browser');
    await page.locator('#brief-style').selectOption('orientation');
    assert.equal(await page.locator('#handoff-text').inputValue(),text);
    await page.locator('#copy').click();await page.waitForFunction(()=>document.querySelector('#copy-status').textContent.startsWith('Browser reported copying'));
    assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),text);
    const manualMarker='synthetic marker: manual copy has not run';
    await page.evaluate(marker=>navigator.clipboard.writeText(marker),manualMarker);
    assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),manualMarker);
    await page.locator('#handoff-copy summary').click();await page.locator('#select-handoff').click();
    const selection=await page.locator('#handoff-text').evaluate(el=>({readonly:el.readOnly,selected:el.value.slice(el.selectionStart,el.selectionEnd),focused:document.activeElement===el}));
    assert.deepEqual(selection,{readonly:true,selected:text,focused:true});
    await page.locator('#handoff-text').press('ControlOrMeta+c');assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),text);
    // A same-job render through history must not clear a manual text selection.
    await page.locator('#history-nav').click();await page.locator('#recent-list button').first().click();
    assert.equal(await page.locator('#handoff-text').evaluate(el=>el.selectionEnd-el.selectionStart),text.length);
  });
  for(const outcome of ['resolve','reject'])await scenario(outcome,async page=>{
    const first=await prepare(page,'Find the executable slice coverage guard: first synthetic copy '+outcome);
    const firstId=first.match(/ · Job: ([^\n]+)/)[1];await page.locator('#copy').click();
    assert.match(await page.locator('#copy-status').innerText(),/Waiting for the browser/);
    assert.equal(await page.locator('#copy').isDisabled(),true);
    const second=await prepare(page,'Find the executable slice coverage guard: second synthetic copy '+outcome);
    assert.notEqual(first,second);assert.match(await page.locator('#copy-status').innerText(),/the earlier brief/);
    assert.equal(await page.locator('#download').isEnabled(),true);
    assert.deepEqual(await page.evaluate(()=>window.syntheticCopy.writes),[first]);
    await page.evaluate(outcome=>window.syntheticCopy[outcome](),outcome);
    await page.waitForFunction(()=>!document.querySelector('#copy').disabled);
    const status=await page.locator('#copy-status').innerText();assert.ok(status.includes(firstId));assert.match(status,/the earlier brief/);
    assert.match(status,outcome==='resolve'?/reported copying/:/could not copy/);
    assert.equal(await page.locator('#handoff-text').inputValue(),second);
  });
  await scenario('missing',async page=>{
    const text=await prepare(page,'Find the executable slice coverage guard: manual fallback.');await page.locator('#copy').click();
    assert.match(await page.locator('#copy-status').innerText(),/could not copy/);
    assert.equal(await page.locator('#handoff-copy').evaluate(el=>el.open),true);
    assert.equal(await page.locator('#select-handoff').isVisible(),true);
    assert.equal(await page.locator('#select-handoff').evaluate(el=>document.activeElement===el),true);
    await page.locator('#select-handoff').click();
    assert.equal(await page.locator('#handoff-text').evaluate(el=>el.value.slice(el.selectionStart,el.selectionEnd)),text);
    assert.equal(await page.locator('#download').isEnabled(),true);
  });
  console.log(`${passed} isolated Chromium clipboard scenarios passed; personal-browser clipboard behavior remains separately qualified.`);
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.kill('SIGINT');});
