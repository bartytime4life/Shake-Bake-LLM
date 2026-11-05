// Isolated Chromium and bundled synthetic source only. Never uses a personal browser profile.
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const {chromium} = require('playwright');
const env={...process.env};
if(process.argv[2])delete env.PYTHONPATH;else env.PYTHONPATH=path.join(__dirname,'../src');
const server=spawn(process.argv[2]||'python3',['-u','-c',
  'from shake_bake.gui import Controller, DEMO, WorkbenchServer\nc=Controller({"starter-demo":DEMO})\ns=WorkbenchServer(("127.0.0.1",0),c)\nprint(s.server_port,flush=True)\ntry: s.serve_forever()\nfinally: s.server_close(); c.close()'],{env,stdio:['ignore','pipe','inherit']});
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
  }finally{await context.close();}
}
(async()=>{
  const [chunk]=await once(server.stdout,'data');baseURL='http://127.0.0.1:'+String(chunk).trim();
  browser=await chromium.launch({headless:true});console.log('Chromium '+browser.version());
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
    assert.equal(JSON.parse(text.split('\n')[3]),capturedRequest);assert.ok(text.includes('return len(reported_slices) <= slices_detected'));
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
    await page.locator('#recent-list button').first().click();
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
    await page.locator('#select-handoff').click();
    assert.equal(await page.locator('#handoff-text').evaluate(el=>el.value.slice(el.selectionStart,el.selectionEnd)),text);
    assert.equal(await page.locator('#download').isEnabled(),true);
  });
  console.log(`${passed} isolated Chromium clipboard scenarios passed; personal-browser clipboard behavior remains separately qualified.`);
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.kill('SIGINT');});
