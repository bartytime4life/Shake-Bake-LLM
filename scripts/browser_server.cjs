// Await a bounded test-server startup. An unfulfilled Promise alone does not
// keep Node alive: a child that exits before printing its port must reject.
function waitForServer(server,{timeoutMs=10000}={}){
  return new Promise((resolve,reject)=>{
    let output='';
    const cleanup=()=>{clearTimeout(timeout);server.stdout.off('data',onData);server.off('error',onError);server.off('exit',onExit);};
    const fail=error=>{cleanup();reject(error);};
    const onError=error=>fail(new Error('Test server could not start: '+error.message));
    const onExit=(code,signal)=>fail(new Error(`Test server exited before reporting its port (code ${code}, signal ${signal}).`));
    const onData=chunk=>{
      output+=chunk.toString();
      if(output.length>1024){fail(new Error('Test server startup output exceeded its limit.'));return;}
      if(!output.includes('\n'))return;
      const line=output.split('\n',1)[0].trim(),port=Number(line);
      if(!/^\d+$/.test(line)||port<1||port>65535){fail(new Error('Test server reported an invalid port.'));return;}
      cleanup();resolve('http://127.0.0.1:'+port);
    };
    const timeout=setTimeout(()=>fail(new Error('Test server startup timed out.')),timeoutMs);
    server.stdout.on('data',onData);server.once('error',onError);server.once('exit',onExit);
    if(server.exitCode!==null||server.signalCode!==null)onExit(server.exitCode,server.signalCode);
  });
}
module.exports={waitForServer};
