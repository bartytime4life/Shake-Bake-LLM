// Actual subprocess regressions; no browser installation or model is needed.
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const {once}=require('node:events');
const {test}=require('node:test');
const {waitForServer}=require('./browser_server.cjs');
const child=source=>spawn(process.execPath,['-e',source],{stdio:['ignore','pipe','ignore']});
async function stop(server){
  if(server.exitCode!==null||server.signalCode!==null)return;
  const exited=once(server,'exit');server.kill('SIGKILL');await exited;
}
test('a server exit without a port rejects instead of silently skipping browser checks',async()=>{
  const server=child('process.exit(7)');
  await assert.rejects(waitForServer(server),/exited before reporting its port \(code 7/);
});
test('an unavailable interpreter rejects startup',async()=>{
  const server=spawn('/nonexistent-shake-bake-test-interpreter',[],{stdio:['ignore','pipe','ignore']});
  await assert.rejects(waitForServer(server),/could not start/);
});
test('an alive server that never reports a port times out',async()=>{
  const server=child('setInterval(()=>{},1000)');
  try{await assert.rejects(waitForServer(server,{timeoutMs:100}),/startup timed out/);}
  finally{await stop(server);}
});
test('fragmented port output resolves while the service is still alive',async()=>{
  const server=child('process.stdout.write("43");setTimeout(()=>process.stdout.write("087\\n"),20);setInterval(()=>{},1000)');
  try{assert.equal(await waitForServer(server),'http://127.0.0.1:43087');assert.equal(server.exitCode,null);}
  finally{await stop(server);}
});
