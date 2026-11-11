// Real DOM and HTTP against disposable synthetic source. No user project, model or failing command runs.
const assert = require('node:assert/strict');
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs/promises');
const {createHash} = require('node:crypto');
const {spawn} = require('node:child_process');
const {waitForServer} = require('./browser_server.cjs');
const {chromium} = require('playwright');
let browser, server, baseURL, fixture, sourceFixture, passed = 0;
const connectionFixtures = [];
const source = '"""Synthetic failed-run source. Never imported by this test."""\n\ndef parse_count(value):\n    return int(value)\n';
const nestedSource = '"""Synthetic nested source. Never imported by this test."""\n\ndef parse_count(value):\n    return int(value.strip())\n';
const nestedWorkingDirectory = 'services/api workspace';
const output = (statement='return int(value)',filename=path.join(fixture,'parse.py')) =>
  `Traceback (most recent call last):\n  File "${filename}", line 4, in parse_count\n    ${statement}\nValueError: invalid literal for int() with base 10: 'many'\n`;
const pytestSection = title => ` ${title} `.padStart(Math.floor((79 + title.length + 2) / 2),'=').padEnd(79,'=') + '\n';
const pytestHeading = title => ` ${title} `.padStart(Math.floor((79 + title.length + 2) / 2),'_').padEnd(79,'_') + '\n';
const pytestFailure = (filename=path.join(fixture,'parse.py'), short=false, message='invalid literal for int() with base 10: \'many\'') => short
  ? `${filename}:4: in parse_count\n    return int(value)\nE   ValueError: ${message}\n`
  : `    def parse_count(value):\n>       return int(value)\nE       ValueError: ${message}\n\n${filename}:4: ValueError\n`;
