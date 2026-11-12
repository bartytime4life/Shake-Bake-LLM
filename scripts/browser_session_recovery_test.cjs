// Disposable servers and generated source only. No user preview, models or clipboard.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const {chromium} = require('playwright');
const {waitForServer} = require('./browser_server.cjs');
const deferred = () => {let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};};
const env={...process.env};
if(process.argv[2])delete env.PYTHONPATH;else env.PYTHONPATH=path.join(__dirname,'../src');
const python = String.raw`import json, sys, time
import shake_bake.gui as gui
roots={"starter-demo":gui.DEMO,"fixture":sys.argv[1]}
roots.update(json.loads(sys.argv[5]))
c=gui.Controller(roots)
c.call("settings", {"enabled":False})
if sys.argv[4]: gui.__version__=sys.argv[4]
original=gui.Handler.do_GET
mode=sys.argv[3]
def get(self):
    if self.path != "/" or mode == "normal": return original(self)
    if mode == "headers_timeout": time.sleep(60); return
    if mode == "redirect":
        self.send_response(302); self.send_header("Location", "https://example.invalid/must-not-follow"); self.send_header("Content-Length", "0"); self.end_headers(); return
    body=b'<div id="workbench-shell"></div><script src="app.js"></script>'
    if mode == "invalid_html": body=b'<html><body>Another local page</body></html>'
    if mode == "oversized": body += b" " * 131073
    if mode == "body_timeout":
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", "4096")
        self.send_header("Set-Cookie", f"{self.server.session_cookie_name}={self.server.session_token}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers(); self.wfile.write(body); self.wfile.flush(); time.sleep(60); return
    self._send(200,body,"application/json" if mode == "wrong_type" else "text/html; charset=utf-8",cookie=True)
gui.Handler.do_GET=get
s=gui.WorkbenchServer(("127.0.0.1",int(sys.argv[2])),c)
print(s.server_port,flush=True)
try: s.serve_forever()
except KeyboardInterrupt: pass
finally: s.server_close(); c.close()`;
let browser,fixture,extraFixture,passed=0;
const command='python parse.py --recorded-only  ';
const error='\ufeffTraceback (most recent call last):\r\n  File "parse.py", line 2, in parse_count\r\n    return int(value)\r\nValueError: synthetic failed run\r\n';
async function stop(server){if(server&&server.exitCode===null){const finished=once(server,'exit');server.kill('SIGINT');await finished;}}
async function scenario(label,run,{clock=false}={}){
  let server,url;
  const context=await browser.newContext({reducedMotion:'reduce'}),page=await context.newPage();
  page.setDefaultTimeout(10000);
  const posts=[],roots=[],external=[],errors=[],releases=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',request=>{
    const target=new URL(request.url());
    if(target.protocol.startsWith('http')&&url&&target.origin!==new URL(url).origin)external.push(request.url());
    if(request.method()==='POST')posts.push(target.pathname);
    if(target.pathname==='/'&&request.method()==='GET')roots.push(request.url());
  });
  const h={page,context,posts,roots,releases,
    async start({mode='normal',version='',additional={}}={}){
      const port=url?new URL(url).port:0;
      server=spawn(process.argv[2]||'python3',['-u','-c',python,fixture,String(port),mode,version,JSON.stringify(additional)],{env,stdio:['ignore','pipe','inherit']});
      url=await waitForServer(server);return url;
    },
    async restart(options){await stop(server);await h.start(options);},
    async disconnected(){await page.evaluate(()=>window.sbWorkbench.syncSession(false));await page.waitForFunction(()=>!document.querySelector('#retry-connection').hidden);},
    async retry(){await page.locator('#retry-connection').click();await page.waitForFunction(()=>document.querySelector('#connection-status').textContent==='Connected locally');assert.equal(await page.locator('#session-notice').isVisible(),true);},
    async cookie(){return (await context.cookies(url)).find(cookie=>cookie.name===`sb_session_${new URL(url).port}`)?.value;}
  };
  try{
    await h.start();if(clock)await page.clock.install();
    await page.goto(url);await page.waitForFunction(()=>window.sbWorkbench?.getState()?.native?.csrf_token);
    await run(h);
    assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
    assert.equal(posts.some(value=>['/api/inventory','/api/model-check'].includes(value)),false);
    passed++;console.log('PASS '+label);
  }finally{
    releases.forEach(release=>release());
    await context.unrouteAll({behavior:'wait'});await context.close();await stop(server);
  }
}
async function prepare(page,request,project='fixture'){
  await page.locator('#choose-source-brief').click();await page.locator('#project').selectOption(project);
  await page.locator('#request').fill(request);await page.locator('#prepare').click();
  await page.waitForFunction(text=>document.querySelector('#original-request').textContent===text,request);
  await page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
}
async function load(page,{project='fixture',directory='./services/api'}={}){
  await page.locator('#choose-failed-run').click();await page.locator('#failure-project').selectOption(project);
  await page.locator('#failure-file').setInputFiles({name:'exact-original.log',mimeType:'text/plain',buffer:Buffer.from(error)});
  await page.waitForFunction(()=>document.querySelector('#failure-file-status').textContent.startsWith('Loaded'));
  if(!await page.locator('#failure-run-details').evaluate(element=>element.open))await page.locator('#failure-run-details > summary').click();
  await page.locator('#failure-command').fill(command);await page.locator('#failure-working-directory').fill(directory);
}
async function diagnose(page){await page.locator('#diagnose-run').click();await page.waitForFunction(()=>document.querySelector('#failure-form').getAttribute('aria-busy')==='false');await page.locator('#failure-result').waitFor({state:'visible'});assert.equal(await page.locator('#failure-original').textContent(),error);}
async function exactInputs(page){assert.equal(await page.locator('#failure-output').inputValue(),error.replace(/\r\n/g,'\n'));assert.equal(await page.locator('#failure-command').inputValue(),command);}
async function hold(page,pattern){
  const seen=deferred(),release=deferred();let held=false;
  await page.route(pattern,async route=>{
    if(held){await route.continue();return;}
    held=true;let response=await route.fetch(),value=await response.json();
    // A real synthetic preparation may be RUNNING for the first few milliseconds.
    for(let tries=0;value.state==='RUNNING'&&tries<100;tries++){await new Promise(r=>setTimeout(r,10));response=await route.fetch();value=await response.json();}
    seen.resolve(value);await release.promise;await route.fulfill({status:response.status(),json:value});
  });
  return {seen:seen.promise,release:()=>release.resolve()};
}
(async()=>{
  fixture=await fs.mkdtemp(path.join(os.tmpdir(),'sb-session-recovery-'));
  extraFixture=await fs.mkdtemp(path.join(os.tmpdir(),'sb-session-added-root-'));
  const source='def parse_count(value):\n    return int(value)\n';
  await fs.mkdir(path.join(fixture,'services/api'),{recursive:true});
  await fs.writeFile(path.join(fixture,'services/api/parse.py'),source);
  await fs.writeFile(path.join(fixture,'retry.py'),'RETRY_LIMIT = 3\n');
  await fs.writeFile(path.join(extraFixture,'parse.py'),source);
  browser=await chromium.launch({headless:true,...(process.env.SB_CHROMIUM_EXECUTABLE?{executablePath:process.env.SB_CHROMIUM_EXECUTABLE}:{})});
  console.log('Chromium '+browser.version());
  await scenario('explicit Retry renews a restarted same-port cookie and retains exact inputs and both captures',async h=>{
    const {page}=h;await prepare(page,'Find RETRY_LIMIT for the synthetic source brief.');
    const sourceCapture=await page.locator('#handoff-text').inputValue();
    await page.locator('#request').fill('Preserve this newer unsubmitted source question.');
    await load(page);await diagnose(page);
    const failureCapture=await page.locator('#failure-copy-text').inputValue(),cookie=await h.cookie(),posts=h.posts.length;
    const oldVersion=await page.locator('#version').innerText();
    await h.restart({version:'0.4.0.synthetic-recovery'});await h.disconnected();
    assert.equal(await h.cookie(),cookie);assert.equal(h.roots.length,1);
    await h.retry();assert.notEqual(await h.cookie(),cookie);assert.equal(h.roots.length,2);assert.equal(h.posts.length,posts);
    await exactInputs(page);assert.equal(await page.locator('#failure-working-directory').inputValue(),'./services/api');
    assert.equal(await page.locator('#failure-copy-text').inputValue(),failureCapture);
    assert.equal(await page.locator('#handoff-text').inputValue(),sourceCapture);
    assert.equal(await page.locator('#request').inputValue(),'Preserve this newer unsubmitted source question.');
    assert.match(await page.locator('#session-notice').innerText(),/service version changed.*0\.4\.0\.synthetic-recovery/);
    assert.ok(!(await page.locator('#version').innerText()).includes(oldVersion));
    await diagnose(page);assert.equal(h.posts.length,posts+1);
    await page.getByText('Original error & report',{exact:true}).click();
    const download=page.waitForEvent('download');await page.locator('#download-failure-json').click();
    const record=JSON.parse(await fs.readFile(await (await download).path(),'utf8'));
    assert.equal(record.error_output,error);assert.equal(record.command,command);assert.equal(record.working_directory,'./services/api');
  });
  await scenario('a restarted session revokes UI-only project approvals without losing either workflow text',async h=>{
    const {page}=h;await page.locator('#choose-failed-run').click();await page.locator('#connect-project > summary').click();await page.locator('#project-path').fill(extraFixture);await page.locator('#project-label').fill('Session-only synthetic folder');await page.locator('#connect-project-button').click();
    await page.waitForFunction(()=>document.querySelector('#project-connect-status').textContent.includes('Folder connected'));
    const project=await page.locator('#failure-project').inputValue();await load(page,{project,directory:''});await diagnose(page);
    await page.locator('#choose-source-brief').click();await page.locator('#project').selectOption(project);await page.locator('#request').fill('Preserve this question for the disconnected folder.');await page.locator('#choose-failed-run').click();
    const posts=h.posts.length;await h.restart();await h.disconnected();await h.retry();
    await exactInputs(page);assert.equal(await page.locator('#failure-project').inputValue(),'');assert.equal(await page.locator('#project').inputValue(),'');
    assert.equal(await page.locator('#failure-project option').evaluateAll((options,id)=>options.some(option=>option.value===id),project),false);
    assert.equal(await page.locator('#project option').evaluateAll((options,id)=>options.some(option=>option.value===id),project),false);
    assert.match(await page.locator('#project-help').textContent(),/unavailable/);assert.equal(await page.locator('#request').inputValue(),'Preserve this question for the disconnected folder.');
    assert.equal(await page.locator('#failure-stale').isVisible(),true);assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);assert.equal(h.posts.length,posts);
    await page.locator('#connect-project-button').click();await page.waitForFunction(()=>document.querySelector('#failure-project').value!=='');await diagnose(page);
  });
  await scenario('fresh state clears an expired real task handle and ignores its late old-session completion',async h=>{
    const {page}=h;await prepare(page,'Find RETRY_LIMIT before an old synthetic task.');const captured=await page.locator('#handoff-text').inputValue();
    const held=await hold(page,'**/api/tasks/*');h.releases.push(held.release);
    await page.locator('#request').fill('Find parse_count in a second synthetic preparation.');await page.locator('#prepare').click();const old=await held.seen;assert.equal(old.state,'DONE');
    const posts=h.posts.length;await h.restart();await h.disconnected();await h.retry();await page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
    assert.equal(await page.locator('#handoff-text').inputValue(),captured);assert.equal(await page.locator('#stop').isVisible(),false);assert.equal(h.posts.length,posts);
    assert.match(await page.locator('#session-notice').textContent(),/earlier preparation is no longer in this session/);
    const finished=page.waitForResponse(response=>response.url().includes('/api/tasks/'+old.task_id));held.release();await finished;
    await page.waitForFunction(()=>!document.querySelector('#prepare').disabled);assert.equal(await page.locator('#handoff-text').inputValue(),captured);
  });
  await scenario('a repeat check crossing a real restart preserves the earlier exact report without replay',async h=>{
    const {page}=h;await load(page);await diagnose(page);
    await page.getByText('Original error & report',{exact:true}).click();
    const save=async()=>{
      const pending=page.waitForEvent('download');await page.locator('#download-failure-json').click();
      return fs.readFile(await (await pending).path(),'utf8');
    };
    const original=await save();
    const capture=JSON.parse(original);
    assert.equal(capture.error_output,error);assert.equal(capture.command,command);assert.ok(capture.evidence.length);
    const changedCommand=command+'--new-check';await page.locator('#failure-command').fill(changedCommand);
    const held=await hold(page,'**/api/troubleshoot');h.releases.push(held.release);
    await page.locator('#diagnose-run').click();const newer=await held.seen;assert.equal(newer.command,changedCommand);
    assert.equal(await page.locator('#failure-result').isVisible(),true);
    assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
    assert.equal(await save(),original);
    const posts=h.posts.length;await h.restart();await h.disconnected();await h.retry();
    const finished=page.waitForResponse(response=>response.url().endsWith('/api/troubleshoot'));held.release();await finished;
    await page.waitForFunction(()=>document.querySelector('#failure-form').getAttribute('aria-busy')==='false');
    assert.equal(await page.locator('#failure-output').inputValue(),error.replace(/\r\n/g,'\n'));
    assert.equal(await page.locator('#failure-command').inputValue(),changedCommand);
    assert.equal(await page.locator('#failure-working-directory').inputValue(),'./services/api');
    assert.equal(await page.locator('#failure-original').textContent(),error);
    assert.match(await page.locator('#failure-stale').innerText(),/earlier|previous/i);
    assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
    assert.equal(await save(),original);assert.equal(h.posts.length,posts);
  });
  for(const crossTab of [false,true])await scenario(`${crossTab?'another tab renewing the shared cookie':'explicit session renewal'} rejects a late old-session failed-run response`,async h=>{
    const {page}=h;await load(page);const held=await hold(page,'**/api/troubleshoot');h.releases.push(held.release);
    await page.locator('#diagnose-run').click();await held.seen;const cookie=await h.cookie();await h.restart();
    if(crossTab){const other=await h.context.newPage();await other.goto(page.url());await page.evaluate(()=>window.sbWorkbench.syncSession(false));await other.close();assert.notEqual(await h.cookie(),cookie);assert.equal(h.roots.length,1);}
    else{await h.disconnected();await h.retry();}
    const finished=page.waitForResponse(response=>response.url().endsWith('/api/troubleshoot'));held.release();await finished;
    await page.waitForFunction(()=>document.querySelector('#failure-progress').textContent.includes('session changed'));
    assert.equal(await page.locator('#failure-result').isVisible(),false);await exactInputs(page);assert.equal(h.posts.length,1);
    await diagnose(page);assert.equal(h.posts.length,2);
  });
  await scenario('a late folder-connection acknowledgement cannot select a different new-session root',async h=>{
    const {page}=h;await page.locator('#choose-failed-run').click();const held=await hold(page,'**/api/projects');h.releases.push(held.release);
    await page.locator('#connect-project > summary').click();await page.locator('#project-path').fill(extraFixture);await page.locator('#project-label').fill('Delayed synthetic folder');await page.locator('#connect-project-button').click();
    const acknowledgement=await held.seen;const id=acknowledgement.project_id||acknowledgement.id;assert.ok(id);
    await h.restart({additional:{[id]:fixture}});await h.disconnected();await h.retry();
    const finished=page.waitForResponse(response=>response.url().endsWith('/api/projects'));held.release();await finished;
    await page.waitForFunction(()=>document.querySelector('#project-connect-status').textContent.includes('session changed'));
    assert.equal(await page.locator('#failure-project').inputValue(),'fixture');assert.equal(await page.locator('#project-path').inputValue(),extraFixture);assert.equal(await page.locator('#project-label').inputValue(),'Delayed synthetic folder');assert.equal(h.posts.length,1);
  });
  for(const mode of ['wrong_type','invalid_html','oversized','redirect','headers_timeout','body_timeout'])await scenario(`failed ${mode.replaceAll('_',' ')} session renewal retains input and requires an explicit successful Retry`,async h=>{
    const {page}=h;await load(page);await diagnose(page);const capture=await page.locator('#failure-copy-text').inputValue();
    await h.restart({mode});await h.disconnected();
    const rootRequest=page.waitForRequest(request=>new URL(request.url()).pathname==='/'&&request.method()==='GET');
    const headers=mode==='body_timeout'?page.waitForResponse(response=>new URL(response.url()).pathname==='/'):null;
    await page.locator('#retry-connection').click();await rootRequest;if(headers)await headers;
    if(mode.endsWith('timeout'))await page.clock.fastForward(16000);
    await page.waitForFunction(()=>!document.querySelector('#retry-connection').disabled);
    assert.match(await page.locator('#session-notice').textContent(),mode.endsWith('timeout')?/renewal timed out/:/could not be verified/);
    assert.match(await page.locator('#connection-status').textContent(),/unavailable/);assert.equal(await page.locator('#session-notice').isVisible(),true);await exactInputs(page);assert.equal(await page.locator('#failure-copy-text').inputValue(),capture);
    const roots=h.roots.length;await page.clock.fastForward(3500);assert.equal(h.roots.length,roots);assert.match(await page.locator('#connection-status').textContent(),/unavailable/);
    await h.restart();await h.retry();await exactInputs(page);await diagnose(page);
  },{clock:true});
  console.log(`${passed} isolated session-recovery browser scenarios passed; no user preview, model or personal clipboard was used.`);
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{await browser?.close();if(fixture)await fs.rm(fixture,{recursive:true,force:true});if(extraFixture)await fs.rm(extraFixture,{recursive:true,force:true});});
