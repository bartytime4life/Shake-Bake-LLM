'use strict';
const $ = (id) => document.getElementById(id);
// Longer than the server's 12-second connection budget. Aborting this browser
// request does not establish whether a service operation ran or a job stopped.
const REQUEST_TIMEOUT_MS = 15000;
let csrf = '', state = null, active = null, pinned = null, models = [], timer = null, polling = false;
let inventoryLoading = false, historySignature = '', serviceTimer = null, sessionSync = null;
let copyState = null;
let settingsPending = false, connected = null, stateRevision = 0, pinRevision = 0;
let draftInitialized = false, draftProjectId = '';
const draftTouched = new Set(), taskKinds = ['code','troubleshoot','documents','search'];
function message(text, error = false) { $('notice').textContent = text; $('notice').classList.toggle('error', error); $('notice').hidden = !text; }
const preview = window.__SB_RECORDED_PREVIEW__ || null;
let nativeState = null, readinessRunning = false;
let modelCheckRevision = 0, modelCheckContext = null;
function savedPreferences() {
  try { const p=JSON.parse(localStorage.getItem('shake-bake-preferences')||'{}');return p&&typeof p==='object'?p:{}; } catch { return {}; }
}
function viewState(value) {
  const saved=savedPreferences();
  const project=value.projects.some(p=>p.id===saved.project_id)?saved.project_id:value.projects[0].id;
  const kind=['code','troubleshoot','documents','search'].includes(saved.task_kind)?saved.task_kind:'code';
  const recent=value.recent.map(r=>({...r,job_id:r.task_id,request_preview:r.task,created_at:new Date(r.created*1000).toISOString(),status:r.state==='DONE'?'prepared':r.state.toLowerCase()}));
  return {native:value,version:value.version,csrf:value.csrf_token,projects:value.projects.map(p=>p.id),
    preferences:{project_id:project,task_kind:kind,ai_mode:value.local_ai_enabled?(saved.ai_mode==='trial'?'trial':'best'):'off',model:saved.model||null,digest:saved.digest||null},
    recent,active:recent.find(r=>r.status==='running')||null,local_ai_allowed:value.policy.enabled,local_ai_paused:!value.local_ai_enabled,
    pipeline_sha256:value.pipeline_id,shared_native:value.shared_native===true,allow_candidate_trials:value.allow_candidate_trials};
}
function viewJob(value) {
  const meta=nativeState?.recent.find(r=>r.task_id===value.task_id);
  const base={job_id:value.task_id,project_id:value.project_id||meta?.project_id||$('project').value,
    completed_at:new Date((value.created_at||meta?.created||Date.now()/1000)*1000).toISOString(),native_result:value};
  if(value.state!=='DONE'||['DENY','ERROR'].includes(value.outcome))return {...base,status:value.state==='RUNNING'?'running':value.state==='CANCELLED'?'cancelled':'failed',error:{message:value.code||value.state}};
  const route=value.routing||{}, evidence=(value.evidence||[]).map(e=>({...e,content:e.text}));
  const note=value.worker;
  return {...base,status:evidence.length?'prepared':'incomplete',packet:{original_request:value.original_request,task_kind:value.task_kind,started_at:base.completed_at,evidence,
    gaps:evidence.length?[]:[{code:'no_usable_evidence',message:'No usable source matched within the scan. Clarify the request; this is not an exhaustive review.'}],
    routing:{...route,status:note?(route.mode==='candidate_trial'?'candidate_notes':'qualified_profile_notes'):route.model||value.worker_error&&route.reason!=='no_qualified_profile'&&route.reason!=='local_ai_disabled'?'abstained':'evidence_only',reason:route.why||value.worker_error||'Exact evidence only.',final_answer_ready:false},
    model_notes:note?{notes:[{text:note.summary,evidence_ids:note.evidence_ids}],uncertainties:note.questions}:null,
    receipt:{files_examined:value.files_examined,source_bytes_read:value.source_bytes_read,excerpt_bytes:value.selected_excerpt_bytes,local_server_reported_usage:note?.usage||null,observed_runtime_version:note?.observed_runtime_version||null,requested_configuration:note?.requested_configuration||null,cloud_tokens:null,token_savings:null,
      discovery:{files_read:value.files_examined,cutoffs:value.cutoffs||[],refusals:value.exclusions||{}}},
    limitations:['Selected excerpts are not a complete repository review.','Source identities refer to captured bytes; later changes require a fresh task.','Model notes are unverified. Real host delivery, accuracy, hardware calibration and savings remain unqualified.','Jobs are retained only in this running session, up to eight and approximately five minutes.']}};
}
async function api(path, body) {
  if(path==='/api/preferences'){if(!preview)localStorage.setItem('shake-bake-preferences',JSON.stringify(body));return body;}
  if(preview){if(path==='/api/state')return viewState(preview.state);if(path==='/api/result'&&body.job_id===preview.result.task_id)return viewJob(preview.result);throw new Error('This is a recorded inert demo. New tasks run in the local application.');}
  let target=path, payload=body;
  if(path==='/api/result'){target='/api/tasks/'+body.job_id;payload=undefined;}
  if(path==='/api/start'){
    target='/api/tasks';payload={project_id:body.project_id,task:body.request,task_kind:body.task_kind};
    if(body.ai_mode==='trial')payload.candidate={model:body.model,digest:body.digest,acknowledged:$('trial-ack').checked};
  }
  if(path==='/api/cancel'){target='/api/tasks/'+body.job_id+'/cancel';payload={};}
  if(path==='/api/pause'){target='/api/settings';payload={enabled:!body.paused};}
  if(path==='/api/models')target='/api/inventory';
  const options=payload===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-SB-CSRF':csrf},body:JSON.stringify(payload)};
  const controller=new AbortController(),deadline=setTimeout(()=>controller.abort(),REQUEST_TIMEOUT_MS);
  let response,data;
  try{
    response=await fetch(target,{credentials:'same-origin',cache:'no-store',...options,signal:controller.signal});
    data=await response.json();
    if(!data||typeof data!=='object'||Array.isArray(data)||
       (path==='/api/start'&&response.ok&&!data.error&&(typeof data.task_id!=='string'||!/^[a-f0-9]{32}$/.test(data.task_id))))throw new Error('Invalid service acknowledgement');
  }catch{
    const timedOut=controller.signal.aborted;
    const error=new Error(timedOut?'The local request timed out. Retry the connection to check the service.':response?`The local service returned an unreadable response (HTTP ${response.status}). Retry the connection.`:'The local service could not be reached. Check that the workbench is running, then retry the connection.');
    error.code=timedOut?'request_timeout':response?'unreadable_response':'connection_unavailable';error.uncertain=true;throw error;
  }finally{clearTimeout(deadline);}
  if(!response.ok||data.error){const error=new Error('The local request could not complete ('+(data.error||response.status)+'). Your source is unchanged.');error.code=data.error;error.uncertain=response.status>=500||data.error==='workbench_request_timeout';throw error;}
  if(path==='/api/state')return viewState(data);
  if(path==='/api/result')return viewJob(data);
  if(path==='/api/start')return {job_id:data.task_id,project_id:body.project_id,status:'running'};
  if(path==='/api/models'){
    if(data.state!=='connected')throw new Error('Local model inventory is unavailable. No model was loaded or downloaded.');
    return {models:data.models.map(m=>({model:m.name,digest:m.digest,quantization:'installed artifact'}))};
  }
  return data;
}
function renderCatalog() {
  const box=$('catalog');box.replaceChildren();
  for(const model of nativeState.catalog.models){
    const title=document.createElement('h3');title.textContent=model.title+' · '+model.publisher;box.append(title);
    const text=document.createElement('p');text.className='small muted';text.textContent='Published statistics: '+(model.stats.map(s=>s.name+': '+s.value).join('; ')||'not recorded')+'. Publisher setup differs from this installed artifact. No reviewed local trial is inferred.';box.append(text);
    const limits=document.createElement('p');limits.className='small muted';limits.textContent=model.limits;box.append(limits);
    if(model.source){const link=document.createElement('a');link.textContent='Primary publisher source';link.href=model.source;link.target='_blank';link.rel='noopener noreferrer';box.append(link);}
  }
  for(const profile of nativeState.policy.profiles){if(!profile.evaluation)continue;const p=document.createElement('p');p.className='small muted';const e=profile.evaluation;p.textContent=`Owner record: ${profile.id} · ${profile.task_kind} · ${profile.status} · ${Math.round(e.accuracy*100)}% across ${e.case_count} cases (${e.dataset_id}). ${profile.reason||'Live identity is checked on use.'} This is an owner declaration, not an authenticated certificate.`;box.append(p);}
}

