// static/js/training.js — AI Training Dashboard modal controller for JarX-8.26

export function initTraining() {
  const container = document.getElementById('training-modal');
  if (!container) return;

  // 1. Create the modal HTML and injects it into the DOM
  container.innerHTML = `
    <div class="modal-content admin-modal-content" role="dialog" aria-label="AI Training Manager" style="background:var(--bg);display:flex;flex-direction:column;width:90vw;max-width:900px;height:85vh;max-height:800px;">
      <div class="modal-header">
        <h4><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:6px;"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 2.5 2.5 0 0 1-.3-4.5A2.5 2.5 0 0 1 5.5 8 2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 2.5 2.5 0 0 0 .3-4.5A2.5 2.5 0 0 0 18.5 8 2.5 2.5 0 0 0 14.5 2Z"/></svg>AI Training Manager</h4>
        <div style="flex:1;"></div>
        <div class="admin-tabs" style="margin-right:12px;margin-bottom:0;border-bottom:none;">
            <button class="admin-tab active" data-mode="local">Local Mode</button>
            <button class="admin-tab" data-mode="remote">Remote/Sleep</button>
        </div>
        <button class="close-btn" id="close-training-modal" aria-label="Close training modal">&#x2716;</button>
      </div>
      <div class="modal-body" style="flex:1;overflow-y:auto;display:flex;flex-direction:column;padding:16px;gap:16px;">
        
        <!-- Hardware Info Panel -->
        <div class="admin-card" style="margin-bottom:0;">
          <h2 style="margin-bottom:8px;">Hardware Detect</h2>
          <div id="training-hw-info" style="display:flex;gap:16px;font-size:13px;opacity:0.8;">
             Loading hardware info...
          </div>
        </div>

        <div style="display:flex;gap:16px;flex:1;min-height:0;">
            <!-- Jobs List -->
            <div class="admin-card" style="flex:1;display:flex;flex-direction:column;margin-bottom:0;min-height:0;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h2 style="margin:0;">Training Jobs</h2>
                <button id="training-new-job-btn" class="admin-btn-add">+ New Job</button>
              </div>
              <div id="training-jobs-list" style="flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:8px;">
                 <div style="opacity:0.5;padding:10px;">Loading jobs...</div>
              </div>
            </div>

            <!-- Job Detail / New Job Form (Side Panel) -->
            <div class="admin-card" id="training-side-panel" style="flex:1;display:flex;flex-direction:column;margin-bottom:0;overflow-y:auto;display:none;">
                <!-- Content injected by JS -->
            </div>
        </div>
      </div>
    </div>
  `;

  // UI state
  let currentMode = 'local';
  let refreshInterval = null;
  let activeJobId = null;

  // Bind event listeners
  const btn = document.getElementById('training-sidebar-btn');
  if (btn) btn.addEventListener('click', openTrainingModal);
  
  const closeBtn = document.getElementById('close-training-modal');
  if (closeBtn) closeBtn.addEventListener('click', closeTrainingModal);

  const newJobBtn = document.getElementById('training-new-job-btn');
  if (newJobBtn) newJobBtn.addEventListener('click', showNewJobForm);

  // Tabs
  const tabs = container.querySelectorAll('.admin-tab');
  tabs.forEach(tab => {
      tab.addEventListener('click', () => {
          tabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          currentMode = tab.getAttribute('data-mode');
      });
  });

  async function openTrainingModal() {
    container.classList.remove('hidden');
    await loadHardwareInfo();
    await loadJobs();
    startAutoRefresh();
  }

  function closeTrainingModal() {
    container.classList.add('hidden');
    stopAutoRefresh();
  }

  function startAutoRefresh() {
      if (refreshInterval) clearInterval(refreshInterval);
      refreshInterval = setInterval(() => {
          loadJobs();
          if (activeJobId) {
              loadJobDetail(activeJobId);
          }
      }, 10000);
  }

  function stopAutoRefresh() {
      if (refreshInterval) {
          clearInterval(refreshInterval);
          refreshInterval = null;
      }
  }

  async function loadHardwareInfo() {
      const hwEl = document.getElementById('training-hw-info');
      if (!hwEl) return;
      try {
          const res = await fetch('/api/training/hardware');
          if (res.ok) {
              const data = await res.json();
              hwEl.innerHTML = `
                <span><b>CPU:</b> ${data.cpu || 'Unknown'}</span>
                <span><b>RAM:</b> ${data.ram_total_gb ? data.ram_total_gb + ' GB' : 'Unknown'}</span>
                <span><b>GPU:</b> ${data.gpu_name || (data.gpu_available ? 'Available' : 'None (CPU Mode)')}</span>
                <span><b>VRAM:</b> ${data.gpu_vram_gb ? data.gpu_vram_gb + ' GB' : 'N/A'}</span>
                <span><b>CUDA:</b> ${data.pytorch_cuda ? 'Yes' : 'No'}</span>
              `;
          } else {
              hwEl.innerHTML = '<span style="color:var(--red);">Failed to load hardware info</span>';
          }
      } catch(e) {
          hwEl.innerHTML = '<span style="color:var(--red);">Error connecting</span>';
      }
  }

  function getStatusBadge(status) {
      status = (status || '').toUpperCase();
      let color = '#777';
      let dot = '';
      if (status === 'RUNNING') { color = 'var(--accent, #4caf50)'; dot = '● '; }
      else if (status === 'PAUSED') color = '#ff9800';
      else if (status === 'COMPLETED') { color = '#2196f3'; dot = '✓ '; }
      else if (status === 'FAILED') color = 'var(--red, #f44336)';
      
      return `<span style="color:${color};font-weight:600;font-size:11px;">${dot}${status}</span>`;
  }

  async function loadJobs() {
      const listEl = document.getElementById('training-jobs-list');
      if (!listEl) return;
      try {
          const res = await fetch('/api/training/jobs');
          if (res.ok) {
              const data = await res.json();
              const jobs = Array.isArray(data) ? data : (data.jobs || []);
              if (!jobs || jobs.length === 0) {
                  listEl.innerHTML = '<div style="opacity:0.5;padding:10px;">No training jobs found.</div>';
                  return;
              }
              
              let html = '';
              for (const job of jobs) {
                  const jobId = job.job_id || job.id;
                  html += `
                    <div class="fs-item" style="padding:10px;border-radius:6px;background:var(--panel);border:1px solid var(--border);display:flex;flex-direction:column;gap:6px;cursor:pointer;" data-job-id="${jobId}">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <strong style="font-size:13px;">${job.name || 'Unnamed Job'}</strong>
                            <span style="font-size:10px;opacity:0.6;background:var(--bg);padding:2px 6px;border-radius:4px;">${job.mode || 'LOCAL'}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            ${getStatusBadge(job.status)}
                            <span style="font-size:11px;opacity:0.7;">${job.current_epoch || 0}/${job.total_epochs || '?'} Epochs</span>
                        </div>
                        <div style="display:flex;gap:6px;margin-top:4px;">
                            <button class="admin-btn-sm job-view-btn" data-id="${jobId}" style="flex:1;">View</button>
                            <button class="admin-btn-sm job-stop-btn" data-id="${jobId}" style="flex:1;">Stop</button>
                        </div>
                    </div>
                  `;
              }
              listEl.innerHTML = html;
              
              listEl.querySelectorAll('.fs-item').forEach(el => {
                  el.addEventListener('click', (e) => {
                      if (e.target.classList.contains('job-stop-btn')) {
                          e.stopPropagation();
                          stopJob(el.getAttribute('data-job-id'));
                      } else {
                          loadJobDetail(el.getAttribute('data-job-id'));
                      }
                  });
              });
          }
      } catch(e) {
          console.error('Failed to load jobs', e);
      }
  }

  function showNewJobForm() {
      activeJobId = null;
      const panel = document.getElementById('training-side-panel');
      panel.style.display = 'flex';
      panel.innerHTML = `
        <h2 style="margin-bottom:12px;">New Training Job</h2>
        <div class="settings-col" style="gap:12px;">
            <div class="settings-row"><label class="settings-label">Job Name</label><input type="text" id="t-new-name" class="settings-select" placeholder="MyModel"></div>
            <div class="settings-row"><label class="settings-label">Model Path</label><input type="text" id="t-new-model" class="settings-select" placeholder="/path/to/base/model"></div>
            <div class="settings-row"><label class="settings-label">Dataset</label><input type="text" id="t-new-dataset" class="settings-select" placeholder="/path/to/dataset"></div>
            <div style="display:flex;gap:12px;">
                <div class="settings-row" style="flex:1;"><label class="settings-label">Epochs</label><input type="number" id="t-new-epochs" class="settings-select" value="10"></div>
                <div class="settings-row" style="flex:1;"><label class="settings-label">Batch Size</label><input type="number" id="t-new-batch" class="settings-select" value="4"></div>
            </div>
            <div style="display:flex;gap:12px;">
                <div class="settings-row" style="flex:1;"><label class="settings-label">Learning Rate</label><input type="text" id="t-new-lr" class="settings-select" value="0.001"></div>
                <div class="settings-row" style="flex:1;"><label class="settings-label">Ckpt Interval</label><input type="number" id="t-new-ckpt" class="settings-select" value="1"></div>
            </div>
            <div class="settings-row" style="justify-content:space-between;margin-top:4px;">
                <label class="settings-label">Mixed Precision (fp16)</label>
                <input type="checkbox" id="t-new-fp16">
            </div>
            <div style="margin-top:12px;display:flex;justify-content:flex-end;">
                <button class="admin-btn-add" id="t-new-submit">Create Job</button>
            </div>
        </div>
      `;
      
      document.getElementById('t-new-submit').addEventListener('click', async () => {
          const payload = {
              name: document.getElementById('t-new-name').value,
              mode: currentMode,
              config: {
                  model_path: document.getElementById('t-new-model').value,
                  dataset_path: document.getElementById('t-new-dataset').value,
                  epochs: parseInt(document.getElementById('t-new-epochs').value, 10) || 10,
                  batch_size: parseInt(document.getElementById('t-new-batch').value, 10) || 4,
                  learning_rate: parseFloat(document.getElementById('t-new-lr').value) || 0.001,
                  checkpoint_interval: parseInt(document.getElementById('t-new-ckpt').value, 10) || 1,
                  mixed_precision: document.getElementById('t-new-fp16').checked
              }
          };
          
          try {
              const res = await fetch('/api/training/jobs', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/json'},
                  body: JSON.stringify(payload)
              });
              if (res.ok) {
                  loadJobs();
                  panel.innerHTML = '<div style="opacity:0.5;padding:10px;">Job created successfully.</div>';
              }
          } catch(e) {
              alert('Error creating job');
          }
      });
  }

  async function loadJobDetail(jobId) {
      activeJobId = jobId;
      const panel = document.getElementById('training-side-panel');
      panel.style.display = 'flex';
      panel.innerHTML = '<div style="opacity:0.5;padding:10px;">Loading job details...</div>';
      
      try {
          const res = await fetch(`/api/training/jobs/${jobId}`);
          if (!res.ok) throw new Error('Not found');
          const job = await res.json();
          
          const currentEpoch = job.current_epoch || job.epoch || 0;
          const totalEpochs = job.total_epochs || job.config?.epochs || 1;
          const progressPct = totalEpochs ? Math.min(100, Math.round((currentEpoch / totalEpochs) * 100)) : 0;
          
          let controls = '';
          if (job.status === 'RUNNING') {
              controls = `<button class="admin-btn-sm" id="jd-pause">Pause</button> <button class="admin-btn-sm" style="color:var(--red);" id="jd-stop">Stop</button>`;
          } else if (job.status === 'PAUSED') {
              controls = `<button class="admin-btn-sm" id="jd-resume">Resume</button> <button class="admin-btn-sm" style="color:var(--red);" id="jd-stop">Stop</button>`;
          } else if (job.status === 'CREATED' || job.status === 'QUEUED') {
              controls = `<button class="admin-btn-sm" id="jd-start">Start</button> <button class="admin-btn-sm" id="jd-cancel">Cancel</button>`;
          }
          
          panel.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;">
                <div>
                    <h2 style="margin:0;margin-bottom:4px;">${job.name}</h2>
                    <div style="font-size:11px;opacity:0.6;">ID: ${job.job_id || job.id} | Mode: ${job.mode}</div>
                </div>
                <div>${getStatusBadge(job.status)}</div>
            </div>
            
            <div style="margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;">
                    <span>Progress: ${currentEpoch}/${totalEpochs} Epochs</span>
                    <span>${progressPct}%</span>
                </div>
                <div style="width:100%;height:6px;background:var(--bg);border-radius:3px;overflow:hidden;">
                    <div style="width:${progressPct}%;height:100%;background:var(--accent,#4caf50);"></div>
                </div>
            </div>
            
            <div style="display:flex;gap:12px;margin-bottom:16px;">
                <div class="admin-card" style="flex:1;margin:0;padding:8px;">
                    <div style="font-size:10px;opacity:0.6;">Current Loss</div>
                    <div style="font-size:16px;font-weight:600;">${job.metrics?.loss || 'N/A'}</div>
                </div>
            </div>
            
            <div style="display:flex;gap:8px;margin-bottom:16px;">
                ${controls}
            </div>
            
            <h3 style="font-size:12px;margin-bottom:8px;">Recent Logs</h3>
            <div id="jd-logs" style="flex:1;background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:8px;font-family:monospace;font-size:10px;overflow-y:auto;white-space:pre-wrap;">Loading logs...</div>
          `;
          
          // Bind controls
          ['start', 'pause', 'resume', 'stop', 'cancel'].forEach(action => {
              const btn = document.getElementById(`jd-${action}`);
              if (btn) btn.addEventListener('click', () => sendAction(jobId, action));
          });
          
          // Load logs
          loadLogs(jobId);
          
      } catch(e) {
          panel.innerHTML = '<div style="opacity:0.5;padding:10px;color:var(--red);">Failed to load job details.</div>';
      }
  }

  async function loadLogs(jobId) {
      const logsEl = document.getElementById('jd-logs');
      if (!logsEl || activeJobId !== jobId) return;
      try {
          const res = await fetch(`/api/training/jobs/${jobId}/logs?tail=50`);
          if (res.ok) {
              const data = await res.json();
              const logs = Array.isArray(data) ? data : (data.logs || []);
              if (logs && logs.length) {
                  logsEl.textContent = logs.join('\n');
                  logsEl.scrollTop = logsEl.scrollHeight;
              } else {
                  logsEl.textContent = '(No logs yet)';
              }
          }
      } catch(e) {}
  }

  async function sendAction(jobId, action) {
      try {
          await fetch(`/api/training/jobs/${jobId}/${action}`, { method: 'POST' });
          loadJobs();
          if (activeJobId === jobId) loadJobDetail(jobId);
      } catch(e) {
          console.error(`Failed to ${action} job`, e);
      }
  }

  function stopJob(jobId) {
      if(confirm('Are you sure you want to stop this job?')) {
          sendAction(jobId, 'stop');
      }
  }
}
