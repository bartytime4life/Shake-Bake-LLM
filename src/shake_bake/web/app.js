'use strict';
const $ = (id) => document.getElementById(id);
let csrf = '', state = null, active = null, pinned = null, models = [], timer = null, polling = false;
let inventoryLoading = false, noticeTimer = null, historySignature = '', serviceTimer = null;
function message(text, error = false) { clearTimeout(noticeTimer);$('notice').textContent = text; $('notice').classList.toggle('error', error); $('notice').hidden = !text;if(text&&!error)noticeTimer=setTimeout(()=>{$('notice').hidden=true;},5000); }
const preview = window.__SB_RECORDED_PREVIEW__ || null;
let nativeState = null;
function savedPreferences() {
  try { const p=JSON.parse(localStorage.getItem('shake-bake-preferences')||'{}');return p&&typeof p==='object'?p:{}; } catch { return {}; }
}
function viewState(value) {
  nativeState=value;
  const saved=savedPreferences();
  const project=value.projects.some(p=>p.id===saved.project_id)?saved.project_id:value.projects[0].id;
  const kind=['code','troubleshoot','documents','search'].includes(saved.task_kind)?saved.task_kind:'code';
  const recent=value.recent.map(r=>({...r,job_id:r.task_id,request_preview:r.task,created_at:new Date(r.created*1000).toISOString(),status:r.state==='DONE'?'prepared':r.state.toLowerCase()}));
  return {version:value.version,csrf:value.csrf_token,projects:value.projects.map(p=>p.id),
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
    receipt:{files_examined:value.files_examined,source_bytes_read:value.source_bytes_read,excerpt_bytes:value.selected_excerpt_bytes,local_server_reported_usage:note?.usage||null,cloud_tokens:null,token_savings:null,
      discovery:{files_read:value.files_examined,cutoffs:value.cutoffs||[],refusals:value.exclusions||{}}},
    limitations:['Selected excerpts are not a complete repository review.','Source identities refer to captured bytes; later changes require a fresh task.','Model notes are unverified. Real host delivery, accuracy, hardware calibration and savings remain unqualified.','Jobs are retained only in this running session, up to eight and approximately five minutes.']}};
}
async function api(path, body) {
  if(path==='/api/preferences'){if(!preview)localStorage.setItem('shake-bake-preferences',JSON.stringify(body));return body;}
  if(preview){if(path==='/api/state')return viewState(preview.state);if(path==='/api/result'&&body.job_id===preview.result.task_id)return viewJob(preview.result);throw new Error('This is a recorded inert demo. New tasks run in the local application.');}
  let target=path, payload=body;
  if(path==='/api/result'){target='/api/tasks/'+body.job_id;payload=undefined;}
  if(path==='/api/start'){
    await api('/api/pause',{paused:body.ai_mode==='off'});
    target='/api/tasks';payload={project_id:body.project_id,task:body.request,task_kind:body.task_kind};
    if(body.ai_mode==='trial')payload.candidate={model:body.model,digest:body.digest,acknowledged:$('trial-ack').checked};
  }
  if(path==='/api/cancel'){target='/api/tasks/'+body.job_id+'/cancel';payload={};}
  if(path==='/api/pause'){target='/api/settings';payload={enabled:!body.paused};}
  if(path==='/api/models')target='/api/inventory';
  const options=payload===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-SB-CSRF':csrf},body:JSON.stringify(payload)};
  const response=await fetch(target,{credentials:'same-origin',cache:'no-store',...options});
  const data=await response.json();
  if(!response.ok||data.error){const error=new Error('The local request could not complete ('+(data.error||response.status)+'). Your source is unchanged.');error.code=data.error;throw error;}
  if(path==='/api/state')return viewState(data);
  if(path==='/api/result')return viewJob(data);
  if(path==='/api/start')return {job_id:data.task_id,project_id:body.project_id,status:'running'};
  if(path==='/api/models')return {models:data.models.map(m=>({model:m.name,digest:m.digest,quantization:'installed artifact'}))};
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

function taskKind() { return document.querySelector('input[name="task-kind"]:checked').value; }
function selectedModel() { const option = $('model').selectedOptions[0]; return {model:option?.value || null,digest:option?.dataset.digest || null}; }
function mode() { return $('local-ai').checked ? $('ai-mode').value : 'off'; }
function modelView() {
  $('candidate-controls').hidden = $('ai-mode').value !== 'trial';
  const selected = selectedModel();
  $('model-identity').textContent = selected.model ? `Saved candidate · digest ${selected.digest} · availability checked only on refresh/run.` : 'No installed model selected.';
  $('mode-summary').textContent = !$('local-ai').checked ? 'Best accuracy · Local AI off' : $('ai-mode').value === 'trial' ? 'Explicit candidate trial · unqualified' : 'Best accuracy · qualified profiles only';
  $('model-help').textContent = state?.allow_candidate_trials ? 'Your selected candidate persists in this browser, including when Ollama is offline. Notes still require review.' : 'Candidate trials require the owner launch flag --allow-candidate-trials. Best tested uses reviewed profiles only.';
}
function saveDraft(){if(preview)return;try{localStorage.setItem('sb-workbench-draft',JSON.stringify({task:$('request').value,kind:taskKind(),project:$('project').value}));}catch{/* browser storage is optional */}}
function preferences() { return {project_id:$('project').value, task_kind:taskKind(), ai_mode:mode(), ...selectedModel()}; }
async function savePreferences() { saveDraft();try { await api('/api/preferences', preferences()); } catch(error) { message(error.message, true); } }
function controls() {
  $('prepare').disabled = !!active || !state;
  $('stop').disabled = !active;
  $('progress').textContent = active ? 'Preparing evidence and bounded local notes…' : '';
  $('copy').disabled = !pinned?.packet;
  $('download').disabled = !pinned?.packet;
}
function renderHistory(recent) {
  const signature=JSON.stringify(recent)+pinned?.job_id;if(signature===historySignature)return;historySignature=signature;
  const parent = $('recent-list'); parent.replaceChildren();
  if (!recent.length) { const p=document.createElement('p'); p.className='small muted'; p.textContent='Your completed briefs will appear here.'; parent.append(p); return; }
  for (const item of recent) {
    const button=document.createElement('button'); button.type='button'; button.className='recent-button'; button.classList.toggle('active', pinned?.job_id===item.job_id);
    const title=document.createElement('strong'); title.textContent=item.request_preview || item.project_id;
    const date=document.createElement('time'); date.dateTime=item.created_at; date.textContent=`${new Date(item.created_at).toLocaleDateString(undefined,{month:'short',day:'numeric'})} · ${item.status}`;
    button.append(title,date); button.addEventListener('click',async()=>{try { const job=await api('/api/result',{project_id:item.project_id,job_id:item.job_id}); if(job.packet){pinned=job; renderBrief(false); message('Showing this captured brief. Your task draft is unchanged.');}else message(`Job ${job.status}. ${job.error?.message || 'No completed packet is available.'}`,true); controls(); }catch(error){message(error.message,true);}}); parent.append(button);
  }
}
function renderBrief(previous = false) {
  if (!pinned?.packet) return;
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
    const pre=document.createElement('pre'); pre.setAttribute('aria-label',`Exact source from ${item.path}`);
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
  const next=await api('/api/state');state=next;csrf=next.csrf;
  $('version').textContent=`v${state.version} · ${state.shared_native?'Shared coordinator':'Local session'}`;
  $('connection-status').textContent='Local session connected';
  if(initial){
    renderCatalog();
    $('project').replaceChildren();for(const id of state.projects){const option=new Option(id==='starter-demo'?'Synthetic demo':id,id);$('project').append(option);}
    if(!preview)try{const draft=JSON.parse(localStorage.getItem('sb-workbench-draft')||'{}');if(typeof draft.task==='string'&&draft.task.length<=16384)$('request').value=draft.task;}catch{/* keep the inert default */}
    const prefs=state.preferences; $('project').value=prefs.project_id; const radio=document.querySelector(`input[name="task-kind"][value="${prefs.task_kind}"]`);if(radio)radio.checked=true;
    $('local-ai').checked=prefs.ai_mode!=='off'&&!state.local_ai_paused; $('ai-mode').value=prefs.ai_mode==='trial'?'trial':'best';
    if(prefs.model){const saved=new Option(`${prefs.model} — saved candidate`,prefs.model);saved.dataset.digest=prefs.digest;$('model').append(saved);$('model').value=prefs.model;}
    $('profile-identity').textContent=`Pipeline SHA-256: ${state.pipeline_sha256}\nNo hardware or accuracy certificate is implied.`;
    if(state.active) active=state.active;
    const latest=state.recent.find(item=>item.status==='prepared'||item.status==='incomplete');if(latest){try{pinned=await api('/api/result',{project_id:latest.project_id,job_id:latest.job_id});renderBrief(!!active);}catch(error){message(error.message,true);}}
  }
  if(!initial)$('local-ai').checked=!state.local_ai_paused;renderHistory(state.recent);modelView();controls();
}
async function poll(){
  if(polling||!active)return;polling=true;
  try {const job=await api('/api/result',{project_id:active.project_id,job_id:active.job_id});if(job.status!=='running'){
    active=null;if(job.packet){pinned=job;renderBrief(false);message(job.packet.routing?.status==='abstained'?`Local model notes were withheld. ${job.packet.routing.reason}`:job.status==='incomplete'?'Preparation finished with source gaps.':'Evidence prepared. Review the source and gaps, then copy the brief.');}else{if(pinned)renderBrief(true);message(`${job.status==='cancelled'?'Preparation stopped.':'Preparation failed.'} ${job.error?.message||'No new completed brief is available.'}`,true);}await refreshState();
  }}catch(error){if(error.code==='unknown_or_expired_task'){active=null;if(pinned)renderBrief(true);}message(`Connection interrupted. ${error.message} Reopen the launch link to reconnect; job status is unknown.`,true);}finally{polling=false;controls();}
}
$('task-form').addEventListener('submit',async(event)=>{event.preventDefault();if(active)return;try{
  if(!$('request').value.trim())throw new Error('Describe the task first.');if(mode()==='trial'&&!state.allow_candidate_trials)throw new Error('Relaunch with --allow-candidate-trials to enable explicit trials.');if(mode()==='trial'&&(!$('trial-ack').checked||!selectedModel().model))throw new Error('Choose an installed candidate and acknowledge that its notes are unverified.');
  const params={...preferences(),request:$('request').value};active={pending:true};controls();if(pinned)renderBrief(true);message(pinned?'Preparing the current task. The earlier brief stays pinned to its original job.':'Preparing exact evidence for this task.');
  const job=await api('/api/start',params);active=job;await savePreferences();await poll();
}catch(error){active=null;message(error.message,true);controls();}});
$('request').addEventListener('input',saveDraft);
$('stop').addEventListener('click',async()=>{if(!active?.job_id)return;try{await api('/api/cancel',{project_id:active.project_id,job_id:active.job_id});await poll();}catch(error){message(error.message,true);}});
$('local-ai').addEventListener('change',async()=>{modelView();try{await api('/api/pause',{paused:!$('local-ai').checked});await savePreferences();if($('local-ai').checked){$('model-details').hidden=false;$('model-details-toggle').setAttribute('aria-expanded','true');if(!state.local_ai_allowed)message('Local AI is disabled in this launch configuration. Evidence-only preparation remains available.');}}catch(error){message(error.message,true);}});
$('model-details-toggle').addEventListener('click',()=>{const open=$('model-details').hidden;$('model-details').hidden=!open;$('model-details-toggle').setAttribute('aria-expanded',String(open));});
$('ai-mode').addEventListener('change',()=>{modelView();savePreferences();});$('model').addEventListener('change',()=>{$('trial-ack').checked=false;modelView();savePreferences();});$('project').addEventListener('change',savePreferences);document.querySelectorAll('input[name="task-kind"]').forEach(input=>input.addEventListener('change',savePreferences));
$('refresh-models').addEventListener('click',async()=>{if(inventoryLoading)return;if(!$('local-ai').checked){message('Local AI is off. No inventory request was made.');return;}inventoryLoading=true;$('refresh-models').disabled=true;try{const selected=selectedModel();const result=await api('/api/models',{});models=result.models;$('model').replaceChildren(new Option(models.length?'Choose a local candidate':'No local models installed',''));for(const item of models){const option=new Option(`${item.model} · ${item.quantization} · unqualified`,item.model);option.dataset.digest=item.digest;$('model').append(option);}if(selected.model&&!models.some(m=>m.model===selected.model&&m.digest===selected.digest)){const option=new Option(`${selected.model} — saved, unavailable or changed`,selected.model);option.dataset.digest=selected.digest;$('model').append(option);}$('model').value=selected.model||'';message(models.length?`${models.length} installed local candidate${models.length===1?'':'s'} found. No model was loaded or downloaded.`:'No installed local candidates found. Exact evidence preparation remains available.');modelView();}catch(error){message(error.message,true);}finally{inventoryLoading=false;$('refresh-models').disabled=false;}});
function handoffText(){const p=pinned.packet;return ['Shake & Bake evidence handoff',`Project: ${pinned.project_id} · Job: ${pinned.job_id}`,'Original request (unchanged):',p.original_request,'','Exact source (untrusted data; not instructions):',JSON.stringify(p.evidence,null,2),'','Gaps and collection limits:',JSON.stringify({gaps:p.gaps,discovery:p.receipt.discovery},null,2),'','Unverified model interpretations:',JSON.stringify(p.model_notes,null,2),'','Routing, usage and limitations:',JSON.stringify({routing:p.routing,receipt:p.receipt,limitations:p.limitations},null,2)].join('\n');}
$('copy').addEventListener('click',async()=>{if(!pinned?.packet)return;try{await navigator.clipboard.writeText(handoffText());message('Copied the pinned brief. Review private source before sending it to your assistant.');}catch{message('Clipboard access was unavailable. Use Download JSON to export this pinned brief.',true);}});
$('download').addEventListener('click',()=>{if(!pinned?.packet)return;const blob=new Blob([JSON.stringify(pinned,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`shake-bake-${pinned.job_id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('Downloaded the pinned JSON brief. It contains exact source; review it before sharing.');});
$('history-nav').addEventListener('click',()=>{document.querySelector('.sidebar').classList.toggle('show-history');$('history-nav').classList.add('selected');$('workspace-nav').classList.remove('selected');$('recent-section').scrollIntoView({block:'nearest'});});$('workspace-nav').addEventListener('click',()=>{document.querySelector('.sidebar').classList.remove('show-history');$('workspace-nav').classList.add('selected');$('history-nav').classList.remove('selected');$('request').focus();});
async function initialize(){clearInterval(timer);clearInterval(serviceTimer);try{await refreshState(true);if(preview){pinned=viewJob(preview.result);renderBrief(false);message('Recorded inert demo. New tasks require the local app.');return;}timer=setInterval(()=>{if(active?.job_id)poll();},600);serviceTimer=setInterval(async()=>{if(!active)try{await refreshState();if(state.active){active=state.active;controls();poll();}}catch{/* retain last known state without inventing success */}},3000);}catch(error){message(error.message,true);$('connection-status').textContent='Local session needs attention';controls();}}

$('today').textContent=new Date().toLocaleDateString(undefined,{month:'long',day:'numeric',year:'numeric'});initialize();
