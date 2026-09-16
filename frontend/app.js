const input = document.querySelector('#input');
const chat = document.querySelector('#messages');
const status = document.querySelector('#statusText');
const welcome = document.querySelector('#welcome');
const typingIndicator = document.querySelector('#typingIndicator');
const sendBtn = document.querySelector('#sendBtn');
const charCount = document.querySelector('#charCount');
const sidebar = document.querySelector('#sidebar');
const overlay = document.querySelector('#overlay');
const menuBtn = document.querySelector('#menuBtn');
const closeSidebar = document.querySelector('#closeSidebar');
const newChatBtn = document.querySelector('#newChatBtn');
const suggestions = document.querySelector('#suggestions');
const actionBar = document.querySelector('#actionBar');

let history = [];
let messageCount = 0;

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function detectCodeLanguage(text) {
  const patterns = {
    python: ['\\bdef\\s+\\w+\\s*\\(', '\\bimport\\s+\\w+', '\\bfrom\\s+\\w+\\s+import', '\\bself\\.\\w+', '@\\w+\\s*\\(', '\\bprint\\s*\\(', '\\bclass\\s+\\w+'],
    javascript: ['\\bconst\\s+\\w+\\s*=', '\\bfunction\\s+\\w+\\s*\\(', '=>\\s*\\{', '\\.then\\s*\\(', 'console\\.log', '\\bvar\\s+\\w+\\s*='],
    html: ['<\\w+[^>]*>', '</\\w+>', '<!DOCTYPE'],
    css: ['\\.\\w+\\s*\\{', '@media', '@keyframes', 'display\\s*:'],
    sql: ['\\bSELECT\\b', '\\bINSERT\\s+INTO\\b', '\\bCREATE\\s+TABLE\\b', '\\bJOIN\\b', '\\bWHERE\\b'],
    bash: ['#!\\s*/bin', '\\$\\(', '\\becho\\b', '\\bgrep\\b'],
    java: ['\\bpublic\\s+(static\\s+)?class\\b', '\\bSystem\\.out\\.print', 'import\\s+java\\.\\'],
    cpp: ['#include\\s*<', 'cout\\s*<<', 'std::', 'class\\s+\\w+\\s*:'],
    go: ['\\bfunc\\s+\\w+\\s*\\(', '\\bpackage\\s+\\w+', 'fmt\\.Print', ':=[\\s]*'],
    rust: ['\\bfn\\s+\\w+\\s*\\(', '\\blet\\s+mut\\s+', 'println!\\s*\\(', '\\bimpl\\s+\\w+'],
    typescript: [':\\s*(string|number|boolean|any)\\b', 'interface\\s+\\w+', 'type\\s+\\w+\\s*='],
  };
  const scores = {};
  for (const [lang, pats] of Object.entries(patterns)) {
    let score = 0;
    for (const p of pats) {
      if (new RegExp(p).test(text)) score++;
    }
    if (score > 0) scores[lang] = score;
  }
  const entries = Object.entries(scores);
  if (!entries.length) return '';
  entries.sort((a, b) => b[1] - a[1]);
  return entries[0][0];
}

function formatMessage(text) {
  let html = escapeHtml(text);
  const codeBlocks = [];

  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const id = `cb-${codeBlocks.length}`;
    codeBlocks.push({ lang: lang || 'text', code: code.trim(), id });
    return `\n<div class="code-block-wrapper" id="${id}"></div>\n`;
  });

  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  html = html.replace(/\n/g, '<br>');

  setTimeout(() => {
    for (const cb of codeBlocks) {
      const el = document.getElementById(cb.id);
      if (!el) continue;
      el.innerHTML = `
        <div class="code-block-header">
          <span class="code-lang">${cb.lang}</span>
          <button class="copy-btn" onclick="copyCode('${cb.id}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            نسخ
          </button>
        </div>
        <pre><code>${escapeHtml(cb.code)}</code></pre>
      `;
    }
  }, 50);

  return html;
}

function copyCode(id) {
  const wrapper = document.getElementById(id);
  if (!wrapper) return;
  const code = wrapper.querySelector('pre code');
  if (!code) return;
  navigator.clipboard.writeText(code.textContent).then(() => {
    const btn = wrapper.querySelector('.copy-btn');
    if (btn) {
      btn.classList.add('copied');
      btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg> تم!';
      setTimeout(() => { btn.classList.remove('copied'); }, 2000);
    }
  });
}

