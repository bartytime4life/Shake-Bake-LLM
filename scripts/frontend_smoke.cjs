// Behavioral checks of the API adapter; this does not claim browser acceptance.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../src/shake_bake/web/app.js'), 'utf8');
const requests = [];
const context = {
  document: {getElementById: () => ({})}, window: {},
  localStorage: {getItem: () => JSON.stringify({ai_mode: 'off'})},
  fetch: async (target, options) => {
    requests.push({target, options});
    return {ok: true, json: async () => ({task_id: 'synthetic-job'})};
  },
};
vm.createContext(context);
vm.runInContext(source.slice(0, source.indexOf('function renderCatalog')), context);
(async () => {
  const view = vm.runInContext('viewState({version:"test",projects:[{id:"demo"}],recent:[],local_ai_enabled:false,policy:{enabled:true}})', context);
  assert.equal(view.preferences.ai_mode, 'off');
  assert.equal(view.local_ai_paused, true);
  await vm.runInContext('api("/api/start", {project_id:"demo",request:"Find coverage",task_kind:"code",ai_mode:"best"})', context);
  assert.equal(requests.length, 1, 'Starting from a stale browser must not change global Local AI state');
  assert.equal(requests[0].target, '/api/tasks');
  assert.deepEqual(JSON.parse(requests[0].options.body), {project_id:'demo', task:'Find coverage', task_kind:'code'});
  await vm.runInContext('api("/api/pause", {paused:false})', context);
  assert.equal(requests[1].target, '/api/settings');
  assert.deepEqual(JSON.parse(requests[1].options.body), {enabled:true});
  console.log('API adapter preserves the service pause; only an explicit toggle changes it.');
})().catch(error => { console.error(error); process.exitCode = 1; });
