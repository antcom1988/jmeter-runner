const plan = document.querySelector('#plan');
const runs = document.querySelector('#runs');
const message = document.querySelector('#upload-message');

async function api(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}

async function loadPlans() {
  const plans = await api('/api/test-plans');
  plan.innerHTML = plans.length ? plans.map(name => `<option value="${name}">${name}</option>`).join('') : '<option value="">Upload a .jmx file first</option>';
}

async function loadRuns() {
  const data = await api('/api/runs');
  if (!data.length) { runs.innerHTML = '<p class="hint">No runs yet.</p>'; return; }
  runs.innerHTML = data.slice().reverse().map(run => `<article class="run">
    <strong>${run.plan}</strong> · <span class="status ${run.status}">${run.status}</span>
    ${run.reportUrl ? ` · <a target="_blank" href="${run.reportUrl}">Open HTML report</a>` : ''}
    · <a href="#" data-log="${run.logUrl}">View log</a><pre hidden></pre>
  </article>`).join('');
}

document.querySelector('#upload-form').addEventListener('submit', async event => {
  event.preventDefault(); message.textContent = 'Uploading…';
  try { const result = await api('/api/uploads', {method:'POST', body:new FormData(event.target)}); message.textContent = `Uploaded ${result.file}`; event.target.reset(); await loadPlans(); }
  catch (error) { message.textContent = error.message; }
});

document.querySelector('#run').addEventListener('click', async () => {
  if (!plan.value) return;
  try { await api('/api/runs', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({plan:plan.value})}); await loadRuns(); }
  catch (error) { alert(error.message); }
});

runs.addEventListener('click', async event => {
  const logUrl = event.target.dataset.log; if (!logUrl) return;
  event.preventDefault(); const output = event.target.parentElement.querySelector('pre');
  const data = await api(logUrl); output.textContent = data.log || 'JMeter has not written logs yet.'; output.hidden = !output.hidden;
});

loadPlans(); loadRuns(); setInterval(loadRuns, 2500);