function addMessage(role, text) {
  if (welcome) welcome.style.display = 'none';
  const wrapper = document.createElement('div');
  wrapper.className = 'msg ' + role;
  const now = new Date();
  const time = now.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });
  const senderName = role === 'user' ? 'أنت' : 'o1ai';
  wrapper.innerHTML = `<div class="msg-meta"><span class="msg-sender">${senderName}</span><span>${time}</span></div><div>${formatMessage(text)}</div>`;
  chat.appendChild(wrapper);
  wrapper.scrollIntoView({ behavior: 'smooth', block: 'end' });
  messageCount++;
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  input.style.height = 'auto';
  updateCharCount();
  addMessage('user', text);
  history.push({ role: 'user', content: text });
  if (status) status.textContent = 'يفكر...';
  if (sendBtn) sendBtn.classList.add('disabled');
  typingIndicator.classList.add('active');
  typingIndicator.scrollIntoView({ behavior: 'smooth', block: 'end' });
  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: history }),
    });
    const data = await r.json();
    typingIndicator.classList.remove('active');
    if (!r.ok) throw new Error(data.detail || 'تعذر الاتصال');
    const answer = data.message.content;
    addMessage('assistant', answer);
    history.push({ role: 'assistant', content: answer });
    if (status) status.textContent = 'جاهز';
  } catch (err) {
    typingIndicator.classList.remove('active');
    addMessage('assistant', 'حدث خطأ: ' + err.message);
    if (status) status.textContent = 'خطأ';
  } finally {
    if (sendBtn) sendBtn.classList.remove('disabled');
  }
}

async function sendCodeAction(action) {
  const text = input.value.trim();
  if (!text) return;
  const lang = detectCodeLanguage(text);
  input.value = '';
  input.style.height = 'auto';
  updateCharCount();
  addMessage('user', text);
  history.push({ role: 'user', content: text });
  if (status) status.textContent = 'يعمل...';
  if (sendBtn) sendBtn.classList.add('disabled');
  typingIndicator.classList.add('active');
  typingIndicator.scrollIntoView({ behavior: 'smooth', block: 'end' });
  try {
    let url = '/api/chat';
    let body = { messages: history };
    if (action !== 'chat') {
      url = `/api/code/${action}`;
      body = { code: text, language: lang };
    }
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    typingIndicator.classList.remove('active');
    if (!r.ok) throw new Error(data.detail || 'تعذر الاتصال');
    const answer = action === 'chat' ? data.message.content : data.explanation || data.formatted_code || data.analysis || 'لا توجد نتيجة';
    addMessage('assistant', answer);
    history.push({ role: 'assistant', content: answer });
    if (status) status.textContent = 'جاهز';
  } catch (err) {
    typingIndicator.classList.remove('active');
    addMessage('assistant', 'حدث خطأ: ' + err.message);
    if (status) status.textContent = 'خطأ';
  } finally {
    if (sendBtn) sendBtn.classList.remove('disabled');
  }
}

function updateCharCount() {
  if (!charCount || !input) return;
  const len = input.value.length;
  charCount.textContent = `${len} / 4000`;
  charCount.classList.remove('warning', 'danger');
  if (len > 3600) charCount.classList.add('danger');
  else if (len > 3200) charCount.classList.add('warning');
}

if (input) {
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 160) + 'px';
    updateCharCount();
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

if (sendBtn) {
  sendBtn.addEventListener('click', sendMessage);
}

if (suggestions) {
  suggestions.querySelectorAll('.suggestion').forEach(btn => {
    btn.addEventListener('click', () => {
      if (input) {
        input.value = btn.getAttribute('data-text');
        updateCharCount();
        input.focus();
      }
    });
  });
}

if (actionBar) {
  actionBar.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.getAttribute('data-action');
      sendCodeAction(action);
    });
  });
}

if (menuBtn) {
  menuBtn.addEventListener('click', () => { sidebar.classList.add('open'); overlay.classList.add('active'); });
}
if (closeSidebar) {
  closeSidebar.addEventListener('click', () => { sidebar.classList.remove('open'); overlay.classList.remove('active'); });
}
if (overlay) {
  overlay.addEventListener('click', () => { sidebar.classList.remove('open'); overlay.classList.remove('active'); });
}
if (newChatBtn) {
  newChatBtn.addEventListener('click', () => {
    history = [];
    messageCount = 0;
    chat.innerHTML = '';
    if (welcome) { welcome.style.display = ''; chat.appendChild(welcome); }
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  });
}

window.copyCode = copyCode;
