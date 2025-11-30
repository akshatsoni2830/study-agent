(() => {
  const BTN_ID = 'study-agent-button';
  const WRAP_ID = 'study-agent-popup-wrap';

  function getFolderIdFromUrl() {
    const href = location.href;
    // Match /folders/<id>
    const m1 = href.match(/\/folders\/([a-zA-Z0-9_-]+)/);
    if (m1 && m1[1]) return m1[1];
    // Match ?id=<id>
    const m2 = href.match(/[?&]id=([a-zA-Z0-9_-]+)/);
    if (m2 && m2[1]) return m2[1];
    return null;
  }

  function ensureButton() {
    if (document.getElementById(BTN_ID)) return;
    const btn = document.createElement('button');
    btn.id = BTN_ID;
    btn.textContent = 'Summarize this folder';
    btn.className = 'study-agent-floating-btn';
    btn.addEventListener('click', openPopup);
    document.documentElement.appendChild(btn);
  }

  function openPopup() {
    const folderId = getFolderIdFromUrl();
    if (!folderId) {
      showToast('Open a specific Google Drive folder first.');
      return;
    }
    closePopup();
    const wrap = document.createElement('div');
    wrap.id = WRAP_ID;
    wrap.className = 'study-agent-popup-wrap';
    wrap.innerHTML = `
      <div class="study-agent-popup">
        <div class="sap-header">Study Agent</div>
        <div class="sap-body">
          <label>Subject Name<br/><input id="sap-subject" type="text" placeholder="e.g., Data Structures"/></label>
          <label>Semester (optional)<br/><input id="sap-sem" type="text" placeholder="e.g., Sem 3"/></label>
          <div class="sap-actions">
            <button id="sap-cancel" class="sap-btn-outline">Cancel</button>
            <button id="sap-run" class="sap-btn-primary">Summarize</button>
          </div>
          <div class="sap-status" id="sap-status"></div>
        </div>
      </div>
    `;
    document.documentElement.appendChild(wrap);
    document.getElementById('sap-cancel').addEventListener('click', closePopup);
    document.getElementById('sap-run').addEventListener('click', async () => {
      const subjectName = /** @type {HTMLInputElement} */(document.getElementById('sap-subject')).value.trim();
      const semester = /** @type {HTMLInputElement} */(document.getElementById('sap-sem')).value.trim();
      const statusEl = document.getElementById('sap-status');
      if (!subjectName) {
        statusEl.textContent = 'Please enter a subject name.';
        return;
      }
      statusEl.textContent = 'Working... this can take a while for large folders.';
      try {
        const payload = { folderId, subjectName, semester };
        chrome.runtime.sendMessage({ type: 'summarizeFolder', payload }, (resp) => {
          if (!resp) {
            statusEl.textContent = 'No response from extension. Is it installed properly?';
            return;
          }
          if (resp.ok && resp.data && resp.data.status === 'ok') {
            const url = `${resp.apiBase}${resp.data.summary_url}`;
            statusEl.innerHTML = `Done! <a href="${url}" target="_blank" rel="noopener">Open summary</a>`;
          } else if (resp.ok) {
            statusEl.textContent = `Server response: ${resp.status} ${JSON.stringify(resp.data)}`;
          } else {
            statusEl.textContent = `Error: ${resp.status} ${resp.error || ''}`;
          }
        });
      } catch (e) {
        statusEl.textContent = String(e);
      }
    });
  }

  function closePopup() {
    const old = document.getElementById(WRAP_ID);
    if (old) old.remove();
  }

  function showToast(text) {
    const toast = document.createElement('div');
    toast.className = 'study-agent-toast';
    toast.textContent = text;
    document.documentElement.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  // Observe URL changes in SPA navigation
  const obs = new MutationObserver(() => ensureButton());
  obs.observe(document.documentElement, { childList: true, subtree: true });
  ensureButton();
})();
