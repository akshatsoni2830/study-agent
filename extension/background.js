chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === 'summarizeFolder') {
    (async () => {
      try {
        const apiBase = 'http://127.0.0.1:8000';
        const res = await fetch(`${apiBase}/summarize-folder`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(message.payload),
        });
        const data = await res.json();
        sendResponse({ ok: res.ok, status: res.status, data, apiBase });
      } catch (e) {
        sendResponse({ ok: false, status: 0, error: String(e) });
      }
    })();
    return true; // keep the message channel open for async response
  }
});
