// static/js/localfiles.js — Local Files browser modal controller for JarX-8.26

let currentPath = '';

export async function openLocalFilesModal() {
  const modal = document.getElementById('localfiles-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  
  if (!currentPath) {
    try {
      const res = await fetch('/api/filesystem/status');
      if (res.ok) {
        const data = await res.json();
        currentPath = data.default_workspace || '';
      }
    } catch(e) {}
  }
  loadDirectory(currentPath);
}

export function closeLocalFilesModal() {
  const modal = document.getElementById('localfiles-modal');
  if (modal) modal.classList.add('hidden');
}

export async function loadDirectory(path) {
  const listEl = document.getElementById('localfiles-list');
  const pathInput = document.getElementById('localfiles-path-input');
  if (!listEl) return;
  
  listEl.innerHTML = '<div style="padding:10px;opacity:0.6;">Loading...</div>';
  try {
    const res = await fetch('/api/filesystem/list', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({path: path || null})
    });
    const data = await res.json();
    if (!data.success) {
      listEl.innerHTML = `<div style="color:#e55;padding:10px;">Error: ${data.error || 'Failed to load directory'}</div>`;
      return;
    }
    
    currentPath = data.path;
    if (pathInput) pathInput.value = currentPath;
    
    if (!data.items || data.items.length === 0) {
      listEl.innerHTML = '<div style="padding:10px;opacity:0.5;">(Directory is empty)</div>';
      return;
    }
    
    let html = '<div style="display:flex;flex-direction:column;gap:4px;">';
    for (const item of data.items) {
      const icon = item.is_dir ? '📁' : '📄';
      const sizeStr = item.size !== null && item.size !== undefined ? `<span style="opacity:0.5;margin-left:auto;">${item.size} bytes</span>` : '';
      html += `
        <div style="display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:4px;background:var(--bg);cursor:pointer;" class="fs-item" data-path="${item.path}" data-isdir="${item.is_dir}">
          <span>${icon}</span>
          <span style="font-weight:${item.is_dir ? '600' : '400'};color:${item.is_dir ? 'var(--accent,#e06c75)' : 'var(--fg)'};">${item.name}</span>
          ${sizeStr}
          <span style="opacity:0.4;font-size:10px;margin-left:12px;">${item.modified || ''}</span>
        </div>
      `;
    }
    html += '</div>';
    listEl.innerHTML = html;
    
    // Attach click handlers
    listEl.querySelectorAll('.fs-item').forEach(el => {
      el.addEventListener('click', () => {
        const itemPath = el.getAttribute('data-path');
        const isDir = el.getAttribute('data-isdir') === 'true';
        if (isDir) {
          loadDirectory(itemPath);
        }
      });
    });
  } catch(e) {
    listEl.innerHTML = `<div style="color:#e55;padding:10px;">Failed to connect: ${e.message}</div>`;
  }
}

export function initLocalFiles() {
  const btn = document.getElementById('tool-localfiles-btn');
  if (btn) {
    btn.addEventListener('click', openLocalFilesModal);
  }
  
  const closeBtn = document.getElementById('close-localfiles-modal');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeLocalFilesModal);
  }
  
  const goBtn = document.getElementById('localfiles-go-btn');
  const pathInput = document.getElementById('localfiles-path-input');
  if (goBtn && pathInput) {
    goBtn.addEventListener('click', () => {
      loadDirectory(pathInput.value.trim());
    });
    pathInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') loadDirectory(pathInput.value.trim());
    });
  }
  
  const upBtn = document.getElementById('localfiles-up-btn');
  if (upBtn) {
    upBtn.addEventListener('click', () => {
      if (!currentPath) return;
      const parts = currentPath.split(/[\/\\]/).filter(Boolean);
      if (parts.length > 1) {
        parts.pop();
        // Windows drive handling
        const parentPath = parts.length === 1 && parts[0].endsWith(':') ? parts[0] + '\\' : parts.join('\\');
        loadDirectory(parentPath);
      }
    });
  }
}
