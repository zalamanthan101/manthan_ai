// ============================================
// MANTHAN AI — Full App Sidebar Provider
// File: SidebarProvider.js
// ============================================

const vscode = require('vscode');

class SidebarProvider {
    constructor(extensionUri) {
        this._extensionUri = extensionUri;
        this._view = null;
    }

    resolveWebviewView(webviewView) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };
        webviewView.webview.html = this._getHtmlForWebview();

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'askAI':
                    await this._callChat(data.task, data.message);
                    break;
                case 'runCode':
                    await this._callRun(data.code, data.language);
                    break;
                case 'uploadFile':
                    await this._callUpload(data.fileData, data.fileName, data.workspaceId);
                    break;
            }
        });
    }

    sendToChat(task, message) {
        if (this._view) {
            this._view.webview.postMessage({ type: 'addUserMessage', value: message, task });
            this._callChat(task, message);
        }
    }

    async _callChat(task, message) {
        this._post({ type: 'showLoading', tab: 'chat' });
        try {
            const form = new URLSearchParams();
            form.append('task', task || 'chat');
            form.append('message', message);

            const res = await fetch('http://127.0.0.1:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: form.toString()
            });
            const data = await res.json();
            this._post({ type: 'chatResponse', value: data.response || data.detail || 'No response' });
        } catch (e) {
            this._post({ type: 'chatResponse', value: `❌ Backend nahi mila!\n\npython main.py chal raha hai?\n\nError: ${e.message}` });
        }
    }

    async _callRun(code, language) {
        this._post({ type: 'showLoading', tab: 'run' });
        try {
            const form = new URLSearchParams();
            form.append('task', 'fix');
            form.append('message', `Run this ${language} code and explain output:\n\`\`\`${language}\n${code}\n\`\`\``);

            const res = await fetch('http://127.0.0.1:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: form.toString()
            });
            const data = await res.json();
            this._post({ type: 'runResponse', value: data.response || 'No output' });
        } catch (e) {
            this._post({ type: 'runResponse', value: `❌ Error: ${e.message}` });
        }
    }

    async _callUpload(fileData, fileName, workspaceId) {
        this._post({ type: 'showLoading', tab: 'upload' });
        try {
            // File content ko message ke saath bhejo
            const form = new URLSearchParams();
            form.append('task', 'explain');
            form.append('message', `Analyze this file "${fileName}" and give a summary:\n\n${fileData.substring(0, 3000)}`);

            const res = await fetch('http://127.0.0.1:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: form.toString()
            });
            const data = await res.json();
            this._post({ type: 'uploadResponse', value: data.response || 'No response', fileName });
        } catch (e) {
            this._post({ type: 'uploadResponse', value: `❌ Error: ${e.message}`, fileName });
        }
    }

    _post(msg) {
        if (this._view) this._view.webview.postMessage(msg);
    }

    _getHtmlForWebview() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0a0a10;
  --bg2: #111118;
  --bg3: #1a1a28;
  --border: #2a2a3a;
  --green: #00FF9C;
  --blue: #00C2FF;
  --purple: #B060FF;
  --red: #FF4D6D;
  --yellow: #FFB800;
  --text: #e0e0e0;
  --muted: #666;
}

body {
  font-family: 'Segoe UI', sans-serif;
  background: var(--bg);
  color: var(--text);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  font-size: 12px;
}

