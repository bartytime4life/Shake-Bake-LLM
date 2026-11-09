'use strict';
// A separate, explicit job. Pasted failures never use the source-brief draft store.
(() => {
  const el = id => document.getElementById(id);
  let projects = [], busy = false, connecting = false, example = false, report = null;
  let projectSignature = '', sourceMode = false;
  const syntheticOutput = 'Traceback (most recent call last):\n  File "validator.py", line 6, in validate_structure\n    return len(reported_slices) <= slices_detected\nTypeError: object of type \'NoneType\' has no len()\n';
  const bridge = () => window.sbWorkbench;
  const preview = !!window.__SB_RECORDED_PREVIEW__;
  const node = (tag, text, className) => {
    const result = document.createElement(tag);
    if (text !== undefined) result.textContent = String(text);
    if (className) result.className = className;
    return result;
  };
  function notice(text) {
    el('failure-notice').textContent = text;
    el('failure-notice').hidden = !text;
  }
  function selectWorkflow(source) {
    sourceMode = source;
    el('source-brief-workflow').hidden = !source;
    el('failed-run-workflow').hidden = source;
    for (const [id, selected] of [['choose-source-brief', source], ['choose-failed-run', !source]]) {
      el(id).setAttribute('aria-pressed', String(selected));
      el(id).classList.toggle('selected', selected);
    }
  }
  el('choose-failed-run').addEventListener('click', () => selectWorkflow(false));
  el('choose-source-brief').addEventListener('click', () => selectWorkflow(true));
  el('history-nav').addEventListener('click', () => selectWorkflow(true));
  el('workspace-nav').addEventListener('click', () => {
    if (!sourceMode) el('failure-output').focus();
  });
  if (preview) {
    selectWorkflow(true);
    el('choose-failed-run').disabled = true;
    el('choose-failed-run').querySelector('span').textContent = 'Available in the running local app.';
  }

  function controls() {
    const selected = projects.find(project => project.id === el('failure-project').value);
    const ready = !!bridge() && projects.length > 0 && !preview;
    el('diagnose-run').disabled = busy || connecting || !ready || !selected || (selected.demo && !example);
    el('connect-project-button').disabled = busy || connecting || !ready;
    el('try-failure-example').disabled = busy || connecting || !ready || !projects.some(project => project.demo);
    el('failure-example-notice').hidden = !example;
    if (!selected) {
      el('failure-project-help').textContent = 'Connect the folder containing the failing code. The bundled demo cannot diagnose a real project.';
    } else if (selected.demo && !example) {
      el('failure-project-help').textContent = 'Synthetic demo selected. Connect your project for a real error, or explicitly try the labelled example.';
    } else {
      el('failure-project-help').textContent = `${selected.demo ? 'Synthetic example' : 'Read-only project'} · ${selected.path || selected.label || selected.id}`;
    }
  }
  function updateState(value) {
    const native = value?.native || value;
    if (!Array.isArray(native?.projects)) return;
    projects = native.projects.map(project => typeof project === 'string'
      ? {id:project,label:project,demo:project === 'starter-demo'} : project);
    const signature = JSON.stringify(projects);
    if (projectSignature !== signature) {
      projectSignature = signature;
      const previous = el('failure-project').value;
      el('failure-project').replaceChildren(new Option('Choose a connected project', ''));
      for (const project of projects) {
        el('failure-project').append(new Option(project.demo ? 'Synthetic demo — example only' : project.label || project.id, project.id));
      }
      const preferred = projects.find(project => project.id === previous) || projects.find(project => !project.demo);
      el('failure-project').value = preferred?.id || '';
    }
    controls();
  }
  window.addEventListener('sb-workbench-state', event => updateState(event.detail));
  if (bridge()?.getState()) updateState(bridge().getState());
  controls();
  el('failure-project').addEventListener('change', () => {
    if (!projects.find(project => project.id === el('failure-project').value)?.demo) example = false;
    controls();
  });
  for (const id of ['failure-output', 'failure-command']) el(id).addEventListener('input', () => {
    if (example && (el('failure-output').value !== syntheticOutput || el('failure-command').value !== 'Synthetic example — no command was run')) example = false;
    controls();
  });
  el('try-failure-example').addEventListener('click', () => {
    if ((el('failure-output').value || el('failure-command').value) && !example) {
      notice('Your current error and command are unchanged. Clear those fields before trying the synthetic example.');
      return;
    }
    const demo = projects.find(project => project.demo);
    if (!demo) return;
    example = true;
    el('failure-project').value = demo.id;
    el('failure-output').value = syntheticOutput;
    el('failure-command').value = 'Synthetic example — no command was run';
    notice('');
    controls();
    el('diagnose-run').focus();
  });

  el('connect-project-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (connecting || busy || !bridge()) return;
    const path = el('project-path').value;
    if (!path.startsWith('/')) {
      el('project-connect-status').textContent = 'Use an absolute folder path beginning with /. The folder must be on the computer running this app.';
      el('project-path').focus();
      return;
    }
    connecting = true;
    controls();
    el('project-connect-status').textContent = 'Connecting folder for read-only use…';
    try {
      const result = await bridge().api('/api/projects', {label:el('project-label').value, path});
      await bridge().syncSession();
      updateState(bridge().getState());
      const id = result.project_id || result.id;
      if (projects.some(project => project.id === id)) el('failure-project').value = id;
      example = false;
      el('project-connect-status').textContent = 'Folder connected for this local session. Paste the error above, then find its source.';
    } catch (error) {
      el('project-connect-status').textContent = `Folder could not be connected. ${error.message}`;
    } finally {
      connecting = false;
      controls();
    }
  });

  function renderSource(evidence, frame) {
    const grid = node('div', undefined, 'evidence-grid');
    const source = node('article', undefined, 'source');
    const header = node('header');
    header.append(node('strong', evidence.path), node('span', `Lines ${evidence.start_line}–${evidence.end_line} · captured now`, 'source-meta'));
    const pre = node('pre');
    pre.tabIndex = 0;
    pre.setAttribute('aria-label', `Source excerpt from ${evidence.path}`);
    // Python source lines follow universal newlines; Unicode separators can occur inside strings.
    const lines = evidence.text.split(/\r\n|\r|\n/);
    if (lines.length && lines[lines.length - 1] === '') lines.pop();
    lines.forEach((text, index) => {
      const lineNumber = Number(evidence.start_line) + index;
      const line = node('span', undefined, 'line');
      if (lineNumber === Number(frame.line)) line.classList.add('is-failure');
      line.append(node('span', String(lineNumber), 'line-number'), node('span', text));
      pre.append(line);
    });
    const hash = node('div', `File SHA-256: ${evidence.file_sha256}\nExcerpt SHA-256: ${evidence.excerpt_sha256}`, 'hash');
    source.append(header, pre, hash);
    grid.append(source);
    return grid;
  }
  function renderReport(value, capturedExample) {
    report = value;
    const frame = value.frames?.find(item => item.frame_id === value.innermost_project_frame);
    const evidence = frame && value.evidence?.find(item => item.evidence_id === frame.evidence_id);
    const located = !!value.source_located && !!evidence;
    el('failure-result-status').textContent = capturedExample ? 'Synthetic example · no command was run' : 'Local source check · no command was run';
    el('failure-result-title').textContent = located
      ? frame.source_comparison === 'mismatch' ? 'Source located; pasted statement differs' : 'Source located — check this line'
      : 'No source located';
    const exception = value.terminal_exception;
    el('failure-exception').textContent = exception ? `${exception.type}${exception.message ? ': ' + exception.message : ''}${exception.message_truncated ? ' [Summary shortened; complete message is in Original output.]' : ''}` : 'No complete Python exception was identified.';
    el('failure-result-context').textContent = located
      ? `${evidence.path}:${frame.line} · ${frame.source_comparison === 'match' ? 'The pasted statement matches the current source line.' : frame.source_comparison === 'mismatch' ? 'The traceback and current file may be from different versions. Check this before drawing conclusions.' : 'The source line was read; the pasted statement could not be compared.'}`
      : 'The pasted output could not be tied to a readable source line in the selected project. No diagnosis or fix is established.';
    el('failure-source').replaceChildren();
    if (located) el('failure-source').append(renderSource(evidence, frame));
    el('failure-guidance').replaceChildren();
    for (const item of value.guidance || []) {
      const section = node('div', undefined, 'failure-guidance-item');
      section.append(node('h4', typeof item === 'string' ? 'Next check' : item.title), node('p', typeof item === 'string' ? item : item.detail));
      el('failure-guidance').append(section);
    }
    if (!el('failure-guidance').childElementCount) el('failure-guidance').append(node('p', 'Check the complete output and the selected project. This check does not run commands or establish the cause.', 'small muted'));
    el('failure-frame-list').replaceChildren();
    for (const item of value.frames || []) {
      const source = value.evidence?.find(entry => entry.evidence_id === item.evidence_id);
      const li = node('li');
      li.append(node('strong', `${item.reported_path}:${item.line}${item.function ? ' in ' + item.function : ''}`));
      li.append(node('div', `${item.status}${item.path ? ' · ' + item.path : ''}${source ? ' · source statement ' + item.source_comparison : ''}`));
      if (item.statement) li.append(node('div', item.statement));
      if (source && item !== frame) li.append(renderSource(source, item));
      el('failure-frame-list').append(li);
    }
    el('failure-frames').hidden = !value.frames?.length;
    // Warn-only, masked credential findings (screening.py); the report and its exports are unchanged.
    const findings = Array.isArray(value.screening) ? value.screening.filter(item => item && typeof item.kind === 'string' && typeof item.where === 'string' && typeof item.preview === 'string').slice(0, 20) : [];
    el('failure-credential-warning').textContent = findings.length
      ? [`Possible credentials in what this report would share (${findings.length} found). Exact text is unchanged; remove or rotate before sharing if they are real:`,
         ...findings.map(item => `- ${item.kind} in ${item.where}${typeof item.path === 'string' ? ' ' + item.path : ''}${Number.isInteger(item.line) ? ' line ' + item.line : ''}: ${item.preview}`)].join('\n')
      : '';
    el('failure-credential-warning').hidden = !findings.length;
    el('failure-original').textContent = value.error_output;
    el('failure-captured-command').textContent = value.command ? `Recorded command (not run): ${value.command}` : 'No command supplied.';
    el('failure-limits').replaceChildren(node('p', 'A source match identifies a place to inspect. It does not prove the cause, run the failing command, or apply a fix.'));
    const limits = [...(value.cutoffs || []).map(item => item === 'exception_message_budget' ? 'Exception summary shortened to 2 KiB. Original output is unchanged.' : 'Check limit reached: ' + item), ...(value.limitations || [])];
    if (limits.length) {
      const list = node('ul');
      for (const limit of limits) list.append(node('li', limit));
      el('failure-limits').append(list);
    }
    el('failure-result').hidden = false;
  }
  el('failure-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (busy || connecting || !bridge()) return;
    const project = projects.find(item => item.id === el('failure-project').value);
    if (!project || (project.demo && !example)) {
      notice('Choose or connect the project that actually failed. The synthetic demo is available only through Try a labelled example.');
      return;
    }
    const payload = {project_id:project.id, error_output:el('failure-output').value, command:el('failure-command').value};
    const encoder = new TextEncoder();
    if (encoder.encode(payload.error_output).length > 65536 || encoder.encode(payload.command).length > 4096) {
      notice('This check accepts up to 64 KiB of error output and 4 KiB of command text. Your text is unchanged; shorten it while keeping the complete traceback and final exception, then retry.');
      return;
    }
    const capturedExample = example;
    busy = true;
    controls();
    notice('');
    el('failure-result').hidden = true;
    el('failure-progress').textContent = 'Matching the traceback to your current source…';
    try {
      const value = await bridge().api('/api/troubleshoot', payload);
      if (value.kind !== 'failure_source_report' || typeof value.error_output !== 'string' || !Array.isArray(value.frames)) throw new Error('The service returned an incomplete source report.');
      renderReport(value, capturedExample);
      el('failure-progress').textContent = value.source_located ? 'Source check complete. Review the captured line below.' : 'Check complete. No source line was located.';
      if (document.activeElement === el('diagnose-run') || document.activeElement === document.body) el('failure-result-title').focus();
    } catch (error) {
      notice(`Could not check this error. ${error.message} Your pasted output is still here.`);
      el('failure-progress').textContent = 'Source check did not complete.';
    } finally {
      busy = false;
      controls();
    }
  });
  function saveReport(json) {
    if (!report) return;
    const frame = report.frames.find(item => item.frame_id === report.innermost_project_frame);
    const text = json ? JSON.stringify(report, null, 2) : [
      '# Shake & Bake — failed run source check',
      'No command was run and no fix was applied.',
      report.command ? `Recorded command: ${report.command}` : 'No command supplied.',
      '', '## Original output (exact, follows this line)', report.error_output,
      '', '## Source check', frame?.path ? `${frame.path}:${frame.line} · ${frame.source_comparison}` : 'No source located.',
      ...(report.evidence || []).map(item => `\n${item.path} lines ${item.start_line}–${item.end_line}\n${item.text}\nFile SHA-256: ${item.file_sha256}\nExcerpt SHA-256: ${item.excerpt_sha256}`),
      '', '## Next checks', ...(report.guidance || []).map(item => typeof item === 'string' ? item : `${item.title}\n${item.detail}`),
      '', '## Limits', ...(report.cutoffs || []).map(item => 'Check limit reached: ' + item), ...(report.limitations || [])
    ].join('\n');
    const blob = new Blob([text], {type:json ? 'application/json' : 'text/plain;charset=utf-8'});
    const url = URL.createObjectURL(blob), link = node('a');
    link.href = url;
    link.download = `shake-bake-failure-report.${json ? 'json' : 'txt'}`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  el('download-failure-text').addEventListener('click', () => saveReport(false));
  el('download-failure-json').addEventListener('click', () => saveReport(true));
})();
