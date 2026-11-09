// Real DOM and HTTP against disposable synthetic source. No user project, model or failing command runs.
const assert = require('node:assert/strict');
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs/promises');
const {spawn} = require('node:child_process');
const {waitForServer} = require('./browser_server.cjs');
const {chromium} = require('playwright');
let browser, server, baseURL, fixture, passed = 0;
const source = '"""Synthetic failed-run source. Never imported by this test."""\n\ndef parse_count(value):\n    return int(value)\n';
const output = (statement='return int(value)',filename=path.join(fixture,'parse.py')) =>
  `Traceback (most recent call last):\n  File "${filename}", line 4, in parse_count\n    ${statement}\nValueError: invalid literal for int() with base 10: 'many'\n`;
async function scenario(label, run, setup) {
  const context = await browser.newContext({reducedMotion:'reduce'}), page = await context.newPage();
  page.setDefaultTimeout(10000);
  const errors = [], requests = [], external = [];
  page.on('pageerror',error => errors.push(error.message));
  page.on('request',request => {
    const url = new URL(request.url());
    if (url.pathname.startsWith('/api/')) requests.push(url.pathname);
    if (['http:','https:'].includes(url.protocol) && url.origin !== new URL(baseURL).origin) external.push(request.url());
  });
  try {
    if (setup) await setup(page,context);
    await page.goto(baseURL);
    await page.waitForFunction(() => window.sbWorkbench?.getState()?.native?.csrf_token);
    await run(page, {requests,external});
    assert.deepEqual(errors, []);
    assert.deepEqual(external, []);
    assert.equal(requests.some(url => ['/api/tasks','/api/inventory','/api/model-check'].includes(url)), false);
    passed++;
    console.log('PASS '+label);
  } finally {
    await context.unrouteAll({behavior:'wait'});
    await context.close();
  }
}
async function diagnose(page, error=output()) {
  await page.locator('#failure-output').fill(error);
  await page.locator('#diagnose-run').click();
  await page.locator('#failure-result').waitFor({state:'visible'});
}
(async () => {
  fixture = await fs.mkdtemp(path.join(os.tmpdir(),'sb-failed-run-browser-'));
  await fs.writeFile(path.join(fixture,'parse.py'),source);
  await fs.writeFile(path.join(fixture,'unicode.py'),'def parse_count(value):\n    marker = \"first\u2028second\"\n    return int(value)\n');
  await fs.writeFile(path.join(fixture,'worker.js'),'function parseCount(value) {\n  throw new TypeError("synthetic failure");\n}\nparseCount(null);\n');
  await fs.writeFile(path.join(fixture,'unicode.js'),'const first = 1;\u2028const second = 2;\u2029throw new Error("synthetic separators");\n');
  await fs.writeFile(path.join(fixture,'settings.ts'),'const port: number = "wrong";\nexport {port};\n');
  const env = {...process.env};
  if (process.argv[2]) delete env.PYTHONPATH; else env.PYTHONPATH = path.join(__dirname,'../src');
  server = spawn(process.argv[2] || 'python3', ['-u','-c',
    'from shake_bake.gui import Controller, DEMO, WorkbenchServer\nc=Controller({"starter-demo":DEMO})\nc.call("settings", {"enabled":False})\ns=WorkbenchServer(("127.0.0.1",0),c)\nprint(s.server_port,flush=True)\ntry: s.serve_forever()\nexcept KeyboardInterrupt: pass\nfinally: s.server_close(); c.close()'], {env,stdio:['ignore','pipe','inherit']});
  baseURL = await waitForServer(server);
  browser = await chromium.launch({headless:true,...(process.env.SB_CHROMIUM_EXECUTABLE?{executablePath:process.env.SB_CHROMIUM_EXECUTABLE}:{})});
  console.log('Chromium '+browser.version());
  await scenario('first visit asks for a real failed run and does not silently use the demo', async page => {
    assert.equal(await page.locator('#failed-run-workflow').isVisible(),true);
    assert.equal(await page.locator('#source-brief-workflow').isVisible(),false);
    assert.equal(await page.locator('#choose-failed-run').getAttribute('aria-pressed'),'true');
    assert.equal(await page.locator('#failure-output').inputValue(),'');
    assert.equal(await page.locator('#failure-command').inputValue(),'');
    assert.equal(await page.locator('#failure-project').inputValue(),'');
    assert.equal(await page.locator('#diagnose-run').isDisabled(),true);
    await page.locator('#failure-project').selectOption('starter-demo');
    assert.equal(await page.locator('#diagnose-run').isDisabled(),true);
    assert.match(await page.locator('#failure-project-help').innerText(),/example/i);
  });
  await scenario('connecting a project preserves the pasted error and the existing source-brief draft', async page => {
    await page.locator('#choose-source-brief').click();
    await page.locator('#request').fill('Preserve this separate source-brief draft.');
    await page.locator('#choose-failed-run').click();
    await page.locator('#failure-output').fill(output());
    await page.locator('#connect-project > summary').click();
    await page.locator('#project-label').fill('Synthetic failure fixture');
    await page.locator('#project-path').fill(fixture);
    await page.locator('#connect-project-button').click();
    await page.waitForFunction(() => document.querySelector('#project-connect-status').textContent.includes('Folder connected'));
    assert.equal(await page.locator('#failure-output').inputValue(),output());
    assert.notEqual(await page.locator('#failure-project').inputValue(),'starter-demo');
    assert.notEqual(await page.locator('#failure-project').inputValue(),'');
    assert.match(await page.locator('#failure-project-help').innerText(),new RegExp(fixture));
    assert.equal(await page.locator('#diagnose-run').isEnabled(),true);
    await page.locator('#choose-source-brief').click();
    assert.equal(await page.locator('#request').inputValue(),'Preserve this separate source-brief draft.');
    await page.locator('#choose-failed-run').click();
    assert.equal(await page.locator('#failure-output').inputValue(),output());
    const storage = await page.evaluate(() => Object.fromEntries(Object.entries(localStorage)));
    assert.equal(Object.values(storage).some(value => value.includes('ValueError: invalid literal')),false);
  });
  await scenario('a real Python traceback locates exact current source without claiming a fix', async page => {
    const error = output();
    await diagnose(page,error);
    assert.match(await page.locator('#failure-result-title').innerText(),/Source located/);
    assert.match(await page.locator('#failure-result-context').innerText(),/parse.py:4.*matches/);
    assert.equal(await page.locator('#failure-source .is-failure').textContent(),'4    return int(value)');
    assert.match(await page.locator('#failure-source .hash').innerText(),/File SHA-256: [a-f0-9]{64}/);
    assert.equal(await page.locator('#failure-original').textContent(),error);
    assert.match(await page.locator('#failure-limits').innerText(),/does not prove the cause/);
    assert.doesNotMatch(await page.locator('#failure-result-title').innerText(),/fixed|ready|root cause/i);
    assert.equal(await page.locator('#failure-result-title').evaluate(el => el === document.activeElement),true);
    assert.match(await page.locator('#failure-captured-project').innerText(),/Synthetic failure fixture/);
    assert.match(await page.locator('#failure-captured-project').innerText(),new RegExp(fixture));
    assert.equal(await page.locator('#failure-format').innerText(),'Python source check');
  });
  await scenario('Unicode within a Python string stays on the same physical source row', async page => {
    const error = output('return int(value)',path.join(fixture,'unicode.py')).replace('line 4,','line 3,');
    await diagnose(page,error);
    assert.match(await page.locator('#failure-result-title').innerText(),/Source located/);
    assert.equal(await page.locator('#failure-source .is-failure .line-number').innerText(),'3');
    assert.equal(await page.locator('#failure-source .line').count(),3);
    assert.match(await page.locator('#failure-source .line').nth(1).textContent(),/first\u2028second/);
  });
  await scenario('zero matching source gives an explicit incomplete result', async page => {
    await diagnose(page,output('return int(value)',path.join(fixture,'missing.py')));
    assert.equal(await page.locator('#failure-result-title').innerText(),'No source located');
    assert.equal(await page.locator('#failure-source').innerText(),'');
    assert.match(await page.locator('#failure-progress').innerText(),/No source line was located/);
    assert.match(await page.locator('#failure-result-context').innerText(),/No diagnosis or fix is established/);
  });
  await scenario('unsupported log text is not turned into an invented diagnosis', async page => {
    await diagnose(page,'The job failed. Connection unavailable.\n');
    assert.equal(await page.locator('#failure-result-title').innerText(),'No source located');
    assert.equal(await page.locator('#failure-source').innerText(),'');
    assert.match(await page.locator('#failure-exception').innerText(),/No complete exception or compiler diagnostic/);
  });
  await scenario('earlier chained evidence is not presented as the location of the final failure', async page => {
    const error = output() + '\nDuring handling of the above exception, another exception occurred:\n\nTraceback (most recent call last):\n  File "/outside-approved-project/handler.py", line 7, in handle\n    raise RuntimeError("synthetic handler")\nRuntimeError: synthetic handler\n';
    await diagnose(page,error);
    assert.equal(await page.locator('#failure-result-title').innerText(),'Other source captured — final failure still unlocated');
    assert.match(await page.locator('#failure-progress').innerText(),/final failure has no located project line/);
    assert.equal(await page.locator('#failure-source').innerText(),'');
    const brief = await page.locator('#failure-copy-text').inputValue();
    assert.match(brief,/Only earlier source was captured/);
    assert.match(brief,/outside-approved-project/);
  });
  await scenario('changed source statement is called out before drawing conclusions', async page => {
    await diagnose(page,output('return int(value) + 1'));
    assert.match(await page.locator('#failure-result-title').innerText(),/pasted statement differs/);
    assert.match(await page.locator('#failure-result-context').innerText(),/different versions/);
    assert.match(await page.locator('#failure-source .is-failure').innerText(),/return int\(value\)/);
  });
  await scenario('Node.js stack locations include line and column without fetching external frames', async page => {
    const error = `TypeError: synthetic failure\n    at parseCount (${path.join(fixture,'worker.js')}:2:9)\n    at https://example.invalid/untrusted.js:7:1\n    at node:internal/main/run_main_module:28:49\n`;
    await diagnose(page,error);
    assert.match(await page.locator('#failure-result-title').innerText(),/Source located/);
    assert.match(await page.locator('#failure-result-context').innerText(),/worker.js:2:9/);
    assert.equal(await page.locator('#failure-format').innerText(),'Node.js source check');
    assert.equal(await page.locator('#failure-source .is-failure .line-number').innerText(),'2');
    await page.locator('#failure-frames > summary').click();
    assert.match(await page.locator('#failure-frame-list').innerText(),/example.invalid/);
    assert.match(await page.locator('#failure-frame-list').innerText(),/node:internal/);
    assert.equal(await page.locator('#failure-original').textContent(),error);
  });
  await scenario('JavaScript Unicode separators retain the parser line numbering in the source viewer', async page => {
    await diagnose(page,`Error: synthetic separators\n    at ${path.join(fixture,'unicode.js')}:3:7\n`);
    assert.equal(await page.locator('#failure-source .line').count(),3);
    assert.equal(await page.locator('#failure-source .is-failure').textContent(),'3throw new Error("synthetic separators");');
  });
  await scenario('TypeScript compiler diagnostics locate exact current source without claiming a fix', async page => {
    const error = "settings.ts(1,7): error TS2322: Type 'string' is not assignable to type 'number'.\n";
    await diagnose(page,error);
    assert.match(await page.locator('#failure-result-title').innerText(),/Source located/);
    assert.match(await page.locator('#failure-result-context').innerText(),/settings.ts:1:7/);
    assert.equal(await page.locator('#failure-format').innerText(),'TypeScript source check');
    assert.match(await page.locator('#failure-exception').innerText(),/TS2322/);
    assert.equal(await page.locator('#failure-source .is-failure').textContent(),'1const port: number = "wrong";');
    assert.equal(await page.locator('#failure-original').textContent(),error);
  });
  await scenario('recorded command and exception text remain inert and export exact original output', async page => {
    const sentinel = path.join(fixture,'COMMAND-MUST-NOT-RUN');
    const command = `touch ${sentinel}`;
    const error = output().replace("invalid literal for int() with base 10: 'many'",'<img src=x onerror=alert(1)>');
    await page.locator('#failure-command').fill(command);
    await diagnose(page,error);
    assert.match(await page.locator('#failure-exception').textContent(),/<img/);
    assert.equal(await page.locator('#failure-result img').count(),0);
    assert.equal(await fs.stat(sentinel).then(()=>true,()=>false),false);
    await page.getByText('Original error & report',{exact:true}).click();
    const downloading = page.waitForEvent('download');
    await page.locator('#download-failure-json').click();
    const download = await downloading;
    const record = JSON.parse(await fs.readFile(await download.path(),'utf8'));
    assert.equal(record.error_output,error);
    assert.equal(record.command,command);
    assert.equal(record.kind,'failure_source_report');
    assert.equal(record.project.path,fixture);
    const storage = await page.evaluate(() => Object.fromEntries(Object.entries(localStorage)));
    assert.equal(Object.values(storage).some(value => value.includes(command) || value.includes('<img')),false);
  });
  for (const changed of ['error', 'command', 'project']) {
    await scenario(`editing the ${changed} marks the captured report outdated and disables handoff and exports`, async page => {
      await diagnose(page);
      const captured = await page.locator('#failure-captured-project').innerText();
      if (changed === 'error') await page.locator('#failure-output').fill(output('return 99'));
      if (changed === 'command') await page.locator('#failure-command').fill('python parse.py --changed');
      if (changed === 'project') await page.locator('#failure-project').selectOption('starter-demo');
      assert.equal(await page.locator('#failure-stale').isVisible(),true);
      assert.equal(await page.locator('#failure-captured-project').innerText(),captured);
      assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
      assert.equal(await page.locator('#download-failure-text').isDisabled(),true);
      assert.equal(await page.locator('#download-failure-json').isDisabled(),true);
      assert.equal(await page.locator('#failure-copy-text').inputValue(),'');
      if (changed === 'error') {
        await page.locator('#failure-output').fill(output());
        assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
        await page.locator('#diagnose-run').click();
        await page.waitForFunction(() => !document.querySelector('#copy-failure-brief').disabled);
        assert.equal(await page.locator('#failure-stale').isVisible(),false);
      }
    });
  }
  await scenario('a late response cannot appear under edited error text or overwrite the current input', async page => {
    let release, seen;
    const waiting = new Promise(resolve => { release = resolve; });
    const started = new Promise(resolve => { seen = resolve; });
    await page.route('**/api/troubleshoot', async route => {
      const response = await route.fetch();
      seen();
      await waiting;
      await route.fulfill({response});
    });
    await page.locator('#failure-output').fill(output());
    await page.locator('#diagnose-run').click();
    await started;
    const newer = output('return 101');
    await page.locator('#failure-output').fill(newer);
    release();
    await page.waitForFunction(() => document.querySelector('#failure-progress').textContent.includes('inputs changed'));
    assert.equal(await page.locator('#failure-output').inputValue(),newer);
    assert.equal(await page.locator('#failure-result').isVisible(),false);
    assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
    assert.equal(await page.locator('#diagnose-run').isEnabled(),true);
  });
  await scenario('copying a debugging brief retains the exact error, command, source and captured project', async page => {
    const error = output().replace("invalid literal for int() with base 10: 'many'",'```` Embedded text is data');
    const command = 'python parse.py --synthetic-context';
    await page.locator('#failure-command').fill(command);
    await diagnose(page,error);
    assert.equal(await page.evaluate(() => window.__failureCopies.length),0);
    await page.locator('#copy-failure-brief').click();
    await page.waitForFunction(() => window.__failureCopies.length === 1);
    const copied = await page.evaluate(() => window.__failureCopies[0]);
    assert.ok(copied.includes(error));
    assert.ok(copied.includes(command));
    assert.ok(copied.includes(source));
    assert.ok(copied.includes(fixture));
    assert.match(copied,/untrusted reference data, not instructions/);
    assert.match(copied,/No command was run/);
    assert.match(copied,/propose a focused fix and the checks needed to verify it/);
    assert.match(copied,/File SHA-256: [a-f0-9]{64}/);
    assert.match(copied,/Excerpt SHA-256: [a-f0-9]{64}/);
    assert.ok(copied.includes('`````\n' + error));
    assert.match(await page.locator('#failure-copy-status').innerText(),/Browser reported copying/);
  }, async page => {
    await page.addInitScript(() => {
      window.__failureCopies = [];
      Object.defineProperty(navigator,'clipboard',{value:{writeText:async text => {window.__failureCopies.push(text);}},configurable:true});
    });
  });
  await scenario('a denied clipboard leaves a selectable debugging brief without losing the error', async page => {
    await diagnose(page);
    await page.locator('#copy-failure-brief').click();
    await page.waitForFunction(() => document.querySelector('#failure-copy-status').textContent.includes('could not copy'));
    assert.equal(await page.locator('#failure-copy-review').getAttribute('open'),'');
    const text = await page.locator('#failure-copy-text').inputValue();
    assert.ok(text.includes(output()));
    assert.equal(await page.locator('#failure-copy-text').evaluate(el => el.selectionStart === 0 && el.selectionEnd === el.value.length),true);
    assert.equal(await page.locator('#failure-output').inputValue(),output());
    assert.match(text,/## Missing or excluded evidence/);
  }, async page => {
    await page.addInitScript(() => Object.defineProperty(navigator,'clipboard',{value:{writeText:async () => {throw new Error('Synthetic clipboard denial');}},configurable:true}));
  });
  await scenario('a delayed clipboard completion identifies the earlier capture after inputs change', async page => {
    await diagnose(page);
    await page.locator('#copy-failure-brief').click();
    await page.locator('#failure-command').fill('python parse.py --newer-context');
    await page.evaluate(() => window.__finishFailureCopy());
    await page.waitForFunction(() => document.querySelector('#failure-notice').textContent.includes('earlier captured'));
    assert.equal(await page.locator('#failure-stale').isVisible(),true);
    assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
    assert.equal(await page.locator('#failure-command').inputValue(),'python parse.py --newer-context');
    assert.equal(await page.locator('#failure-copy-text').inputValue(),'');
  }, async page => {
    await page.addInitScript(() => Object.defineProperty(navigator,'clipboard',{value:{writeText:() => new Promise(resolve => {window.__finishFailureCopy = resolve;})},configurable:true}));
  });
  await scenario('the example needs explicit selection and cannot overwrite a real pasted error', async page => {
    const error = output();
    await page.locator('#failure-output').fill(error);
    await page.locator('#try-failure-example').click();
    assert.equal(await page.locator('#failure-output').inputValue(),error);
    assert.match(await page.locator('#failure-notice').innerText(),/unchanged/);
    await page.locator('#failure-output').fill('');
    await page.locator('#try-failure-example').click();
    assert.equal(await page.locator('#failure-example-notice').isVisible(),true);
    assert.equal(await page.locator('#failure-project').inputValue(),'starter-demo');
    await page.locator('#diagnose-run').click();
    await page.locator('#failure-result').waitFor({state:'visible'});
    assert.match(await page.locator('#failure-result-status').innerText(),/Synthetic example/i);
    assert.match(await page.locator('#failure-result-title').innerText(),/Source located/);
    await page.locator('#failure-output').fill(error);
    assert.equal(await page.locator('#diagnose-run').isDisabled(),true);
    assert.equal(await page.locator('#failure-example-notice').isVisible(),false);
  });
  await scenario('oversized UTF-8 input is kept intact and rejected before making a request', async (page,{requests}) => {
    const error = 'é'.repeat(32769);
    await page.locator('#failure-output').fill(error);
    await page.locator('#diagnose-run').click();
    assert.match(await page.locator('#failure-notice').innerText(),/64 KiB/);
    assert.equal(await page.locator('#failure-output').inputValue(),error);
    assert.equal(requests.includes('/api/troubleshoot'),false);
    assert.equal(await page.locator('#failure-result').isVisible(),false);
  });
  await scenario('a failed service request keeps pasted output and avoids a success report', async page => {
    await page.route('**/api/troubleshoot',route => route.fulfill({status:503,json:{error:'synthetic_unavailable'}}));
    await page.locator('#failure-output').fill(output());
    await page.locator('#diagnose-run').click();
    await page.locator('#failure-notice').waitFor({state:'visible'});
    assert.equal(await page.locator('#failure-output').inputValue(),output());
    assert.equal(await page.locator('#failure-result').isVisible(),false);
    assert.match(await page.locator('#failure-progress').innerText(),/did not complete/);
    assert.equal(await page.locator('#diagnose-run').isEnabled(),true);
  });
  await scenario('small-screen error review fits without horizontal page scrolling', async page => {
    await page.setViewportSize({width:390,height:844});
    await diagnose(page);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),true);
    assert.equal(await page.locator('#failure-source .is-failure').isVisible(),true);
    await page.locator('#choose-source-brief').click();
    assert.equal(await page.locator('#request').isVisible(),true);
    await page.locator('#choose-failed-run').click();
    assert.equal(await page.locator('#failure-result').isVisible(),true);
  });
  console.log(`${passed} failed-run browser scenarios passed.`);
})().catch(error => {console.error(error);process.exitCode=1;}).finally(async () => {
  if (browser) await browser.close();
  if (server) server.kill('SIGTERM');
  if (fixture) await fs.rm(fixture,{recursive:true,force:true});
});