/* ── Header ── */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.logo { display: flex; align-items: center; gap: 6px; }
.logo-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
.logo-text { font-size: 12px; font-weight: 800; color: var(--green); letter-spacing: 2px; }
.server-status { font-size: 10px; color: var(--muted); }

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── Tabs ── */
.tabs {
  display: flex;
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.tab {
  flex: 1;
  padding: 8px 4px;
  text-align: center;
  cursor: pointer;
  font-size: 11px;
  color: var(--muted);
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
  user-select: none;
}
.tab.active { color: var(--green); border-bottom-color: var(--green); background: var(--bg); }
.tab:hover:not(.active) { color: var(--text); background: var(--bg3); }

/* ── Tab Panels ── */
.panel { display: none; flex: 1; flex-direction: column; overflow: hidden; padding: 10px; gap: 8px; }
.panel.active { display: flex; }

/* ── Task Buttons ── */
.task-row { display: flex; gap: 4px; flex-wrap: wrap; flex-shrink: 0; }
.task-btn {
  padding: 3px 9px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg2);
  color: var(--muted);
  font-size: 10px;
  cursor: pointer;
  transition: all 0.15s;
}
.task-btn.active { background: #00FF9C22; border-color: var(--green); color: var(--green); }

/* ── Chat History ── */
.chat-history {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0;
}
.chat-history::-webkit-scrollbar { width: 3px; }
.chat-history::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

.msg {
  padding: 8px 10px;
  border-radius: 8px;
  line-height: 1.5;
  word-wrap: break-word;
  white-space: pre-wrap;
  max-width: 98%;
  font-size: 11.5px;
}
.msg-user { background: #007acc; color: #fff; align-self: flex-end; border-radius: 8px 2px 8px 8px; }
.msg-ai { background: var(--bg3); color: var(--text); align-self: flex-start; border: 1px solid var(--border); border-radius: 2px 8px 8px 8px; }
.msg-loading { background: var(--bg3); color: var(--muted); border: 1px solid var(--border); font-style: italic; font-size: 11px; }
.msg-system { background: #00FF9C11; color: var(--green); border: 1px solid #00FF9C33; font-size: 11px; text-align: center; align-self: center; border-radius: 20px; padding: 4px 12px; }

/* ── Input Area ── */
.input-row { display: flex; gap: 6px; flex-shrink: 0; }
textarea, .code-input {
  flex: 1;
  padding: 8px;
  background: var(--bg3);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 11.5px;
  resize: none;
  font-family: 'Consolas', monospace;
  outline: none;
  transition: border-color 0.15s;
}
textarea:focus, .code-input:focus { border-color: #00FF9C44; }
.send-btn {
  padding: 0 12px;
  background: var(--green);
  color: #000;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 800;
  font-size: 15px;
  align-self: flex-end;
  height: 36px;
  transition: background 0.15s;
}
.send-btn:hover { background: #00cc7a; }
.send-btn:disabled { background: var(--border); color: var(--muted); cursor: not-allowed; }

/* ── Upload Panel ── */
.upload-zone {
  border: 2px dashed var(--border);
  border-radius: 10px;
  padding: 20px;
  text-align: center;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.upload-zone:hover, .upload-zone.drag { border-color: var(--blue); color: var(--blue); background: #00C2FF08; }
.upload-zone .upload-icon { font-size: 24px; margin-bottom: 6px; }
.upload-zone p { font-size: 11px; }
.file-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
.file-item {
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 11px;
}
.file-item .file-name { color: var(--blue); font-weight: 600; margin-bottom: 4px; }
.file-item .file-resp { color: var(--text); white-space: pre-wrap; font-size: 11px; line-height: 1.4; }
#file-input { display: none; }

/* ── Run Panel ── */
.lang-select {
  background: var(--bg3);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  outline: none;
  flex-shrink: 0;
}
.run-output {
  flex: 1;
  overflow-y: auto;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  font-family: 'Consolas', monospace;
  font-size: 11px;
  color: var(--green);
  white-space: pre-wrap;
  min-height: 80px;
}
.run-controls { display: flex; gap: 6px; align-items: center; flex-shrink: 0; }
.run-btn {
  padding: 6px 16px;
  background: var(--green);
  color: #000;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 700;
  font-size: 11px;
  transition: background 0.15s;
}
.run-btn:hover { background: #00cc7a; }
.clear-btn {
  padding: 6px 12px;
  background: var(--bg3);
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  font-size: 11px;
}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="logo">
    <div class="logo-dot"></div>
    <span class="logo-text">MANTHAN AI</span>
  </div>
  <span class="server-status" id="server-status">⚡ localhost:8000</span>
</div>

<!-- Tabs -->
<div class="tabs">
  <div class="tab active" data-tab="chat">💬 Chat</div>
  <div class="tab" data-tab="run">▶ Runner</div>
  <div class="tab" data-tab="upload">📁 Upload</div>
</div>

<!-- ═══════════════════════════════════════ -->
<!-- TAB 1: CHAT                            -->
<!-- ═══════════════════════════════════════ -->
<div class="panel active" id="panel-chat">

  <!-- Task Buttons -->
  <div class="task-row">
    <button class="task-btn active" data-task="chat">💬 Chat</button>
    <button class="task-btn" data-task="fix">🐛 Fix</button>
    <button class="task-btn" data-task="explain">💡 Explain</button>
    <button class="task-btn" data-task="enhance">⚡ Enhance</button>
    <button class="task-btn" data-task="generate">✨ Generate</button>
    <button class="task-btn" data-task="review">🔍 Review</button>
  </div>

  <!-- Chat History -->
  <div class="chat-history" id="chat-history">
    <div class="msg msg-system">👋 Namaste! Manthan AI ready hai.</div>
    <div class="msg msg-ai">Koi bhi code select karo aur right-click karo — Fix, Explain, ya Enhance kar sakte ho!\n\nYa yahan seedha poochhte raho 🚀</div>
  </div>

  <!-- Input -->
  <div class="input-row">
    <textarea id="chat-input" placeholder="Yahan type karo... (Ctrl+Enter = Send)" rows="3"></textarea>
    <button class="send-btn" id="chat-send">➤</button>
  </div>
</div>

<!-- ═══════════════════════════════════════ -->
<!-- TAB 2: CODE RUNNER                     -->
<!-- ═══════════════════════════════════════ -->
<div class="panel" id="panel-run">

  <div class="run-controls">
    <select class="lang-select" id="lang-select">
      <option value="python">🐍 Python</option>
      <option value="javascript">🟨 JavaScript</option>
      <option value="typescript">🔷 TypeScript</option>
      <option value="java">☕ Java</option>
      <option value="cpp">⚙️ C++</option>
    </select>
    <button class="run-btn" id="run-btn">▶ Run & Explain</button>
    <button class="clear-btn" id="clear-run">Clear</button>
  </div>

  <textarea class="code-input" id="code-input" placeholder="Yahan apna code paste karo..." style="height:180px; flex-shrink:0;"></textarea>

  <div style="font-size:10px; color: var(--muted); flex-shrink:0;">AI Output / Explanation:</div>
  <div class="run-output" id="run-output">// Output yahan dikhega...</div>

</div>

<!-- ═══════════════════════════════════════ -->
<!-- TAB 3: FILE UPLOAD                     -->
<!-- ═══════════════════════════════════════ -->
<div class="panel" id="panel-upload">

  <div class="upload-zone" id="upload-zone">
    <div class="upload-icon">📂</div>
    <p><strong>Click karo ya file drag karo</strong></p>
    <p style="margin-top:4px; font-size:10px;">.py .js .ts .txt .json .md files supported</p>
  </div>
  <input type="file" id="file-input" accept=".py,.js,.ts,.jsx,.tsx,.txt,.json,.md,.html,.css,.cpp,.java">

  <div style="font-size:10px; color: var(--muted); flex-shrink:0;">Analyzed Files:</div>
  <div class="file-list" id="file-list">
    <div style="color: var(--muted); font-size:11px; text-align:center; padding:20px;">Abhi koi file upload nahi ki</div>
  </div>

</div>

<script>
const vscode = acquireVsCodeApi();

// ── Tab Switching ─────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
  });
});

// ── Task Buttons ──────────────────────────
let currentTask = 'chat';
document.querySelectorAll('.task-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.task-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentTask = btn.dataset.task;
  });
});

// ── Chat ──────────────────────────────────
const chatHistory = document.getElementById('chat-history');
const chatInput   = document.getElementById('chat-input');
const chatSend    = document.getElementById('chat-send');
let chatLoading   = null;

function addMsg(text, type) {
  const d = document.createElement('div');
  d.className = 'msg msg-' + type;
  d.textContent = text;
  chatHistory.appendChild(d);
  chatHistory.scrollTop = chatHistory.scrollHeight;
  return d;
}

function sendChat() {
  const text = chatInput.value.trim();
  if (!text) return;
  addMsg(text, 'user');
  chatInput.value = '';
  chatSend.disabled = true;
  vscode.postMessage({ type: 'askAI', task: currentTask, message: text });
}

chatSend.addEventListener('click', sendChat);
chatInput.addEventListener('keydown', e => { if (e.ctrlKey && e.key === 'Enter') sendChat(); });

// ── Code Runner ───────────────────────────
const codeInput = document.getElementById('code-input');
const runOutput = document.getElementById('run-output');
const runBtn    = document.getElementById('run-btn');

document.getElementById('clear-run').addEventListener('click', () => {
  codeInput.value = '';
  runOutput.textContent = '// Output yahan dikhega...';
});

runBtn.addEventListener('click', () => {
  const code = codeInput.value.trim();
  if (!code) { runOutput.textContent = '⚠️ Pehle code likho!'; return; }
  const lang = document.getElementById('lang-select').value;
  runOutput.textContent = '⏳ AI analyze kar raha hai...';
  runBtn.disabled = true;
  vscode.postMessage({ type: 'runCode', code, language: lang });
});

// ── File Upload ───────────────────────────
const uploadZone = document.getElementById('upload-zone');
const fileInput  = document.getElementById('file-input');
const fileList   = document.getElementById('file-list');

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('drag');
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', e => { if (e.target.files[0]) handleFile(e.target.files[0]); });

function handleFile(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const content = e.target.result;

    // Placeholder dikhao
    if (fileList.children.length === 1 && fileList.children[0].style.textAlign === 'center') {
      fileList.innerHTML = '';
    }
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = '<div class="file-name">📄 ' + file.name + '</div><div class="file-resp" style="color:var(--muted)">⏳ Analyzing...</div>';
    fileList.appendChild(item);

    vscode.postMessage({ type: 'uploadFile', fileData: content, fileName: file.name, workspaceId: 'default' });
    fileInput.value = '';
  };
  reader.readAsText(file);
}