async function scenario(label, run, setup, expectedTaskRequests = 0) {
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
    assert.equal(requests.filter(url => url === '/api/tasks').length,expectedTaskRequests);
    assert.equal(requests.some(url => ['/api/inventory','/api/model-check'].includes(url)), false);
    passed++;
    console.log('PASS '+label);
  } finally {
    await context.unrouteAll({behavior:'wait'});
    await context.close();
  }
}
async function fillRunDetail(page, selector, value) {
  const details = page.locator('#failure-run-details');
  if (!await details.evaluate(node => node.open)) await details.locator('summary').click();
  await page.locator(selector).fill(value);
}
function briefJson(brief, heading) {
  const section = brief.split(`## ${heading}\n`)[1]?.split('\n## ')[0];
  const fenced = section?.match(/(`{3,})\n([\s\S]*?)\n\1/);
  assert.ok(fenced, `Missing structured brief section: ${heading}`);
  return JSON.parse(fenced[2]);
}
async function diagnose(page, error=output()) {
  await page.locator('#failure-output').fill(error);
  await page.locator('#diagnose-run').click();
  await page.locator('#failure-result').waitFor({state:'visible'});
}
(async () => {
  fixture = await fs.mkdtemp(path.join(os.tmpdir(),'sb-failed-run-browser-'));
  sourceFixture = await fs.mkdtemp(path.join(os.tmpdir(),'sb-source-brief-browser-'));
  await fs.writeFile(path.join(sourceFixture,'retry.py'),'RETRY_LIMIT = 3\n');
  await fs.writeFile(path.join(fixture,'parse.py'),source);
  await fs.mkdir(path.join(fixture,nestedWorkingDirectory),{recursive:true});
  await fs.writeFile(path.join(fixture,nestedWorkingDirectory,'parse.py'),nestedSource);
  await fs.writeFile(path.join(fixture,'unicode.py'),'def parse_count(value):\n    marker = \"first\u2028second\"\n    return int(value)\n');
  await fs.writeFile(path.join(fixture,'worker.js'),'function parseCount(value) {\n  throw new TypeError("synthetic failure");\n}\nparseCount(null);\n');
  await fs.writeFile(path.join(fixture,'eof.js'),'function incomplete() {\n');
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
    assert.equal(await page.locator('#failure-working-directory').inputValue(),'');
    assert.equal(await page.locator('#failure-project').inputValue(),'');
    assert.equal(await page.locator('#diagnose-run').isDisabled(),true);
    await page.locator('#failure-project').selectOption('starter-demo');
    assert.equal(await page.locator('#diagnose-run').isDisabled(),true);
    assert.match(await page.locator('#failure-project-help').innerText(),/example/i);
    assert.equal(await page.locator('#failure-run-details').evaluate(node => node.open),false);
    await page.locator('#connect-failure-project').click();
    assert.equal(await page.locator('#connect-project').evaluate(node => node.open),true);
    assert.equal(await page.evaluate(() => document.activeElement.id),'project-path');
    await page.locator('#connect-project > summary').click();
    await page.locator('#choose-source-brief').click();
    await page.locator('#connect-source-project').click();
    assert.equal(await page.locator('#connect-project').evaluate(node => node.open),true);
    assert.equal(await page.evaluate(() => document.activeElement.id),'project-path');
  });
  await scenario('connecting a project preserves the pasted error and the existing source-brief draft', async page => {
    await page.locator('#choose-source-brief').click();
    await page.locator('#request').fill('Preserve this separate source-brief draft.');
    await page.locator('#choose-failed-run').click();
    await page.locator('#failure-output').fill(output());
    await fillRunDetail(page, '#failure-working-directory', nestedWorkingDirectory);
    await page.locator('#connect-project > summary').click();
    await page.locator('#project-label').fill('Synthetic failure fixture');
    await page.locator('#project-path').fill(fixture);
    await page.locator('#connect-project-button').click();
    await page.waitForFunction(() => document.querySelector('#project-connect-status').textContent.includes('Folder connected'));
    assert.equal(await page.locator('#failure-output').inputValue(),output());
    assert.equal(await page.locator('#failure-working-directory').inputValue(),nestedWorkingDirectory);
    assert.notEqual(await page.locator('#failure-project').inputValue(),'starter-demo');
    assert.notEqual(await page.locator('#failure-project').inputValue(),'');
    assert.match(await page.locator('#failure-project-help').innerText(),new RegExp(fixture));
    assert.equal(await page.locator('#diagnose-run').isEnabled(),true);
    await page.locator('#choose-source-brief').click();
    assert.equal(await page.locator('#request').inputValue(),'Preserve this separate source-brief draft.');
    await page.locator('#choose-failed-run').click();
    assert.equal(await page.locator('#failure-output').inputValue(),output());
    assert.equal(await page.locator('#failure-working-directory').inputValue(),nestedWorkingDirectory);
    const storage = await page.evaluate(() => Object.fromEntries(Object.entries(localStorage)));
    assert.equal(Object.values(storage).some(value => value.includes('ValueError: invalid literal')),false);
  });
  await scenario('source-brief folder connection selects only that workflow and keeps readable labels after reload', async page => {
    await page.locator('#failure-project').selectOption('');
    const failureProject = await page.locator('#failure-project').inputValue();
    assert.equal(failureProject,'');
    await page.locator('#failure-output').fill(output());
    await fillRunDetail(page, '#failure-command', 'python parse.py --preserved');
    await fillRunDetail(page, '#failure-working-directory', nestedWorkingDirectory);
    await page.locator('#choose-source-brief').click();
    await page.locator('#request').fill('Where is RETRY_LIMIT defined? Preserve this source question.');
    assert.equal(await page.locator('#connect-project').isVisible(),true);
    await page.locator('#connect-project > summary').click();
    await page.locator('#project-label').fill('Second Synthetic Folder');
    await page.locator('#project-path').fill(sourceFixture);
    await page.locator('#connect-project-button').click();
    await page.waitForFunction(() => document.querySelector('#project-connect-status').textContent.includes('source brief now uses'));
    const sourceProject = await page.locator('#project').inputValue();
    assert.notEqual(sourceProject,'starter-demo');
    assert.notEqual(sourceProject,failureProject);
    assert.equal(await page.locator('#project option:checked').innerText(),'Second Synthetic Folder');
    assert.equal(await page.locator('#request').inputValue(),'Where is RETRY_LIMIT defined? Preserve this source question.');
    await page.locator('#choose-failed-run').click();
    assert.equal(await page.locator('#failure-project').inputValue(),failureProject);
    assert.equal(await page.locator('#failure-output').inputValue(),output());
    assert.equal(await page.locator('#failure-command').inputValue(),'python parse.py --preserved');
    assert.equal(await page.locator('#failure-working-directory').inputValue(),nestedWorkingDirectory);
    await page.reload();
    await page.waitForFunction(() => window.sbWorkbench?.getState()?.native?.csrf_token);
    await page.locator('#choose-source-brief').click();
    assert.equal(await page.locator('#project').inputValue(),sourceProject);
    assert.equal(await page.locator('#project option:checked').innerText(),'Second Synthetic Folder');
    assert.equal(await page.locator('#request').inputValue(),'Where is RETRY_LIMIT defined? Preserve this source question.');
  });
  for (const workflow of ['source','failed']) {
    await scenario(`a delayed ${workflow} folder connection preserves an away-and-back project choice and newer text`, async page => {
      const newRoot = await fs.mkdtemp(path.join(os.tmpdir(),'sb-connect-race-'));
      connectionFixtures.push(newRoot);
      const initialError = output(), newerError = output('return 123');
      const initialQuestion = 'Preserve this question during folder connection.';
      const newerQuestion = 'This newer source question must survive the delayed connection.';
      await page.locator('#failure-output').fill(initialError);
      await page.locator('#choose-source-brief').click();
      await page.locator('#request').fill(initialQuestion);
      if (workflow === 'failed') await page.locator('#choose-failed-run').click();
      const selector = workflow === 'source' ? '#project' : '#failure-project';
      const before = await page.locator(selector).inputValue();
      const alternative = await page.locator(`${selector} option`).evaluateAll((options, selected) => options.find(option => option.value && option.value !== selected && !option.disabled).value,before);
      let release, started;
      const waiting = new Promise(resolve => {release = resolve;});
      const seen = new Promise(resolve => {started = resolve;});
      await page.route('**/api/projects',async route => {
        const response = await route.fetch();
        started();
        await waiting;
        await route.fulfill({response});
      });
      try {
        await page.locator('#connect-project > summary').click();
        await page.locator('#project-label').fill(`Synthetic ${workflow} connection race`);
        await page.locator('#project-path').fill(newRoot);
        await page.locator('#connect-project-button').click();
        await seen;
        await page.locator(selector).selectOption(alternative);
        await page.locator(selector).selectOption(before);
        if (workflow === 'source') await page.locator('#request').fill(newerQuestion);
        else await page.locator('#failure-output').fill(newerError);
        release();
        await page.waitForFunction(() => document.querySelector('#project-connect-status').textContent.includes('newer project selection is unchanged'));
        assert.equal(await page.locator(selector).inputValue(),before);
        const connected = await page.evaluate(root => window.sbWorkbench.getState().native.projects.find(project => project.path === root),newRoot);
        assert.ok(connected);
        assert.notEqual(before,connected.id);
        await page.locator('#choose-source-brief').click();
        assert.equal(await page.locator('#request').inputValue(),workflow === 'source' ? newerQuestion : initialQuestion);
        await page.locator('#choose-failed-run').click();
        assert.equal(await page.locator('#failure-output').inputValue(),workflow === 'failed' ? newerError : initialError);
      } finally {release?.();}
    });
  }
  await scenario('loading a UTF-8 error file preserves BOM and CRLF through the local check and JSON export', async (page,{requests}) => {
    const error = '\ufeff' + output().replace(/\n/g,'\r\n');
    await page.locator('#failure-file').setInputFiles({name:'complete-error.log',mimeType:'text/plain',buffer:Buffer.from(error,'utf8')});
    await page.waitForFunction(() => document.querySelector('#failure-file-status').textContent.startsWith('Loaded complete-error.log'));
    assert.equal(await page.locator('#failure-output').inputValue(),error.replace(/\r\n/g,'\n'));
    await fillRunDetail(page, '#failure-command', 'python parse.py --recorded-only');
    assert.equal(requests.includes('/api/troubleshoot'),false);
    const storage = await page.evaluate(() => Object.fromEntries(Object.entries(localStorage)));
    assert.equal(Object.values(storage).some(value => value.includes('ValueError: invalid literal')),false);
    await page.locator('#diagnose-run').click();
    await page.locator('#failure-result').waitFor({state:'visible'});
    assert.match(await page.locator('#failure-result-title').innerText(),/Source located/);
    assert.equal(await page.locator('#failure-original').textContent(),error);
    await page.getByText('Original error & report',{exact:true}).click();
    const downloading = page.waitForEvent('download');
    await page.locator('#download-failure-json').click();
    const record = JSON.parse(await fs.readFile(await (await downloading).path(),'utf8'));
    assert.equal(record.error_output,error);
    assert.equal(record.error_sha256,createHash('sha256').update(Buffer.from(error,'utf8')).digest('hex'));
    assert.equal(record.command,'python parse.py --recorded-only');
    assert.equal(record.working_directory,'');
    assert.equal(record.working_directory_path,'.');
  });
  await scenario('an explicit working folder selects the nested relative source instead of a same-named root file', async page => {
    const error = output('return int(value.strip())','parse.py');
    await diagnose(page,error);
    assert.match(await page.locator('#failure-result-title').innerText(),/pasted statement differs/);
    assert.match(await page.locator('#failure-source').innerText(),/return int\(value\)/);
    assert.match(await page.locator('#failure-captured-working-directory').innerText(),/connected project folder \(\.\)/);
    await fillRunDetail(page, '#failure-working-directory', './' + nestedWorkingDirectory);
    await page.locator('#diagnose-run').click();
    await page.waitForFunction(() => !document.querySelector('#copy-failure-brief').disabled);
    assert.equal(await page.locator('#failure-stale').isVisible(),false);
    assert.match(await page.locator('#failure-result-title').innerText(),/Source located — check this line/);
    assert.match(await page.locator('#failure-result-context').innerText(),/services\/api workspace\/parse.py:4/);
    assert.match(await page.locator('#failure-source').innerText(),/return int\(value.strip\(\)\)/);
    assert.match(await page.locator('#failure-captured-working-directory').innerText(),/services\/api workspace/);
    assert.ok((await page.locator('#failure-copy-text').inputValue()).includes('"working_directory": "./services/api workspace"'));
  });
  await scenario('working-folder edits preserve a loaded exact error and captured folder in the report and brief', async page => {
    const error = '\ufeff' + output('return int(value.strip())','parse.py').replace(/\n/g,'\r\n');
    const directory = path.join(fixture,nestedWorkingDirectory);
    await page.locator('#failure-file').setInputFiles({name:'nested-run.log',mimeType:'text/plain',buffer:Buffer.from(error,'utf8')});
    await page.waitForFunction(() => document.querySelector('#failure-file-status').textContent.startsWith('Loaded nested-run.log'));
    await fillRunDetail(page, '#failure-working-directory', directory);
    await page.locator('#diagnose-run').click();
    await page.locator('#failure-result').waitFor({state:'visible'});
    assert.equal(await page.locator('#failure-original').textContent(),error);
    assert.match(await page.locator('#failure-result-context').innerText(),/services\/api workspace\/parse.py:4/);
    const captured = await page.locator('#failure-captured-working-directory').innerText();
    assert.ok(captured.includes(directory));
    const brief = await page.locator('#failure-copy-text').inputValue();
    assert.ok(brief.includes(JSON.stringify(directory)));
    assert.ok(brief.includes('"working_directory_path": "services/api workspace"'));
    await page.getByText('Original error & report',{exact:true}).click();
    const downloading = page.waitForEvent('download');
    await page.locator('#download-failure-json').click();
    const record = JSON.parse(await fs.readFile(await (await downloading).path(),'utf8'));
    assert.equal(record.error_output,error);
    assert.equal(record.working_directory,directory);
    assert.equal(record.working_directory_path,nestedWorkingDirectory);
    await fillRunDetail(page, '#failure-working-directory', '');
    assert.equal(await page.locator('#failure-captured-working-directory').innerText(),captured);
    assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
    await page.locator('#diagnose-run').click();
    await page.waitForFunction(() => !document.querySelector('#copy-failure-brief').disabled);
    assert.equal(await page.locator('#failure-original').textContent(),error);
    assert.match(await page.locator('#failure-result-title').innerText(),/pasted statement differs/);
  });
  await scenario('refused working folders explain how to recover and preserve exact inputs', async page => {
    const error = '\ufeff' + output().replace(/\n/g,'\r\n');
    const command = 'python parse.py --keep-this-command';
    await page.locator('#failure-file').setInputFiles({name:'preserved-error.log',mimeType:'text/plain',buffer:Buffer.from(error,'utf8')});
    await page.waitForFunction(() => document.querySelector('#failure-file-status').textContent.startsWith('Loaded preserved-error.log'));
    await fillRunDetail(page, '#failure-command', command);
    for (const [directory,recovery] of [
      [os.tmpdir(),/outside the connected project/],
      ['../',/without parent-folder steps/],
      ['missing-synthetic-folder',/Check that it exists and is a readable folder/]
    ]) {
      await fillRunDetail(page, '#failure-working-directory', directory);
      await page.locator('#failure-run-details > summary').click();
      await page.locator('#diagnose-run').click();
      await page.locator('#failure-notice').waitFor({state:'visible'});
      const message = await page.locator('#failure-notice').innerText();
      assert.match(message,recovery);
      assert.match(message,/clear the field to use the connected project folder/);
      assert.doesNotMatch(message,/working_directory_|invalid_failure_/);
      assert.equal(await page.locator('#failure-working-directory').inputValue(),directory);
      assert.equal(await page.locator('#failure-command').inputValue(),command);
      assert.equal(await page.locator('#failure-output').inputValue(),error.replace(/\r\n/g,'\n'));
      assert.equal(await page.evaluate(() => document.activeElement.id),'failure-working-directory');
      assert.equal(await page.locator('#failure-run-details').evaluate(node => node.open),true);
      assert.equal(await page.locator('#failure-result').isVisible(),false);
    }
    await fillRunDetail(page, '#failure-working-directory', '');
    await page.locator('#diagnose-run').click();
    await page.locator('#failure-result').waitFor({state:'visible'});
    assert.match(await page.locator('#failure-result-title').innerText(),/Source located — check this line/);
    assert.equal(await page.locator('#failure-original').textContent(),error);
    assert.equal(await page.locator('#failure-command').inputValue(),command);
    assert.equal(await page.locator('#failure-notice').isVisible(),false);
  });
  await scenario('editing a loaded error replaces its preserved file copy with the edited text', async page => {
    const loaded = output().replace(/\n/g,'\r\n');
    await page.locator('#failure-file').setInputFiles({name:'edit-me.log',mimeType:'text/plain',buffer:Buffer.from(loaded,'utf8')});
    await page.waitForFunction(() => document.querySelector('#failure-file-status').textContent.startsWith('Loaded edit-me.log'));
    const edited = output('return 77');
    await page.locator('#failure-output').fill(edited);
    assert.equal(await page.locator('#failure-file-status').textContent(),'');
    await page.locator('#diagnose-run').click();
    await page.locator('#failure-result').waitFor({state:'visible'});
    assert.equal(await page.locator('#failure-original').textContent(),edited);
    assert.match(await page.locator('#failure-result-title').innerText(),/pasted statement differs/);
  });
  await scenario('oversized, invalid UTF-8, NUL and unreadable files preserve the current exact error', async (page,{requests}) => {
    const error = output().replace(/\n/g,'\r\n');
    await page.locator('#failure-file').setInputFiles({name:'keep.log',mimeType:'text/plain',buffer:Buffer.from(error,'utf8')});
    await page.waitForFunction(() => document.querySelector('#failure-file-status').textContent.startsWith('Loaded keep.log'));
    for (const [name,buffer,message] of [
      ['large.log',Buffer.alloc(65537,65),/larger than 64 KiB/],
      ['invalid.log',Buffer.from([0xc3,0x28]),/valid UTF-8/],
      ['binary.log',Buffer.from('not\0a text log'),/NUL bytes/],
      ['unreadable.log',Buffer.from('unused'),/could not be read/]
    ]) {
      await page.locator('#failure-file').setInputFiles({name,mimeType:'text/plain',buffer});
      await page.waitForFunction(() => document.querySelector('#failure-file-status').textContent.includes('current error is unchanged'));
      assert.match(await page.locator('#failure-file-status').textContent(),message);
      assert.equal(await page.locator('#failure-output').inputValue(),error.replace(/\r\n/g,'\n'));
    }
    assert.equal(requests.includes('/api/troubleshoot'),false);
    await page.locator('#diagnose-run').click();
    await page.locator('#failure-result').waitFor({state:'visible'});
    assert.equal(await page.locator('#failure-original').textContent(),error);
  }, async page => {
    await page.addInitScript(() => {
      const read = File.prototype.arrayBuffer;
      File.prototype.arrayBuffer = function () {
        return this.name === 'unreadable.log' ? Promise.reject(new Error('Synthetic read failure')) : read.call(this);
      };
    });
  });
  await scenario('late file reads cannot overwrite newer typed text or a newer selected file', async (page,{requests}) => {
    await page.locator('#failure-file').setInputFiles({name:'slow-first.log',mimeType:'text/plain',buffer:Buffer.from(output(),'utf8')});
    await page.waitForFunction(() => window.__finishFileReads.length === 1);
    const newer = output('return 88');
    await page.locator('#failure-output').fill(newer);
    await page.evaluate(async () => {window.__finishFileReads.shift()();await new Promise(requestAnimationFrame);});
    assert.equal(await page.locator('#failure-output').inputValue(),newer);
    assert.doesNotMatch(await page.locator('#failure-file-status').textContent(),/^Loaded slow-first\.log/);
    await page.locator('#failure-file').setInputFiles({name:'slow-second.log',mimeType:'text/plain',buffer:Buffer.from('old file','utf8')});
    await page.waitForFunction(() => window.__finishFileReads.length === 1);
    await page.locator('#failure-file').setInputFiles({name:'newer.log',mimeType:'text/plain',buffer:Buffer.from(newer,'utf8')});
    await page.waitForFunction(() => document.querySelector('#failure-file-status').textContent.startsWith('Loaded newer.log'));
    await page.evaluate(async () => {window.__finishFileReads.shift()();await new Promise(requestAnimationFrame);});
    assert.equal(await page.locator('#failure-output').inputValue(),newer);
    assert.match(await page.locator('#failure-file-status').textContent(),/^Loaded newer.log/);
    assert.equal(requests.includes('/api/troubleshoot'),false);
  }, async page => {
    await page.addInitScript(() => {
      const read = File.prototype.arrayBuffer;
      window.__finishFileReads = [];
      File.prototype.arrayBuffer = function () {
        const bytes = read.call(this);
        return this.name.startsWith('slow-') ? new Promise((resolve,reject) => bytes.then(value => window.__finishFileReads.push(() => resolve(value)),reject)) : bytes;
      };
    });
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
    assert.equal(await page.locator('#failure-technical-limits').evaluate(node => node.open),false);
    assert.equal(await page.locator('#failure-technical-limits li').first().isVisible(),false);
    assert.doesNotMatch(await page.locator('#failure-result-title').innerText(),/fixed|ready|root cause/i);
    assert.equal(await page.locator('#failure-result-title').evaluate(el => el === document.activeElement),true);
    assert.match(await page.locator('#failure-captured-project').innerText(),/Synthetic failure fixture/);
    assert.match(await page.locator('#failure-captured-project').innerText(),new RegExp(fixture));
    assert.equal(await page.locator('#failure-format').innerText(),'Python source check');
  });
  for (const short of [false,true]) {
    await scenario(`${short ? 'short' : 'default'} decorated pytest output locates exact source and preserves the complete report`, async page => {
      const raw = pytestSection('FAILURES') + pytestHeading('test_parse_count') + pytestFailure(undefined,short)
        + pytestSection('short test summary info') + 'FAILED tests/test_parse.py::test_parse_count - ValueError: invalid literal\n';
      const error = short ? raw.replaceAll('\n','\r\n') : raw;
      await fillRunDetail(page, '#failure-command', short ? 'pytest --tb=short' : 'pytest');
      if (short) {
        await page.locator('#failure-file').setInputFiles({name:'pytest-short.log',mimeType:'text/plain',buffer:Buffer.from(error,'utf8')});
        await page.waitForFunction(() => document.querySelector('#failure-file-status').textContent.startsWith('Loaded pytest-short.log'));
        await page.locator('#diagnose-run').click();
        await page.locator('#failure-result').waitFor({state:'visible'});
      } else await diagnose(page,error);
      assert.match(await page.locator('#failure-result-title').innerText(),/Source located/);
      assert.equal(await page.locator('#failure-format').innerText(),'pytest source check');
      assert.match(await page.locator('#failure-result-context').innerText(),/parse.py:4.*matches/);
      assert.equal(await page.locator('#failure-source .is-failure').textContent(),'4    return int(value)');
      assert.match(await page.locator('#failure-exception').innerText(),/ValueError: invalid literal/);
      assert.match(await page.locator('#failure-guidance').innerText(),/final pytest failure/);
      assert.equal(await page.locator('#failure-original').textContent(),error);
      const brief = await page.locator('#failure-copy-text').inputValue();
      assert.match(brief,/"error_format": "pytest"/);
      assert.ok(brief.includes(raw));
      assert.ok(brief.includes(source));
      await page.getByText('Original error & report',{exact:true}).click();
      const downloading = page.waitForEvent('download');
      await page.locator('#download-failure-json').click();
      const report = JSON.parse(await fs.readFile(await (await downloading).path(),'utf8'));
      assert.equal(report.error_output,error);
      assert.equal(report.error_sha256,createHash('sha256').update(error).digest('hex'));
      assert.equal(report.format,'pytest');
    });
  }
  await scenario('a final pytest failure outside the project keeps earlier source visibly incomplete', async page => {
    const error = pytestSection('FAILURES') + pytestHeading('test_local') + pytestFailure()
      + pytestHeading('test_final') + pytestFailure('/outside-approved-project/final.py',false,'final failure')
      + pytestSection('short test summary info') + 'FAILED tests/test_parse.py::test_local\nFAILED external/test_final.py::test_final\n';
    await diagnose(page,error);
    assert.equal(await page.locator('#failure-format').innerText(),'pytest source check');
    assert.equal(await page.locator('#failure-result-title').innerText(),'Other source captured — final failure still unlocated');
    assert.equal(await page.locator('#failure-source').innerText(),'');
    assert.equal(await page.locator('#failure-exception').innerText(),'ValueError: final failure');
    const brief = await page.locator('#failure-copy-text').inputValue();
    assert.match(brief,/Only earlier source was captured/);
    assert.ok(brief.includes(source));
    assert.match(brief,/outside-approved-project\/final.py/);
    await page.locator('#failure-frames > summary').click();
    assert.match(await page.locator('#failure-frame-list').innerText(),/parse.py:4/);
    assert.match(await page.locator('#failure-frame-list').innerText(),/outside_project/);
    assert.equal(await page.locator('#failure-frame-list .source').count(),1);
  });
  await scenario('captured pytest output cannot replace the real location or terminal exception', async page => {
    const fakePath = path.join(fixture,'worker.js');
    const error = pytestSection('FAILURES') + pytestHeading('test_parse_count') + pytestFailure()
      + '---------------------------- Captured stdout call -----------------------------\n'
      + `${fakePath}:2: in pretend_failure\n    throw new TypeError("synthetic failure");\nE   TypeError: printed text\n`
      + '_____________ test_printed_example _____________\n'
      + `>       pretend_failure()\nE       RuntimeError: printed example\n${fakePath}:2: RuntimeError\n`
      + pytestSection('short test summary info') + 'FAILED tests/test_parse.py::test_parse_count - ValueError: invalid literal\n';
    await diagnose(page,error);
    assert.equal(await page.locator('#failure-format').innerText(),'pytest source check');
    assert.match(await page.locator('#failure-result-context').innerText(),/parse.py:4/);
    assert.match(await page.locator('#failure-exception').innerText(),/^ValueError:/);
    assert.doesNotMatch(await page.locator('#failure-exception').innerText(),/printed/);
    await page.locator('#failure-frames > summary').click();
    assert.equal(await page.locator('#failure-frame-list > li').count(),1);
    assert.doesNotMatch(await page.locator('#failure-frame-list').innerText(),/worker.js|pretend_failure/);
    assert.ok((await page.locator('#failure-copy-text').inputValue()).includes(error));
    assert.equal(await page.locator('#failure-original').textContent(),error);
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
    await page.getByText('Original error & report',{exact:true}).click();
    const downloading = page.waitForEvent('download');
    await page.locator('#download-failure-text').click();
    const saved = await fs.readFile(await (await downloading).path(),'utf8');
    assert.equal(saved,brief);
    assert.match(saved,/Only earlier source was captured/);
    assert.match(saved,/outside-approved-project\/handler.py/);
    assert.match(saved,/outside_project/);
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
    assert.match(await page.locator('#failure-limits').innerText(),/2 of 3 reported locations were not captured/);
  });
  for (const externalFirst of [false,true]) {
    await scenario(`aggregate member labels and copied identities stay bound${externalFirst ? ' when the first member is outside the project' : ''}`, async page => {
      const first = externalFirst ? '/outside-approved-project/first.js' : path.join(fixture,'worker.js');
      const second = path.join(fixture,'unicode.js');
      const error = `[AggregateError: All promises were rejected] {\n  [errors]: [\n    TypeError: first input failed\n        at first (${first}:2:9),\n    RangeError: second input failed\n        at second (${second}:3:7)\n  ]\n}\n`;
      await diagnose(page,error);
      assert.equal(await page.locator('#failure-exception').innerText(),externalFirst ? 'RangeError: second input failed' : 'TypeError: first input failed');
      await page.locator('#failure-frames > summary').click();
      const frames = page.locator('#failure-frame-list > li');
      assert.match(await frames.nth(0).innerText(),/Error 1 · Chain 0 · member of error 0 · TypeError: first input failed/);
      assert.doesNotMatch(await frames.nth(0).innerText(),/RangeError: second input failed/);
      assert.match(await frames.nth(1).innerText(),/Error 2 · Chain 0 · member of error 0 · RangeError: second input failed/);
      assert.doesNotMatch(await frames.nth(1).innerText(),/TypeError: first input failed/);
      assert.equal(await page.locator('#failure-original').textContent(),error);
      const brief = await page.locator('#failure-copy-text').inputValue();
      const errors = briefJson(brief,'Parsed errors and explicit associations');
      const locations = briefJson(brief,'Locations and source comparison');
      assert.equal(briefJson(brief,'Captured current source').evidence_id,'E1');
      assert.deepEqual(errors.exceptions.map(item => [item.type,item.message]),[['AggregateError','All promises were rejected'],['TypeError','first input failed'],['RangeError','second input failed']]);
      assert.deepEqual(locations.map(item => [item.frame_id,item.chain_index,item.exception_index]),[['F1',0,1],['F2',0,2]]);
      assert.equal(locations[0].status,externalFirst ? 'outside_project' : 'located');
      assert.equal(locations[0].evidence_id,externalFirst ? null : 'E1');
      assert.equal(locations[1].evidence_id,externalFirst ? 'E1' : 'E2');
      assert.equal(errors.terminal_exception.type,externalFirst ? 'RangeError' : 'TypeError');
    });
  }
  await scenario('invalid or absent error indexes never inherit a neighboring member message', async page => {
    await page.route('**/api/troubleshoot',async route => {
      const response = await route.fetch(), value = await response.json();
      value.frames[0].exception_index = value.exceptions.length;
      value.frames.push({...value.frames[0],frame_id:'F2',exception_index:-1});
      value.frames.push({...value.frames[0],frame_id:'F3',exception_index:'0'});
      value.frames.push({...value.frames[0],frame_id:'F4',exception_index:null});
      value.frames.push({...value.frames[0],frame_id:'F5',chain_index:1,exception_index:0});
      await route.fulfill({response,json:value});
    });
    await diagnose(page,`TypeError: do not lend this message\n    at ${path.join(fixture,'worker.js')}:2:9\n`);
    await page.locator('#failure-frames > summary').click();
    const frames = page.locator('#failure-frame-list > li');
    assert.equal(await frames.count(),5);
    for (let index=0;index<5;index++) {
      assert.match(await frames.nth(index).innerText(),new RegExp(`F${index+1}.*worker.js`));
      assert.match(await frames.nth(index).innerText(),new RegExp(`Chain ${index === 4 ? 1 : 0} · no explicit error association`));
      assert.doesNotMatch(await frames.nth(index).innerText(),/do not lend this message/);
    }
    const locations = briefJson(await page.locator('#failure-copy-text').inputValue(),'Locations and source comparison');
    assert.deepEqual(locations.map(item => item.exception_index),[null,null,null,null,null]);
  });
  await scenario('unsupported nested aggregate members retain their gap and never borrow a sibling error', async page => {
    const error = `AggregateError: outer\n  [errors]: [\n    AggregateError: nested {\n      [errors]: [\n        TypeError: inner\n            at ${path.join(fixture,'worker.js')}:2:9\n      ]\n    }\n  ]\n}\n`;
    await diagnose(page,error);
    assert.equal(await page.locator('#failure-result-title').innerText(),'No source located');
    assert.match(await page.locator('#failure-guidance').innerText(),/could not be interpreted/);
    assert.match(await page.locator('#failure-limits').innerText(),/node_aggregate_format_unsupported/);
    const locations = briefJson(await page.locator('#failure-copy-text').inputValue(),'Locations and source comparison');
    assert.equal(locations[0].status,'node_aggregate_format_unsupported');
    assert.equal(locations[0].exception_index,null);
    await page.locator('#failure-frames > summary').click();
    assert.match(await page.locator('#failure-frame-list').innerText(),/no explicit error association/);
    assert.doesNotMatch(await page.locator('#failure-frame-list').innerText(),/TypeError: inner/);
    assert.equal(await page.locator('#failure-original').textContent(),error);
  });
  await scenario('JavaScript Unicode separators retain the parser line numbering in the source viewer', async page => {
    await diagnose(page,`Error: synthetic separators\n    at ${path.join(fixture,'unicode.js')}:3:7\n`);
    assert.equal(await page.locator('#failure-source .line').count(),3);
    assert.equal(await page.locator('#failure-source .is-failure').textContent(),'3throw new Error("synthetic separators");');
  });
  await scenario('Node.js end-of-file locations show preceding source without inventing the reported source line', async page => {
    const error = `${path.join(fixture,'eof.js')}:2\n\n\n\nSyntaxError: Unexpected end of input\n`;
    await diagnose(page,error);
    assert.equal(await page.locator('#failure-result-title').innerText(),'End of file reported — inspect preceding source');
    assert.match(await page.locator('#failure-result-context').innerText(),/eof.js:2.*end of file.*through line 1/);
    assert.equal(await page.locator('#failure-source .is-failure .line-number').innerText(),'1');
    const brief = await page.locator('#failure-copy-text').inputValue();
    assert.match(brief,/"line": 2/);
    assert.match(brief,/"location_kind": "end_of_file"/);
    assert.match(brief,/"context_line": 1/);
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
    await fillRunDetail(page, '#failure-command', command);
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
  for (const changed of ['error', 'command', 'project', 'working folder']) {
    await scenario(`editing the ${changed} marks the captured report outdated and disables handoff and exports`, async page => {
      await diagnose(page);
      const captured = await page.locator('#failure-captured-project').innerText();
      if (changed === 'error') await page.locator('#failure-output').fill(output('return 99'));
      if (changed === 'command') await fillRunDetail(page, '#failure-command', 'python parse.py --changed');
      if (changed === 'project') await page.locator('#failure-project').selectOption('starter-demo');
      if (changed === 'working folder') await fillRunDetail(page, '#failure-working-directory', nestedWorkingDirectory);
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
    await fillRunDetail(page, '#failure-command', command);
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
  await scenario('possible credentials warn with masked previews before sharing and leave exact copied data unchanged', async page => {
    const token = 'gh' + 'p_' + 'A1b2'.repeat(9);
    const error = output().replace("invalid literal for int() with base 10: 'many'",'synthetic credential ' + token);
    const command = 'python parse.py --synthetic-token ' + token;
    await fillRunDetail(page, '#failure-command', command);
    await diagnose(page,error);
    const warning = page.locator('#failure-credential-warning');
    assert.equal(await warning.isVisible(),true);
    assert.equal(await warning.getAttribute('role'),'alert');
    const warningText = await warning.innerText();
    assert.match(warningText,/Possible credentials/);
    assert.match(warningText,/GitHub token/);
    assert.ok(warningText.includes('ghp_…'));
    assert.equal(warningText.includes(token),false);
    assert.equal(await warning.evaluate(el => !!(el.compareDocumentPosition(document.querySelector('#copy-failure-brief')) & Node.DOCUMENT_POSITION_FOLLOWING)),true);
    assert.equal(await page.locator('#copy-failure-brief').isEnabled(),true);
    await page.locator('#copy-failure-brief').click();
    await page.waitForFunction(() => window.__failureCopies.length === 1);
    const copied = await page.evaluate(() => window.__failureCopies[0]);
    assert.ok(copied.includes(error));
    assert.ok(copied.includes(command));
    assert.equal(copied.includes('Possible credentials'),false);
    assert.equal(copied.includes('ghp_…'),false);
    await page.getByText('Original error & report',{exact:true}).click();
    const downloading = page.waitForEvent('download');
    await page.locator('#download-failure-text').click();
    const download = await downloading;
    const saved = await fs.readFile(await download.path(),'utf8');
    assert.ok(saved.includes(error));
    assert.equal(saved.includes('Possible credentials'),false);
    await page.locator('#failure-output').fill(output());
    assert.equal(await warning.isVisible(),false);
    assert.equal(await warning.textContent(),'');
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
    await fillRunDetail(page, '#failure-command', 'python parse.py --newer-context');
    await page.evaluate(() => window.__finishFailureCopy());
    await page.waitForFunction(() => document.querySelector('#failure-notice').textContent.includes('earlier captured'));
    assert.equal(await page.locator('#failure-stale').isVisible(),true);
    assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
    assert.equal(await page.locator('#failure-command').inputValue(),'python parse.py --newer-context');
    assert.equal(await page.locator('#failure-copy-text').inputValue(),'');
  }, async page => {
    await page.addInitScript(() => Object.defineProperty(navigator,'clipboard',{value:{writeText:() => new Promise(resolve => {window.__finishFailureCopy = resolve;})},configurable:true}));
  });
  await scenario('an unsettled earlier copy blocks a newer report copy while review and exports remain available', async page => {
    await fillRunDetail(page, '#failure-command', 'python parse.py --capture-A');
    await diagnose(page);
    await page.locator('#copy-failure-brief').click();
    assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
    assert.equal(await page.locator('#copy-failure-brief').getAttribute('aria-busy'),'true');
    // Repeated or scripted clicks cannot queue another uncancellable write.
    await page.locator('#copy-failure-brief').dispatchEvent('click');
    assert.equal(await page.evaluate(() => window.__clipboardWrites.length),1);
    await fillRunDetail(page, '#failure-command', 'python parse.py --capture-B');
    await page.locator('#diagnose-run').click();
    await page.locator('#failure-result').waitFor({state:'visible'});
    assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
    assert.match(await page.locator('#failure-copy-status').innerText(),/earlier captured debugging brief/);
    await page.locator('#copy-failure-brief').dispatchEvent('click');
    assert.equal(await page.evaluate(() => window.__clipboardWrites.length),1);
    assert.match(await page.locator('#failure-copy-text').inputValue(),/--capture-B/);
    await page.locator('#failure-copy-review > summary').click();
    assert.equal(await page.locator('#failure-copy-text').isVisible(),true);
    await page.getByText('Original error & report',{exact:true}).click();
    assert.equal(await page.locator('#download-failure-text').isEnabled(),true);
    assert.equal(await page.locator('#download-failure-json').isEnabled(),true);
    const downloading = page.waitForEvent('download');
    await page.locator('#download-failure-text').click();
    assert.match(await fs.readFile(await (await downloading).path(),'utf8'),/--capture-B/);
    await page.evaluate(() => window.__clipboardWrites[0].finish());
    await page.waitForFunction(() => document.querySelector('#failure-notice').textContent.includes('earlier captured'));
    assert.equal(await page.locator('#copy-failure-brief').isEnabled(),true);
    assert.equal(await page.locator('#copy-failure-brief').getAttribute('aria-busy'),'false');
    await page.locator('#copy-failure-brief').click();
    assert.equal(await page.evaluate(() => window.__clipboardWrites.length),2);
    await page.evaluate(() => window.__clipboardWrites[1].finish());
    await page.waitForFunction(() => document.querySelector('#failure-copy-status').textContent.includes('Browser reported copying'));
    assert.match(await page.evaluate(() => window.__syntheticClipboard),/--capture-B/);
    assert.equal(await page.locator('#failure-command').inputValue(),'python parse.py --capture-B');
  }, async page => {
    await page.addInitScript(() => {
      window.__clipboardWrites = [];
      Object.defineProperty(navigator,'clipboard',{value:{writeText:text => new Promise(resolve => {
        window.__clipboardWrites.push({text,finish(){window.__syntheticClipboard=text;resolve();}});
      })},configurable:true});
    });
  });
  await scenario('the source and failed-run workflows share one unsettled clipboard write', async page => {
    await diagnose(page);
    await page.locator('#copy-failure-brief').click();
    await page.locator('#choose-source-brief').click();
    const question = 'Find the retry limit in this synthetic source fixture.';
    const sourceProject = await page.evaluate(root => window.sbWorkbench.getState().native.projects.find(project => project.path === root).id,sourceFixture);
    await page.locator('#project').selectOption(sourceProject);
    await page.locator('#request').fill(question);
    await page.locator('#prepare').click();
    await page.waitForFunction(text => document.querySelector('#original-request').textContent === text,question);
    assert.equal(await page.locator('#copy').isDisabled(),true);
    assert.equal(await page.locator('#copy').getAttribute('aria-busy'),'true');
    assert.match(await page.locator('#copy-status').innerText(),/copying a debugging brief/);
    await page.locator('#copy').dispatchEvent('click');
    assert.equal(await page.evaluate(() => window.__clipboardWrites.length),1);
    assert.equal(await page.locator('#download-text').isEnabled(),true);
    await page.evaluate(() => window.__clipboardWrites[0].finish());
    await page.waitForFunction(() => !document.querySelector('#copy').disabled);
    await page.locator('#copy').click();
    assert.equal(await page.evaluate(() => window.__clipboardWrites.length),2);
    await page.locator('#choose-failed-run').click();
    assert.equal(await page.locator('#copy-failure-brief').isDisabled(),true);
    assert.match(await page.locator('#failure-copy-status').innerText(),/copying a source brief/);
    await page.locator('#copy-failure-brief').dispatchEvent('click');
    assert.equal(await page.evaluate(() => window.__clipboardWrites.length),2);
    assert.equal(await page.locator('#failure-output').inputValue(),output());
    assert.equal(await page.locator('#download-failure-text').isEnabled(),true);
    await page.evaluate(() => window.__clipboardWrites[1].finish());
    await page.waitForFunction(() => !document.querySelector('#copy-failure-brief').disabled);
    assert.equal(await page.locator('#copy-failure-brief').getAttribute('aria-busy'),'false');
    assert.equal(await page.locator('#failure-copy-status').innerText(),'');
    assert.match(await page.evaluate(() => window.__syntheticClipboard),/Find the retry limit/);
    await page.locator('#choose-source-brief').click();
    assert.equal(await page.locator('#request').inputValue(),question);
    assert.match(await page.locator('#copy-status').innerText(),/Browser reported copying this brief/);
  }, async page => {
    await page.addInitScript(() => {
      window.__clipboardWrites = [];
      Object.defineProperty(navigator,'clipboard',{value:{writeText:text => new Promise(resolve => {
        window.__clipboardWrites.push({text,finish(){window.__syntheticClipboard=text;resolve();}});
      })},configurable:true});
    });
  }, 1);
  await scenario('the example needs explicit selection and cannot overwrite a real pasted error', async page => {
    const error = output();
    await page.locator('#failure-output').fill(error);
    await page.locator('#try-failure-example').click();
    assert.equal(await page.locator('#failure-output').inputValue(),error);
    assert.match(await page.locator('#failure-notice').innerText(),/unchanged/);
    await page.locator('#failure-output').fill('');
    await fillRunDetail(page, '#failure-working-directory', nestedWorkingDirectory);
    await page.locator('#try-failure-example').click();
    assert.equal(await page.locator('#failure-working-directory').inputValue(),nestedWorkingDirectory);
    assert.equal(await page.locator('#failure-output').inputValue(),'');
    assert.equal(await page.locator('#failure-example-notice').isVisible(),false);
    assert.match(await page.locator('#failure-notice').innerText(),/working folder are unchanged/);
    await fillRunDetail(page, '#failure-working-directory', '');
    await page.locator('#try-failure-example').click();
    assert.equal(await page.locator('#failure-example-notice').isVisible(),true);
    assert.equal(await page.locator('#failure-working-directory').inputValue(),'');
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
  await scenario('source preparation stays visible across workflows and preserves editable error inputs through stop', async (page,{requests}) => {
    const job = 'c4'.repeat(16);
    let releaseAcknowledgement, startSeen, status = 'RUNNING';
    const acknowledgement = new Promise(resolve => {releaseAcknowledgement=resolve;});
    const started = new Promise(resolve => {startSeen=resolve;});
    await page.route('**/api/tasks',async route => {
      startSeen();
      await acknowledgement;
      await route.fulfill({json:{task_id:job,state:'RUNNING'}});
    });
    await page.route(`**/api/tasks/${job}`,route => route.fulfill({json:{task_id:job,state:status}}));
    await page.route(`**/api/tasks/${job}/cancel`,route => {
      status='CANCELLED';
      return route.fulfill({json:{task_id:job,state:status}});
    });
    const error = output(), command = 'python parse.py --preserved';
    await page.locator('#failure-output').fill(error);
    await fillRunDetail(page,'#failure-command',command);
    await fillRunDetail(page,'#failure-working-directory',nestedWorkingDirectory);
    await page.locator('#choose-source-brief').click();
    const project = await page.evaluate(root => window.sbWorkbench.getState().native.projects.find(item => item.path === root).id,sourceFixture);
    await page.locator('#project').selectOption(project);
    await page.locator('#request').fill('Inspect the synthetic retry limit.');
    try {
      await page.locator('#prepare').click();
      await started;
      await page.locator('#choose-failed-run').click();
      assert.equal(await page.locator('#preparation-activity').isVisible(),true);
      assert.equal(await page.locator('#diagnose-run').isDisabled(),true);
      assert.equal(await page.locator('#failure-output').isEditable(),true);
      await page.locator('#failure-form').dispatchEvent('submit');
      assert.match(await page.locator('#failure-notice').innerText(),/View preparation.*Stop/);
      assert.equal(requests.includes('/api/troubleshoot'),false);
      releaseAcknowledgement();
      await page.waitForFunction(() => !document.querySelector('#stop').disabled);
      assert.equal(await page.locator('#diagnose-run').isDisabled(),true);
      const newer = output('return 99');
      await page.locator('#failure-output').fill(newer);
      assert.equal(await page.locator('#failure-command').inputValue(),command);
      assert.equal(await page.locator('#failure-working-directory').inputValue(),nestedWorkingDirectory);
      await page.evaluate(() => window.sbWorkbench.connectionFailed());
      assert.equal(await page.locator('#diagnose-run').isDisabled(),true);
      assert.match(await page.locator('#preparation-activity-text').innerText(),/unknown/i);
      await page.locator('#retry-connection').click();
      await page.waitForFunction(() => window.sbWorkbench.isConnected());
      assert.equal(await page.locator('#diagnose-run').isDisabled(),true);
      await page.locator('#activity-view').click();
      assert.equal(await page.locator('#source-brief-workflow').isVisible(),true);
      await page.locator('#stop').click();
      await page.waitForFunction(() => !window.sbWorkbench.isPreparing());
      assert.equal(await page.locator('#preparation-activity').isVisible(),false);
      await page.locator('#choose-failed-run').click();
      assert.equal(await page.locator('#diagnose-run').isEnabled(),true);
      assert.equal(await page.locator('#failure-output').inputValue(),newer);
      assert.equal(await page.locator('#failure-command').inputValue(),command);
      assert.equal(await page.locator('#failure-working-directory').inputValue(),nestedWorkingDirectory);
      assert.equal(requests.includes('/api/troubleshoot'),false);
    } finally {releaseAcknowledgement?.();}
  },undefined,1);
  await scenario('a service busy race gives a useful wait or stop action without changing run inputs', async (page,{requests}) => {
    await page.route('**/api/troubleshoot',route => route.fulfill({status:409,json:{error:'helper_busy'}}));
    const error = output(), command = 'python parse.py --keep';
    await page.locator('#failure-output').fill(error);
    await fillRunDetail(page,'#failure-command',command);
    await fillRunDetail(page,'#failure-working-directory',nestedWorkingDirectory);
    await page.locator('#diagnose-run').click();
    await page.locator('#failure-notice').waitFor({state:'visible'});
    const message = await page.locator('#failure-notice').innerText();
    assert.match(message,/View preparation.*Stop/);
    assert.doesNotMatch(message,/helper_busy/);
    assert.equal(await page.locator('#failure-output').inputValue(),error);
    assert.equal(await page.locator('#failure-command').inputValue(),command);
    assert.equal(await page.locator('#failure-working-directory').inputValue(),nestedWorkingDirectory);
    assert.equal(await page.locator('#failure-result').isVisible(),false);
    assert.equal(requests.filter(url => url === '/api/troubleshoot').length,1);
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
  const recovery = spawn(process.execPath,[path.join(__dirname,'browser_session_recovery_test.cjs'),...process.argv.slice(2)],{env:process.env,stdio:'inherit'});
  await new Promise((resolve,reject) => {
    recovery.once('error',reject);
    recovery.once('exit',(code,signal) => code === 0 ? resolve() : reject(new Error(`Session-recovery browser checks failed (${signal || code}).`)));
  });
})().catch(error => {console.error(error);process.exitCode=1;}).finally(async () => {
  if (browser) await browser.close();
  if (server) server.kill('SIGTERM');
  if (fixture) await fs.rm(fixture,{recursive:true,force:true});
  if (sourceFixture) await fs.rm(sourceFixture,{recursive:true,force:true});
  for (const root of connectionFixtures) await fs.rm(root,{recursive:true,force:true});
});
