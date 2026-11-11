// Real source preparation and DOM/JSON readback using only disposable synthetic files.
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const fs=require('node:fs/promises');
const path=require('node:path');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
const {waitForServer}=require('./browser_server.cjs');
const env={...process.env};
if(process.argv[2])delete env.PYTHONPATH;else env.PYTHONPATH=path.join(__dirname,'../src');
const exact="def needle_marker():\r\n    return 'λ'\r\n";
const original='# padding '+'x'.repeat(20000)+'\r\n'+exact;
const notice='Some excerpts were shortened to fit the source-byte limit. Only whole source lines are included; ask for surrounding lines if needed.';
const server=spawn(process.argv[2]||process.env.SB_PYTHON||'python3',['-u','-c',[
  'import tempfile',
  'from pathlib import Path',
  'from shake_bake.gui import Controller, WorkbenchServer',
  'temporary=tempfile.TemporaryDirectory(prefix="sb-excerpt-budget-")',
  'base=Path(temporary.name); root=base/"project"; root.mkdir()',
  `(root/"fixture.py").write_bytes(${JSON.stringify(original)}.encode("utf-8"))`,
  'c=Controller({"budget-fixture":root},state_directory=base/"state")',
  'c.call("settings", {"enabled":False})',
  's=WorkbenchServer(("127.0.0.1",0),c)',
  'print(s.server_port,flush=True)',
  'try: s.serve_forever()',
  'except KeyboardInterrupt: pass',
  'finally: s.server_close(); c.close(); temporary.cleanup()',
].join('\n')],{env,stdio:['ignore','pipe','inherit']});
let browser;
(async()=>{
  const baseURL=await waitForServer(server);
  browser=await chromium.launch({headless:true,...(process.env.SB_CHROMIUM_EXECUTABLE?{executablePath:process.env.SB_CHROMIUM_EXECUTABLE}:{})});
  const context=await browser.newContext({reducedMotion:'reduce'}),page=await context.newPage();
  page.setDefaultTimeout(10000);
  const errors=[],external=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{const url=new URL(request.url());if(['http:','https:'].includes(url.protocol)&&url.origin!==new URL(baseURL).origin)external.push(request.url());});
  await page.goto(baseURL);await page.locator('#choose-source-brief').click();
  await page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
  await page.locator('#project').selectOption('budget-fixture');
  await page.locator('#request').fill('Find needle_marker');await page.locator('#prepare').click();
  await page.waitForFunction(()=>document.querySelector('#original-request').textContent==='Find needle_marker');
  await page.waitForFunction(()=>!document.querySelector('#prepare').disabled);
  assert.equal(await page.locator('#collection-warning').isVisible(),true);
  assert.equal(await page.locator('#collection-warning').innerText(),notice);
  await page.locator('#evidence-section > summary').click();
  assert.equal(await page.locator('#evidence .source-meta').innerText(),'Lines 2–3');
  await page.locator('#handoff-copy > summary').click();
  for(const style of ['orientation','evidence']){
    await page.locator('#brief-style').selectOption(style);
    assert.ok((await page.locator('#handoff-text').inputValue()).split('\n').includes(notice));
  }
  const downloading=page.waitForEvent('download');await page.locator('#download').click();
  const download=await downloading,job=JSON.parse(await fs.readFile(await download.path(),'utf8'));
  assert.equal(job.packet.original_request,'Find needle_marker');
  assert.equal(job.packet.evidence.length,1);
  const record=job.packet.evidence[0];
  assert.deepEqual([record.start_line,record.end_line],[2,3]);
  assert.equal(record.content,exact);
  assert.equal(record.file_sha256,crypto.createHash('sha256').update(original).digest('hex'));
  assert.equal(record.excerpt_sha256,crypto.createHash('sha256').update(exact).digest('hex'));
  assert.equal(job.packet.receipt.excerpt_bytes,Buffer.byteLength(exact));
  assert.ok(job.packet.receipt.discovery.cutoffs.includes('excerpt_window_shortened'));
  assert.equal(job.packet.model_notes,null);
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  console.log('PASS real source-byte fitting, visible warning, both handoffs and exact Unicode/CRLF JSON/hash readback; no external requests.');
  await context.close();
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{
  if(browser)await browser.close();
  const stopped=new Promise(resolve=>{if(server.exitCode!==null||server.signalCode!==null)resolve();else server.once('exit',resolve);});
  server.kill('SIGINT');await stopped;
});
