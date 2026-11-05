'use strict';
const $ = id => document.getElementById(id);
const icon = name => { const svg=document.createElementNS('http://www.w3.org/2000/svg','svg'); const use=document.createElementNS(svg.namespaceURI,'use'); use.setAttribute('href','#i-'+name); svg.append(use); return svg; };
const el = (tag,cls,text) => { const node=document.createElement(tag); if(cls)node.className=cls; if(text!==undefined)node.textContent=text; return node; };
const preview=window.__SB_RECORDED_PREVIEW__ || null;
let state=null, taskKind='code', activeTask=null, currentResult=null, pollTimer=null, toastTimer=null;
const errors={helper_busy:'One job is already running. Let it finish or cancel it first.',workbench_busy:'The local workbench is busy. Wait briefly, then check the current job in Activity.',workbench_request_timeout:'The local request timed out. Check Activity before starting another job; any previous brief is retained.',invalid_request:'Enter a question for your brief.',invalid_project_id:'Choose an approved working folder.',project_not_allowed:'This folder is not available to this workbench.',request_size:'That request is too large. Try a shorter question.',session_required:'Reload the workbench to restore its local session.',request_not_allowed:'The local session expired. Reload the workbench.',workbench_unavailable:'The workbench could not complete that request. Your source is unchanged.',unknown_or_expired_task:'This brief is no longer retained. Prepare a fresh one.'};
function friendly(code){return errors[code] || 'The task could not be completed ('+String(code)+'). Your source is unchanged.';}
async function api(path,payload){
  if(preview){if(path==='/api/state')return preview.state;if(path==='/api/tasks/'+preview.result.task_id)return preview.result;throw new Error('recorded_preview_only');}
  const options={credentials:'same-origin',headers:{}};
  if(payload!==undefined){options.method='POST';options.headers={'Content-Type':'application/json','X-SB-CSRF':state?.csrf_token||''};options.body=JSON.stringify(payload);}
  const response=await fetch(path,options);const value=await response.json();if(!response.ok)throw new Error(value.error||'workbench_unavailable');return value;
}
function toast(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,4500);}
function formatBytes(number){return number>=1024?(number/1024).toFixed(1)+' KiB':number+' B';}
function setKind(kind){taskKind=kind;for(const button of document.querySelectorAll('[data-kind]')){const selected=button.dataset.kind===kind;button.classList.toggle('selected',selected);button.setAttribute('aria-checked',String(selected));}if(state)renderModels();saveDraft();}
function saveDraft(){if(preview)return;try{localStorage.setItem('sb-workbench-draft',JSON.stringify({task:$('task').value,kind:taskKind,project:$('project').value}));}catch{}}
function projectNote(){const project=state?.projects.find(p=>p.id===$('project').value);$('project-note').textContent=project?.demo?'Starter demo · an inert source fixture, read only.':project?.path||'';}
function showConnection(value){
 const connected=value?.state==='connected';$('connection-title').textContent=connected?'Ollama is reachable':value?.state==='unavailable'?'Ollama is unavailable':'Ollama not checked';
 $('connection-caption').textContent=connected?value.models.length+' model entries reported. Availability does not establish qualification.':value?.state==='unavailable'?'Start your local Ollama service to check models. Evidence preparation is still available.':'Evidence collection works without a model.';
}
function renderModels(){
 const container=$('model-cards');container.replaceChildren();
 for(const model of state.catalog.models){
   const button=el('button','model-card');button.type='button';button.setAttribute('aria-label','Model details: '+model.title);
   const header=el('div','model-card-header');header.append(el('span','model-avatar',model.initial));const name=el('div');name.append(el('strong',null,model.title),el('small',null,model.publisher));header.append(name);
   const valid=state.policy.profiles.some(p=>p.model===model.tag&&p.task_kind===taskKind&&p.status==='review_record_valid');
   button.append(header,el('span','candidate-badge',valid?'Review record valid · identity checked on use':'Candidate · local trial pending'),el('p',null,model.role));
   const foot=el('div','model-card-footer');foot.append(el('span',null,model.download),el('span',null,'Explore model  ↗'));button.append(foot);button.addEventListener('click',()=>showModel(model.tag));container.append(button);
 }
}
function showModel(tag){
 const model=state.catalog.models.find(m=>m.tag===tag)||{tag,title:tag,publisher:'Owner-configured model',role:'Local preparation profile',download:'Package size not recorded',stats:[],source:null,limits:'Actual local accuracy and memory use require qualification.'};
 const panel=$('model-dialog-content');panel.replaceChildren();panel.append(el('span','eyebrow','MODEL DETAILS · INSPECT THE CHOICE'),el('h2',null,model.title),el('div','tag',model.tag),el('p',null,model.role));
 panel.append(el('h3',null,'Why it is being considered'),el('p',null,model.reason||'This model is listed by the owner as a candidate. No winning result is inferred.'));
 const chosen=currentResult?.routing?.model===tag;
 if(chosen){panel.append(el('h3',null,'Why it was selected for this brief'),el('p',null,currentResult.routing.why));}
 panel.append(el('h3',null,'Published statistics'));
 if(model.stats.length){const table=el('table');const head=el('tr');head.append(el('th',null,'Author-reported benchmark'),el('th',null,'Reported score'));table.append(head);for(const metric of model.stats){const row=el('tr');row.append(el('td',null,metric.name),el('td',null,metric.value));table.append(row);}panel.append(table);}
 else panel.append(el('p',null,'No published statistics are recorded for this exact entry.'));
 panel.append(el('p','micro','Publisher figures use their own test setup. They are not measurements of this quantized model on your PC. Checked '+(model.checked||'not recorded')+'.'));
 if(model.source){const link=el('a',null,'Open the primary benchmark source ↗');link.href=model.source;link.target='_blank';link.rel='noopener noreferrer';panel.append(link);}
 panel.append(el('h3',null,'Local results for this task'));
 const detailKind=chosen?(currentResult.task_kind||taskKind):taskKind;
 const profile=state.policy.profiles.find(p=>p.model===tag&&p.task_kind===detailKind&&p.evaluation);
 const local=el('div','local-pending');
 if(profile){const record=profile.evaluation;local.append(el('p',null,'Owner-recorded trial: '+Math.round(record.accuracy*100)+'% final-task accuracy across '+record.case_count+' cases. Dataset: '+record.dataset_id+'.'),el('p',null,'Record status: '+profile.status+'. '+(profile.reason||'Live model availability is checked when a task runs.')));}
 else local.append(el('p',null,'No reviewed local trial is recorded for this task. Accuracy, speed and memory use have not been measured here.'));
 panel.append(local);
 const details=el('details');const summary=el('summary',null,'Version, hardware notes & limits');details.append(summary,el('p',null,'Registry tag: '+model.tag+'. '+model.download+'. Download size is not runtime VRAM.'),el('p',null,model.limits));
 const digest=currentResult?.worker?.observed_model_digest;if(chosen&&digest)details.append(el('p',null,'Observed local tag digest: '+digest));
 details.append(el('p',null,'A profile needs a reviewed held-out trial, a matching pipeline and model identity, and no recorded critical errors before automatic selection. Records and metadata are not a guarantee of future answers.'));panel.append(details);
 $('model-dialog').showModal();
}
function renderState(value){
 const previous=$('project').value;state=value;$('version').textContent='v'+value.version;
 const select=$('project');select.replaceChildren();for(const p of value.projects){const option=el('option',null,p.label+(p.demo?' · demo':''));option.value=p.id;select.append(option);}if(value.projects.some(p=>p.id===previous))select.value=previous;projectNote();
 $('local-ai').checked=value.local_ai_enabled;
 const valid=value.policy.profiles.filter(p=>p.status==='review_record_valid').length;
 $('profile-count').textContent=valid?valid+' profile records match this build':'No qualified local profile yet';
 $('profile-caption').textContent=valid?'Live model identity will be checked before preparation.':'Candidates stay candidates until reviewed accuracy trials pass.';
 showConnection(value.inventory);renderModels();
 const recent=$('recent-list');recent.replaceChildren();
 for(const item of value.recent){const button=el('button','recent-button');button.type='button';button.append(el('strong',null,item.task),el('small',null,(item.entry_point==='assistant'?'Assistant':'Workspace')+' · '+item.task_kind+' · '+item.state.toLowerCase()));button.addEventListener('click',async()=>{if(item.state==='RUNNING'){activeTask=item.task_id;setBusy(true);pollJob();return;}try{showResult(await api('/api/tasks/'+item.task_id));$('brief-section').scrollIntoView({behavior:'smooth',block:'start'});}catch(error){toast(friendly(error.message));}});recent.append(button);}
 if(!value.recent.length)recent.append(el('p','muted','Your first brief starts here.'));
}
async function refreshState(){renderState(await api('/api/state'));}
function resultContext(message=''){const label=$('result-request');label.textContent=currentResult?'Brief for: '+(currentResult.original_request.length>240?currentResult.original_request.slice(0,240)+'…':currentResult.original_request)+' · Job '+currentResult.task_id.slice(0,8)+(message?' · '+message:''):message||'A completed brief will show its original request and job identity here.';}
function setBusy(busy){$('prepare').disabled=busy;$('job-progress').hidden=!busy;$('task').disabled=busy;$('project').disabled=busy;for(const card of document.querySelectorAll('[data-kind]'))card.disabled=busy||Boolean(preview);$('step-source').classList.toggle('preparing',busy);if(busy){resultContext(currentResult?'Showing the previous completed brief while a new job runs.':'Preparing a new brief.');$('result-state').textContent=currentResult?'Previous brief retained':'Preparing';$('result-state').className='status-pill attention';}}
async function startTask(event){event.preventDefault();$('form-error').hidden=true;if(preview){showResult(preview.result);toast('Showing the recorded demo. New tasks run in the local app.');return;}if(!$('task').value.trim())return;saveDraft();setBusy(true);try{const started=await api('/api/tasks',{project_id:$('project').value,task:$('task').value,task_kind:taskKind});activeTask=started.task_id;pollJob();}catch(error){setBusy(false);resultContext(currentResult?'A new job was not confirmed; this is the previous brief.':'The new job was not confirmed. Check Activity.');$('form-error').textContent=friendly(error.message);$('form-error').hidden=false;}}
async function pollJob(){
 clearTimeout(pollTimer);if(!activeTask)return;const identifier=activeTask;
 try{const result=await api('/api/tasks/'+identifier);if(activeTask!==identifier)return;if(result.state==='RUNNING'){pollTimer=setTimeout(pollJob,750);return;}activeTask=null;setBusy(false);showResult(result);await refreshState();}
 catch(error){activeTask=null;setBusy(false);resultContext(currentResult?'The latest status could not be confirmed; this is the previous brief.':'Check Activity to recover the latest job status.');$('form-error').textContent=friendly(error.message);$('form-error').hidden=false;}
}
function drawMap(records){
 const svg=$('evidence-map');svg.replaceChildren();const ns=svg.namespaceURI;
 const add=(tag,attrs,text,parent=svg)=>{const node=document.createElementNS(ns,tag);for(const [key,value]of Object.entries(attrs||{}))node.setAttribute(key,String(value));if(text!==undefined)node.textContent=text;parent.append(node);return node;};
 const positions=records.length>2?[[16,22],[16,144],[405,22],[405,144]]:[[28,83],[398,83]];
 records.forEach((record,index)=>{const [x,y]=positions[index];const start=x<280?x+135:x;add('path',{d:`M${start} ${y+22} C${x<280?215:350} ${y+22},${x<280?210:350} 105,280 105`,class:'map-link'});});
 add('circle',{cx:280,cy:105,r:46,class:'map-center'});add('text',{x:280,y:103,'text-anchor':'middle',class:'map-label'},'Your brief');add('text',{x:280,y:120,'text-anchor':'middle',class:'map-small'},records.length+' excerpts');
 records.forEach((record,index)=>{const [x,y]=positions[index];const g=add('g',{class:'map-source',role:'button',tabindex:0,'aria-label':'Inspect '+record.path+' '+record.evidence_id});add('rect',{x,y,width:135,height:44,rx:9},undefined,g);add('text',{x:x+10,y:y+16},record.evidence_id+' · captured source',g);const path=record.path.length>22?'…'+record.path.slice(-21):record.path;add('text',{x:x+10,y:y+32},path,g);const select=()=>{for(const card of document.querySelectorAll('.evidence-card'))card.classList.remove('highlight');const card=$('source-'+record.evidence_id);card.classList.add('highlight');card.scrollIntoView({behavior:'smooth',block:'center'});};g.addEventListener('click',select);g.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();select();}});});
}
function showResult(result){
 if(result.state!=='DONE'){const cancelled=result.state==='CANCELLED';toast(cancelled?'Job cancelled. Source files are unchanged.':'The job ended without a completed brief. Source files are unchanged.');resultContext(currentResult?'The latest job did not complete; this is the previous brief.':'The latest job did not complete.');$('result-state').textContent=currentResult?'Previous brief retained':cancelled?'Cancelled':result.state;return;}
 if(result.outcome==='DENY'||result.outcome==='ERROR'){toast(friendly(result.code||result.worker_error||'workbench_unavailable'));resultContext(currentResult?'The latest job failed; this is the previous brief.':'The latest job could not prepare a brief.');$('result-state').textContent=currentResult?'Previous brief retained':'Could not prepare';$('result-state').className='status-pill attention';return;}
 currentResult=result;$('full-request').textContent=result.original_request;resultContext();$('empty-result').hidden=true;$('result-content').hidden=false;
 const records=result.evidence||[];const route=result.routing||{};
 $('metric-evidence').textContent=records.length;$('metric-files').textContent=result.files_examined??'—';$('metric-bytes').textContent=formatBytes(result.selected_excerpt_bytes||0);
 $('result-state').textContent=result.worker?'Evidence + unverified notes':'Evidence-only brief';$('result-state').className='status-pill complete';
 $('choice-title').textContent=route.model||'Evidence-only handoff';$('choice-subtitle').textContent=route.model?'Chosen from reviewed profile records.':'No qualified model was selected.';
 $('why-label').textContent=route.model?'Why this model?':'Why evidence only?';$('why-text').textContent=route.why||'Exact evidence is preserved for the host to assess.';
 $('why-facts').replaceChildren(el('span',null,'Local model'),el('strong',null,route.model?'Reviewed record selected':'No qualified profile selected'));
 if(route.model){const details=el('button','text-button','Inspect selected model ↗');details.addEventListener('click',()=>showModel(route.model));$('why-facts').append(details);}
 const note=$('result-note');note.replaceChildren();
 if(result.worker){note.append(el('strong',null,'Worker interpretation · unverified'),el('span',null,result.worker.summary));}
 else note.append(el('strong',null,records.length?'Evidence collected. The host makes the judgment.':'No usable source matched this request.'),el('span',null,route.why||'Inspect the scan scope and request more evidence if needed.'));
 drawMap(records);const list=$('evidence-list');list.replaceChildren();
 for(const record of records){const card=el('article','evidence-card');card.id='source-'+record.evidence_id;const header=el('div','evidence-header');header.append(el('span','evidence-id',record.evidence_id),el('strong','evidence-path',record.path),el('span','evidence-range','Lines '+record.start_line+'–'+record.end_line));const code=el('div','source-code');const lineCount=record.end_line-record.start_line+1;code.append(el('pre','source-gutter',Array.from({length:lineCount},(_,i)=>String(record.start_line+i)).join('\n')),el('pre','source-text',record.text));const hash=el('details','hash-detail');hash.append(el('summary',null,'Inspect source identity'),el('code',null,'File SHA-256: '+record.file_sha256),el('code',null,'Excerpt SHA-256: '+record.excerpt_sha256),el('p',null,'Captured snapshot; the current file is not being revalidated.'));card.append(header,code,hash);list.append(card);}
 const scope=$('scope-content');scope.replaceChildren(el('p',null,'Coverage: selected excerpts only. This is not a complete repository review.'),el('p',null,'Scan cutoffs: '+((result.cutoffs||[]).join(', ')||'none reached')+'.'),el('p',null,'Exclusions: '+JSON.stringify(result.exclusions||{})),el('p',null,'Source bytes read: '+(result.source_bytes_read??'not recorded')+'.'),el('p',null,'Cloud usage and token savings are not measured. No direct cloud-provider client is active.'),el('code',null,'Snapshot: '+(result.snapshot_id||'No captured source snapshot')));
 if(result.worker?.questions?.length)scope.append(el('p',null,'Worker questions: '+result.worker.questions.join(' ')));
 for(const id of ['step-source','step-model','step-evidence','step-host'])$(id).classList.remove('done','attention','preparing');
 $('step-source').classList.add(records.length?'done':'attention');$('step-model').classList.add(result.worker?'done':'attention');$('step-evidence').classList.add(records.length?'done':'attention');$('step-host').classList.add('attention');
}
function briefText(){
 if(!currentResult)return '';
 const r=currentResult;const parts=['SHAKE & BAKE · EVIDENCE HANDOFF','Preparation only. Host reasoning and a final answer are still required.','','REQUEST',r.original_request||'', '', 'MODEL CHOICE',r.routing?.why||'No model selected.'];
 if(r.worker)parts.push('','UNVERIFIED WORKER NOTES',r.worker.summary,...(r.worker.questions||[]).map(q=>'Open question: '+q));
 for(const e of r.evidence||[])parts.push('',e.evidence_id+' · '+e.path+':'+e.start_line+'–'+e.end_line,'File SHA-256: '+e.file_sha256,e.text);
 parts.push('','SCOPE','Selected excerpts only; not a complete repository review.','Cutoffs: '+((r.cutoffs||[]).join(', ')||'none reached'),'Snapshot: '+(r.snapshot_id||'none'),'Captured source is not live revalidation.');return parts.join('\n');
}
async function init(){
 try{
  renderState(await api('/api/state'));
  if(preview){$('task').value=preview.result.original_request;$('task').readOnly=true;$('prepare').firstChild.textContent='Open recorded demo ';$('local-ai').disabled=true;$('check-ollama').disabled=true;for(const card of document.querySelectorAll('[data-kind]'))card.disabled=true;for(const b of document.querySelectorAll('[data-example]'))b.disabled=true;$('project-note').textContent='Recorded demo preview · new tasks run in the local app.';document.querySelector('.top-status').replaceChildren(el('span','dot mint'),document.createTextNode('Recorded demo preview'));showResult(preview.result);}
  else{try{const draft=JSON.parse(localStorage.getItem('sb-workbench-draft')||'null');if(draft){$('task').value=String(draft.task||'').slice(0,16384);if(['code','troubleshoot','documents','search'].includes(draft.kind))setKind(draft.kind);if(state.projects.some(p=>p.id===draft.project))$('project').value=draft.project;projectNote();}}catch{}const running=state.recent.find(item=>item.state==='RUNNING');if(running){activeTask=running.task_id;setBusy(true);pollJob();}}
 }catch(error){$('form-error').textContent=friendly(error.message);$('form-error').hidden=false;$('prepare').disabled=true;}
}
document.querySelectorAll('[data-kind]').forEach(button=>button.addEventListener('click',()=>setKind(button.dataset.kind)));
$('project').addEventListener('change',()=>{projectNote();saveDraft();});$('task').addEventListener('input',saveDraft);
document.querySelectorAll('[data-example]').forEach(button=>button.addEventListener('click',()=>{setKind('code');$('task').value=button.dataset.example==='coverage'?'Find the executable slice coverage guard. Can it accept fewer reported slices than detected? Provide exact evidence and gaps.':'Explain how executable slice validation works in this demo. Show the controlling source and what remains unknown.';saveDraft();$('task').focus();}));
$('task-form').addEventListener('submit',startTask);
$('cancel-job').addEventListener('click',async()=>{if(!activeTask)return;try{await api('/api/tasks/'+activeTask+'/cancel',{});pollJob();}catch(error){toast(friendly(error.message));}});
$('local-ai').addEventListener('change',async()=>{const checkbox=$('local-ai');checkbox.disabled=true;try{await api('/api/settings',{enabled:checkbox.checked});await refreshState();if(activeTask)pollJob();toast(checkbox.checked?'Qualified local AI is allowed.':'Local AI switched off. New evidence-only jobs remain available.');}catch(error){checkbox.checked=!checkbox.checked;toast(friendly(error.message));}finally{checkbox.disabled=false;}});
$('check-ollama').addEventListener('click',async()=>{const button=$('check-ollama');button.disabled=true;$('connection-title').textContent='Checking local service…';try{showConnection(await api('/api/inventory',{}));}catch(error){toast(friendly(error.message));}finally{button.disabled=false;}});
$('close-model').addEventListener('click',()=>$('model-dialog').close());$('close-copy').addEventListener('click',()=>$('copy-dialog').close());
$('copy-brief').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(briefText());toast('Brief copied. Paste it into your assistant.');}catch{$('copy-text').value=briefText();$('copy-dialog').showModal();$('copy-text').select();}});
$('download-brief').addEventListener('click',()=>{if(!currentResult)return;const blob=new Blob([JSON.stringify(currentResult,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=el('a');link.href=url;link.download='shake-and-bake-brief-'+currentResult.task_id.slice(0,8)+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
init();