function taskKind() { return document.querySelector('input[name="task-kind"]:checked')?.value || null; }
function selectedModel() { const option = $('model').selectedOptions[0]; return {model:option?.value || null,digest:option?.dataset.digest || null}; }
function mode() { return $('local-ai').checked ? $('ai-mode').value : 'off'; }
function modelView() {
  $('candidate-controls').hidden = $('ai-mode').value !== 'trial';
  const selected = selectedModel();
  // Include the enable state so off/on and A/B/A transitions revoke in-flight checks.
  const context = JSON.stringify([selected.model, selected.digest, $('local-ai').checked]);
  if(context!==modelCheckContext){modelCheckContext=context;$('trial-ack').checked=false;resetModelCheck();}
  $('model-identity').textContent = selected.model ? `Saved candidate · digest ${selected.digest} · ${$('model').selectedOptions[0]?.dataset.availability==='unavailable'?'unavailable or changed; explicitly choose an installed artifact.':$('model').selectedOptions[0]?.dataset.availability==='unknown'?'inventory unavailable; refresh or check again.':'availability checked only on refresh/run.'}` : 'No installed model selected.';
  $('mode-summary').textContent = settingsPending ? 'Saving Local AI choice…' : !$('local-ai').checked ? 'Exact evidence · Local AI off' : $('ai-mode').value === 'trial' ? 'Explicit candidate trial · unqualified' : 'Reviewed profiles only';
  readinessControls();
  $('model-help').textContent = state?.allow_candidate_trials ? 'Your selected candidate persists in this browser, including when Ollama is offline. Notes still require review.' : 'Candidate trials require the owner launch flag --allow-candidate-trials. Best tested uses reviewed profiles only.';
}
function draftStatus(text){if($('draft-status').textContent!==text)$('draft-status').textContent=text;}
function validDraftProject(){return state?.projects?.includes($('project').value)===true;}
function draftContext(){
  const projectValid=validDraftProject(),kindValid=taskKinds.includes(taskKind());
  $('project-help').classList.toggle('sr-only',projectValid&&kindValid);
  $('project-help').textContent=!projectValid
    ? `The saved project${draftProjectId?' “'+draftProjectId+'”':''} is unavailable. Choose an approved project for this draft.${kindValid?'':' Choose a task type too.'}`
    : !kindValid?'The saved task type is unavailable. Choose a task type for this draft.':"Only projects approved in the owner's launch configuration are available.";
}
function saveDraft(){
  if(preview)return;
  // Initial connection must resolve the saved context before replacing it.
  if(!draftInitialized){draftStatus('Draft kept in this page while the local session connects.');return;}
  if(validDraftProject())draftProjectId=$('project').value;
  try{
    localStorage.setItem('sb-workbench-draft',JSON.stringify({task:$('request').value,kind:taskKind(),project:draftProjectId}));
    draftStatus('Draft saved in this browser. Browser data clearing removes it; prepared briefs remain session-only.');
  }catch{draftStatus('Draft could not be saved in this browser. Keep this page open or copy your task text before leaving.');}
}
function restoreDraft(prefs){
  let draft=null,storageProblem=false;
  if(!preview)try{
    const raw=localStorage.getItem('sb-workbench-draft');
    if(raw!==null){const value=JSON.parse(raw);if(value&&typeof value.task==='string'&&value.task.length<=16384)draft=value;else storageProblem=true;}
  }catch{storageProblem=true;}
  // The draft owns its project/type; separate preferences may describe another task.
  // Preserve edits made while the first state request was pending, even without storage.
  if(draft&&!draftTouched.has('task'))$('request').value=draft.task;
  draftProjectId=draftTouched.has('project')?$('project').value:draft?(typeof draft.project==='string'?draft.project:''):prefs.project_id;
  if(!state.projects.includes(draftProjectId)){
    const choose=new Option('Choose a project for this draft','');choose.disabled=true;$('project').prepend(choose);$('project').value='';
  }else $('project').value=draftProjectId;
  const kind=draftTouched.has('kind')?taskKind():draft?draft.kind:prefs.task_kind;
  document.querySelectorAll('input[name="task-kind"]').forEach(input=>{input.checked=input.value===kind;});
  draftInitialized=true;draftContext();
  if(preview)draftStatus('Recorded preview. Drafts are not saved.');
  else if(draftTouched.size)saveDraft();
  else draftStatus(storageProblem?'Saved draft could not be read. New edits will replace it if browser storage is available.':draft?'Draft saved in this browser. Browser data clearing removes it; prepared briefs remain session-only.':'Task drafts are saved in this browser as you edit. Prepared briefs remain session-only.');
}
function preferences() { return {project_id:$('project').value, task_kind:taskKind(), ai_mode:mode(), ...selectedModel()}; }
async function savePreferences() { saveDraft();if(!draftInitialized)return;try { await api('/api/preferences', preferences()); } catch(error) { message(error.message, true); } }
function controls() {
  $('prepare').disabled = !!active || !state || !connected || settingsPending || !!preview || !validDraftProject() || !taskKinds.includes(taskKind());
  $('stop').disabled = !active?.job_id || !!preview;
  $('local-ai').disabled = !state || !connected || settingsPending || !!preview || !state.local_ai_allowed;
  $('local-ai').setAttribute('aria-busy',String(settingsPending));
  $('refresh-models').disabled = inventoryLoading || settingsPending || !connected || !!preview || !$('local-ai').checked;
  $('retry-connection').hidden = connected!==false || !!preview;
  $('retry-connection').disabled = !!sessionSync;
  $('progress').textContent = settingsPending ? 'Confirming Local AI with the local service…' : active?.pending ? 'Starting preparation…' : active&&!connected ? 'Job status is unknown — reconnect to check preparation.' : active ? 'Preparing evidence and bounded local notes…' : preview ? 'Recorded demo — open the local app to prepare a new task.' : '';
  renderCopyStatus();
  $('download').disabled = !pinned?.packet;
  readinessControls();
}
function renderHistory(recent) {
  const signature=JSON.stringify(recent)+pinned?.job_id;if(signature===historySignature)return;historySignature=signature;
  const parent = $('recent-list'); parent.replaceChildren();
  if (!recent.length) { const p=document.createElement('p'); p.className='small muted'; p.textContent='Your completed briefs will appear here.'; parent.append(p); return; }
  for (const item of recent) {
    const button=document.createElement('button'); button.type='button'; button.className='recent-button'; button.classList.toggle('active', pinned?.job_id===item.job_id);
    const title=document.createElement('strong'); title.textContent=item.request_preview || item.project_id;
    const date=document.createElement('time'); date.dateTime=item.created_at; date.textContent=`${new Date(item.created_at).toLocaleDateString(undefined,{month:'short',day:'numeric'})} · ${item.status}`;
    button.append(title,date);
    if(item.status==='expired'){button.disabled=true;date.textContent+=' · prepare again to refresh';}
    button.addEventListener('click',async()=>{
      const revision=++pinRevision;
      try {
        const job=await api('/api/result',{project_id:item.project_id,job_id:item.job_id});
        if(revision!==pinRevision)return;
        if(job.packet){pinned=job;renderBrief(!!active);renderHistory(state.recent);showWorkspace();$('brief-title').focus();message('Showing this captured brief. Your task draft is unchanged.');}
        else message(`Job ${job.status}. ${job.error?.message || 'No completed packet is available.'}`,true);
        controls();
      }catch(error){if(revision===pinRevision)message(error.message,true);}
    });
    parent.append(button);
  }
}
function renderBrief(previous = false) {
  if (!pinned?.packet) return;
  $('handoff-copy').hidden=false;
  const text=handoffText(pinned);
  if($('handoff-text').value!==text)$('handoff-text').value=text;
  const packet=pinned.packet; $('brief-title').textContent=previous ? 'Previous brief — current task has no new result' : pinned.status==='incomplete' ? 'Evidence incomplete — review the gaps' : 'Evidence prepared — diagnosis open';
  $('brief-subtitle').textContent=`${pinned.project_id==='starter-demo'?'Synthetic demo':pinned.project_id} · ${packet.task_kind || 'code'} · ${new Date(pinned.completed_at).toLocaleDateString()}`;
  $('job-identity').textContent=`Project: ${pinned.project_id} · Job: ${pinned.job_id} · Started: ${packet.started_at}`;
  $('original-request').textContent=packet.original_request; $('brief-details').hidden=false;
  $('route-reason').textContent=packet.routing?.reason || 'Exact-source preparation only.';
  $('worker-status').hidden=packet.routing?.status!=='abstained';$('worker-status').textContent=packet.routing?.status==='abstained'?`Local notes withheld: ${packet.routing.reason}`:'';
  $('evidence-count').textContent=`${packet.evidence.length} excerpt${packet.evidence.length===1?'':'s'}`;
  const grid=$('evidence'); grid.replaceChildren();
  for(const item of packet.evidence){
    const article=document.createElement('article'); article.className='source'; const header=document.createElement('header');
    const icon=document.createElement('img'); icon.src='/icons/document.svg'; icon.alt=''; const name=document.createElement('strong'); name.textContent=item.path;
    const range=document.createElement('span'); range.className='source-meta'; range.textContent=`Lines ${item.start_line}–${item.end_line}`; header.append(icon,name,range);
    const pre=document.createElement('pre'); pre.tabIndex=0;pre.setAttribute('role','region');pre.setAttribute('aria-label',`Exact source from ${item.path}`);
    const lines=item.content.split('\n'); if(item.content.endsWith('\n')) lines.pop();
    lines.forEach((text,index)=>{const row=document.createElement('span'); row.className='line'; const number=document.createElement('span'); number.className='line-number'; number.setAttribute('aria-hidden','true'); number.textContent=String(item.start_line+index); const code=document.createElement('code'); code.textContent=text; row.append(number,code); pre.append(row);});
    const hash=document.createElement('div'); hash.className='hash'; hash.textContent=`SHA-256 ${item.file_sha256}`; article.append(header,pre,hash); grid.append(article);
  }
  if(!packet.evidence.length){ const empty=document.createElement('div'); empty.className='empty'; const p=document.createElement('p');p.textContent='No source was captured. Review the gaps and clarify the request.';empty.append(p);grid.append(empty); }
  const discovery=packet.receipt.discovery; $('scan-limits').textContent=discovery?`Bounded lexical scan: ${discovery.files_read} files read. Cutoffs: ${discovery.cutoffs.join(', ')||'none reached'}. Exclusions: ${JSON.stringify(discovery.refusals)}. This is not an exhaustive review.`:'';
  $('gaps-section').hidden=!packet.gaps.length&&!discovery; $('gaps').replaceChildren();
  for(const gap of packet.gaps){const li=document.createElement('li');li.textContent=`${gap.selection?.path?gap.selection.path+' — ':''}${gap.code}: ${gap.message}`;$('gaps').append(li);}
  const notes=packet.model_notes; $('notes-section').hidden=!notes; $('notes').replaceChildren();$('uncertainties').replaceChildren();
  if(notes){ for(const item of notes.notes){const li=document.createElement('li');li.textContent=`${item.text}\nEvidence: ${item.evidence_ids.map(id=>packet.evidence.find(e=>e.evidence_id===id)?.path||id).join(', ')}`;$('notes').append(li);} for(const text of notes.uncertainties){const li=document.createElement('li');li.textContent=text;$('uncertainties').append(li);} }
  $('receipt-section').hidden=false;$('receipt').textContent=JSON.stringify({job_id:pinned.job_id,routing:packet.routing,usage:packet.receipt},null,2);$('limitations').replaceChildren();for(const text of packet.limitations){const li=document.createElement('li');li.textContent=text;$('limitations').append(li);} controls();
}
async function refreshState(initial=false){
  if(settingsPending)return;
  const revision=++stateRevision;
  let next;
  try{next=await api('/api/state');}
  catch(error){if(revision!==stateRevision||settingsPending)return;throw error;}
  if(revision!==stateRevision||settingsPending)return;
  state=next;nativeState=next.native;csrf=next.csrf;connected=true;
  $('version').textContent=`v${state.version} · ${state.shared_native?'Shared coordinator':'Local session'}`;
  $('connection-status').textContent='Local session connected';
  $('local-ai-retention').textContent=nativeState.local_ai_preference_persistent?'Local AI choice is saved on this computer. Briefs expire with the session.':'Local AI choice and briefs last only for this diagnostic session.';
  if(initial){
    renderCatalog();
    $('project').replaceChildren();for(const id of state.projects){const option=new Option(id==='starter-demo'?'Synthetic demo':id,id);$('project').append(option);}
    const prefs=state.preferences;restoreDraft(prefs);
    $('local-ai').checked=prefs.ai_mode!=='off'&&!state.local_ai_paused; $('ai-mode').value=prefs.ai_mode==='trial'?'trial':'best';
    if(prefs.model){const saved=new Option(`${prefs.model} — saved candidate`,prefs.model);saved.dataset.digest=prefs.digest;$('model').append(saved);$('model').value=prefs.model;}
    $('profile-identity').textContent=`Pipeline SHA-256: ${state.pipeline_sha256}\nNo hardware or accuracy certificate is implied.`;
    if(state.active) active=state.active;
    const latest=state.recent.find(item=>item.status==='prepared'||item.status==='incomplete');if(latest){try{pinned=await api('/api/result',{project_id:latest.project_id,job_id:latest.job_id});renderBrief(!!active);}catch(error){message(error.message,true);}}
  }
  if(!initial)$('local-ai').checked=!state.local_ai_paused;renderHistory(state.recent);modelView();controls();
}
async function poll(){
  if(polling||!active?.job_id)return;polling=true;
  try {const job=await api('/api/result',{project_id:active.project_id,job_id:active.job_id});if(job.status!=='running'){
    active=null;++pinRevision;if(job.packet){pinned=job;renderBrief(false);message(job.packet.routing?.status==='abstained'?`Local model notes were withheld. ${job.packet.routing.reason}`:job.status==='incomplete'?'Preparation finished with source gaps.':'Evidence prepared. Review the source and gaps, then copy the brief.');}else{if(pinned)renderBrief(true);message(`${job.status==='cancelled'?'Preparation stopped.':'Preparation failed.'} ${job.error?.message||'No new completed brief is available.'}`,true);}await refreshState();
  }}catch(error){connectionFailed();if(error.code==='unknown_or_expired_task'){active=null;if(pinned)renderBrief(true);message('This task has expired from the local session. Your pinned brief remains available; prepare a new task for fresh evidence.',true);}else message(`Connection interrupted. ${error.message} Job status is unknown until reconnected.`,true);}finally{polling=false;controls();}
}
$('task-form').addEventListener('submit',async(event)=>{event.preventDefault();if(active||settingsPending||!connected||!state||preview)return;try{
  if(!validDraftProject()||!taskKinds.includes(taskKind()))throw new Error('Choose an approved project and task type for this draft.');
  if(!$('request').value.trim())throw new Error('Describe the task first.');if(mode()==='trial'&&!state.allow_candidate_trials)throw new Error('Relaunch with --allow-candidate-trials to enable explicit trials.');if(mode()==='trial'&&(!$('trial-ack').checked||!selectedModel().model))throw new Error('Choose an installed candidate and acknowledge that its notes are unverified.');
  const params={...preferences(),request:$('request').value};++pinRevision;++stateRevision;active={pending:true};controls();if(pinned)renderBrief(true);message(pinned?'Preparing the current task. The earlier brief stays pinned to its original job.':'Preparing exact evidence for this task.');
  const job=await api('/api/start',params);active=job;await savePreferences();await poll();
}catch(error){
  active=null;
  if(error.uncertain){
    connectionFailed();message(`Preparation start was not confirmed. ${error.message} Checking the local session…`,true);
    // An older background snapshot cannot establish what happened to this start.
    if(sessionSync)await sessionSync;
    await syncSession(false);
    message(`Preparation start was not confirmed. ${error.message} The service may have accepted this task. Check Recent briefs before starting again. No start request was retried.`,true);
  }else message(error.message,true);
  controls();
}});
$('request').addEventListener('input',()=>{draftTouched.add('task');saveDraft();});
$('stop').addEventListener('click',async()=>{if(!active?.job_id)return;try{await api('/api/cancel',{project_id:active.project_id,job_id:active.job_id});await poll();}catch(error){message(error.message,true);}});
$('local-ai').addEventListener('change',async()=>{
  if(settingsPending||!connected||!state||preview)return;
  const requested=$('local-ai').checked;
  settingsPending=true;++stateRevision;modelView();controls();
  try{
    const result=await api('/api/pause',{paused:!requested});
    $('local-ai').checked=result.enabled===true;state.local_ai_paused=!$('local-ai').checked;
    await savePreferences();
    if($('local-ai').checked){$('model-details').hidden=false;$('model-details-toggle').setAttribute('aria-expanded','true');}
    message(requested&&!result.enabled?'Local AI is disabled in this launch configuration. Evidence-only preparation remains available.':result.enabled?'Local AI is on. Model use still requires an eligible profile or an explicit candidate trial.':'Local AI is off. New tasks will prepare exact evidence only.');
  }catch(error){
    connected=false;$('local-ai').checked=!state.local_ai_paused;
    message(`Local AI change was not confirmed. ${error.message}`,true);
  }finally{
    settingsPending=false;
    try{await refreshState();}catch{connectionFailed();}
    modelView();controls();
  }
});
$('model-details-toggle').addEventListener('click',()=>{const open=$('model-details').hidden;$('model-details').hidden=!open;$('model-details-toggle').setAttribute('aria-expanded',String(open));});
$('ai-mode').addEventListener('change',()=>{modelView();savePreferences();});$('model').addEventListener('change',()=>{modelView();savePreferences();});
$('project').addEventListener('change',()=>{draftTouched.add('project');draftContext();savePreferences();controls();});
document.querySelectorAll('input[name="task-kind"]').forEach(input=>input.addEventListener('change',()=>{draftTouched.add('kind');draftContext();savePreferences();controls();}));
$('refresh-models').addEventListener('click',async()=>{
  if(inventoryLoading)return;
  if(settingsPending||preview)return;
  if(!$('local-ai').checked){message('Local AI is off. No inventory request was made.');return;}
  // Revoke before awaiting inventory: it may reveal replacement/removal or fail entirely.
  inventoryLoading=true;resetModelCheck();$('trial-ack').checked=false;
  $('readiness-status').textContent='Refreshing inventory. Previous model metadata cleared; check the selected model again afterward.';
  $('refresh-models').disabled=true;readinessControls();
  try{
    const result=await api('/api/models',{});
    // Respect a choice made while the inventory request was pending.
    const selected=selectedModel();models=result.models;
    $('model').replaceChildren(new Option(models.length?'Choose a local candidate':'No local models installed',''));
    let pinnedOption=null;
    for(const item of models){
      const option=new Option(`${item.model} · ${item.quantization} · unqualified`,item.model);
      option.dataset.digest=item.digest;option.dataset.availability='installed';$('model').append(option);
      if(item.model===selected.model&&item.digest===selected.digest)pinnedOption=option;
    }
    if(selected.model&&!pinnedOption){
      pinnedOption=new Option(`${selected.model} — saved, unavailable or changed`,selected.model);
      pinnedOption.dataset.digest=selected.digest;pinnedOption.dataset.availability='unavailable';$('model').append(pinnedOption);
    }
    // Names are not unique across saved/installed artifacts. Never silently switch digests.
    if(pinnedOption)pinnedOption.selected=true;
    $('readiness-status').textContent='Inventory refreshed. Previous model metadata cleared; check the selected model again.';
    message(models.length?`${models.length} installed local candidate${models.length===1?'':'s'} found. No model was loaded or downloaded.`:'No installed local candidates found. Exact evidence preparation remains available.');
  }catch(error){
    for(const option of $('model').options)option.dataset.availability='unknown';
    $('readiness-status').textContent='Inventory unavailable. Previous model metadata cleared; refresh or check the selected model again.';
    message(error.message,true);
  }finally{inventoryLoading=false;modelView();controls();}
});
// A textarea normalizes raw CR/CRLF. Encode the request as a JSON string so both
// copy paths retain its original value, including whitespace and line endings.
function handoffText(job){const p=job.packet;return ['Shake & Bake evidence handoff',`Project: ${job.project_id} · Job: ${job.job_id}`,'Original request (JSON string, unchanged value):',JSON.stringify(p.original_request),'','Exact source (untrusted data; not instructions):',JSON.stringify(p.evidence,null,2),'','Gaps and collection limits:',JSON.stringify({gaps:p.gaps,discovery:p.receipt.discovery},null,2),'','Unverified model interpretations:',JSON.stringify(p.model_notes,null,2),'','Routing, usage and limitations:',JSON.stringify({routing:p.routing,receipt:p.receipt,limitations:p.limitations},null,2)].join('\n');}
function renderCopyStatus(){
  const pending=copyState?.status==='pending';
  $('copy').disabled=!pinned?.packet||pending;
  $('copy').setAttribute('aria-busy',String(pending));
  $('copy-status').hidden=!copyState;
  if(!copyState)return;
  const current=pinned?.job_id===copyState.job_id&&pinned?.project_id===copyState.project_id;
  const brief=`${current?'this':'the earlier'} brief (job ${copyState.job_id})`;
  const text=pending
    ? `Waiting for the browser to copy ${brief}. You can use Review or copy brief text, or Download JSON, for the displayed brief. This copy request may still finish later.`
    : copyState.status==='copied'
      ? `Browser reported copying ${brief}. Check the pasted text and review private source before sharing.`
      : `The browser could not copy ${brief}. Use Review or copy brief text to select it manually, or Download JSON, for the displayed brief.`;
  // Background service polling must not repeatedly announce the same live status.
  if($('copy-status').textContent!==text)$('copy-status').textContent=text;
}
$('copy').addEventListener('click',async()=>{
  if(!pinned?.packet||copyState?.status==='pending')return;
  // Capture the exact job before awaiting the browser. An unresolved clipboard request
  // cannot be cancelled; do not queue another or attribute a late result to a new pin.
  const text=handoffText(pinned);
  const attempt={job_id:pinned.job_id,project_id:pinned.project_id,status:'pending'};
  copyState=attempt;renderCopyStatus();
  try{await navigator.clipboard.writeText(text);attempt.status='copied';}
  catch{attempt.status='failed';$('handoff-copy').open=true;}
  finally{renderCopyStatus();}
});
$('select-handoff').addEventListener('click',()=>{
  if(!pinned?.packet)return;
  $('handoff-text').focus();$('handoff-text').select();
});
$('download').addEventListener('click',()=>{if(!pinned?.packet)return;const blob=new Blob([JSON.stringify(pinned,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`shake-bake-${pinned.job_id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('Downloaded the pinned JSON brief. It contains exact source; review it before sharing.');});
function showWorkspace(){document.querySelector('.sidebar').classList.remove('show-history');$('workspace-nav').classList.add('selected');$('workspace-nav').setAttribute('aria-pressed','true');$('history-nav').classList.remove('selected');$('history-nav').setAttribute('aria-pressed','false');}
$('history-nav').addEventListener('click',()=>{document.querySelector('.sidebar').classList.add('show-history');$('history-nav').classList.add('selected');$('history-nav').setAttribute('aria-pressed','true');$('workspace-nav').classList.remove('selected');$('workspace-nav').setAttribute('aria-pressed','false');$('recent-section').scrollIntoView({block:'nearest'});});
$('workspace-nav').addEventListener('click',()=>{showWorkspace();$('request').focus();});
function connectionFailed(){connected=false;$('connection-status').textContent='Local session unavailable — retry or reload this page.';controls();}
function syncSession(announce=true){
  if(settingsPending)return Promise.resolve();
  if(sessionSync)return sessionSync;
  const wasConnected=connected;
  sessionSync=(async()=>{
    try{await refreshState(!state);if(!active&&state?.active){active=state.active;controls();}if(active?.job_id)await poll();if(announce&&!wasConnected&&connected)message('Local session reconnected. Your task draft and pinned brief are unchanged.');}
    catch{connectionFailed();}
  })().finally(()=>{sessionSync=null;controls();});
  controls();return sessionSync;
}
$('retry-connection').addEventListener('click',async()=>{await syncSession();if(connected)message('Local session reconnected. Your task draft and pinned brief are unchanged.');else message('The local session is still unavailable. Check the workbench is running. If it restarted, save any pinned brief, then reload this page.',true);});
async function initialize(){
  clearInterval(timer);clearInterval(serviceTimer);controls();
  try{await refreshState(true);if(preview){pinned=viewJob(preview.result);renderBrief(false);message('Recorded inert demo. New tasks require the local app.');}}
  catch(error){message(error.message,true);connectionFailed();}
  if(!preview){timer=setInterval(()=>{if(active?.job_id)poll();},600);serviceTimer=setInterval(()=>{if(!active||!connected)syncSession();},3000);}
}

$('today').textContent=new Date().toLocaleDateString(undefined,{month:'long',day:'numeric',year:'numeric'});initialize();

function memoryText(value){return typeof value==='number'?`${(value/1073741824).toFixed(1)} GiB`:'Not detected';}
function facts(id,entries){const list=$(id);list.replaceChildren();for(const [name,value]of entries){const term=document.createElement('dt'),detail=document.createElement('dd');term.textContent=name;detail.textContent=value;list.append(term,detail);}}
function readinessControls(){
  $('check-computer').disabled=readinessRunning||!!active||!state||!!preview||settingsPending||!connected;
  $('check-model').disabled=inventoryLoading||readinessRunning||!!active||!state||!!preview||settingsPending||!connected||!$('local-ai').checked||!selectedModel().model;
}
function resetModelCheck(){modelCheckRevision++;facts('model-facts',[['Model','No check for this selection']]);$('readiness-status').textContent='Selection changed. Check this model again before relying on its metadata.';}
$('check-computer').addEventListener('click',async()=>{
  if(readinessRunning)return;readinessRunning=true;readinessControls();$('readiness-status').textContent='Reading local capability metadata…';
  try{const r=await api('/api/computer',{});facts('computer-facts',[
    ['System',r.system+' · '+r.machine],['CPU',r.cpu_model||'Not detected'],['Available CPU threads',String(r.available_logical_cpus??'Not detected')],
    ['Physical RAM',memoryText(r.physical_ram_bytes)],['Available memory now',memoryText(r.available_memory_bytes)],['Observed container limit',memoryText(r.container_memory_limit_bytes)],
    ['GPU / VRAM',r.gpus.length?r.gpus.map(g=>`${g.vendor} ${g.device_id} · ${g.driver||'driver unknown'} · ${memoryText(g.vram_total_bytes)}`).join('; '):'Not detected; CPU-only hardware is not established'],
    ['Observed',new Date(r.observed_at).toLocaleString()],['Model fit / peak memory','Not measured']]);$('readiness-status').textContent='Computer metadata checked without contacting Ollama. Memory is a point-in-time estimate for this process environment.';
  }catch(error){facts('computer-facts',[['Current check','Unavailable']]);$('readiness-status').textContent=error.message;}finally{readinessRunning=false;readinessControls();}
});
$('check-model').addEventListener('click',async()=>{
  if(readinessRunning||inventoryLoading||settingsPending||!connected||preview)return;modelView();const selection=selectedModel(),key=JSON.stringify(selection),revision=modelCheckRevision;if(!selection.model||!$('local-ai').checked)return;
  readinessRunning=true;readinessControls();facts('model-facts',[['Current check','Checking selected model…']]);$('readiness-status').textContent='Checking the pinned digest, runtime and model metadata. No source or generation is sent.';
  const current=()=>revision===modelCheckRevision&&key===JSON.stringify(selectedModel())&&$('local-ai').checked&&!inventoryLoading;
  try{const r=await api('/api/model-check',selection);if(!current())return;
    facts('model-facts',[['Model',r.model],['Reported digest',r.reported_digest],['Ollama runtime',r.runtime_version],['Reported quantization',r.reported_details.quantization_level||'Not reported'],
      ['Reported parameters',r.reported_details.parameter_size||'Not reported'],['Reported context capacity',r.reported_context_length===null?'Not reported':r.reported_context_length.toLocaleString()+' tokens'],
      ['Capabilities',r.reported_capabilities?.join(', ')||'Not reported'],['Thinking can be disabled',r.reported_thinking_can_disable===null?'Not reported':r.reported_thinking_can_disable?'Reported yes':'Reported no'],
      ['Requested preparation',`${r.requested_configuration.options.num_ctx.toLocaleString()} context / ${r.requested_configuration.options.num_predict} output tokens · thinking off · ${r.requested_configuration.deadline_seconds}s deadline`],
      ['Local task accuracy','Unqualified; readiness is not an accuracy trial'],['Checked',new Date(r.observed_at).toLocaleString()]]);
    $('readiness-status').textContent='Reported model identity and runtime stayed stable during this check. Actual memory fit and task accuracy remain unmeasured.';
  }catch(error){if(current()){facts('model-facts',[['Current check','Unavailable or identity changed']]);$('readiness-status').textContent=error.message;}}finally{readinessRunning=false;readinessControls();}
});