// ── Messages from Extension ───────────────
window.addEventListener('message', event => {
  const msg = event.data;

  // Chat responses
  if (msg.type === 'showLoading') {
    if (msg.tab === 'chat') chatLoading = addMsg('⏳ Manthan AI soch raha hai...', 'loading');
  }
  else if (msg.type === 'chatResponse') {
    if (chatLoading) { chatLoading.remove(); chatLoading = null; }
    addMsg(msg.value, 'ai');
    chatSend.disabled = false;
  }
  else if (msg.type === 'addUserMessage') {
    addMsg(msg.value, 'user');
    // Switch to chat tab
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.querySelector('[data-tab="chat"]').classList.add('active');
    document.getElementById('panel-chat').classList.add('active');
  }

  // Run responses
  else if (msg.type === 'runResponse') {
    runOutput.textContent = msg.value;
    runBtn.disabled = false;
  }

  // Upload responses
  else if (msg.type === 'uploadResponse') {
    const items = fileList.querySelectorAll('.file-item');
    const lastItem = items[items.length - 1];
    if (lastItem) {
      lastItem.querySelector('.file-resp').textContent = msg.value;
      lastItem.querySelector('.file-resp').style.color = 'var(--text)';
    }
  }
});
</script>
</body>
</html>`;
    }
}

module.exports = { SidebarProvider };