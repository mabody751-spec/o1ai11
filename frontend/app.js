const form = document.querySelector('#form') || null;
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

let history = [];
let messageCount = 0;

function addMessage(role, text) {
  if (welcome) welcome.style.display = 'none';
  const wrapper = document.createElement('div');
  wrapper.className = 'msg ' + role;
  const now = new Date();
  const time = now.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });
  const senderName = role === 'user' ? 'أنت' : 'o1ai';
  wrapper.innerHTML = `<div class="msg-meta"><span class="msg-sender">${senderName}</span><span>${time}</span></div><div>${escapeHtml(text)}</div>`;
  chat.appendChild(wrapper);
  wrapper.scrollIntoView({ behavior: 'smooth', block: 'end' });
  messageCount++;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
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
      body: JSON.stringify({ messages: history })
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

if (menuBtn) {
  menuBtn.addEventListener('click', () => {
    sidebar.classList.add('open');
    overlay.classList.add('active');
  });
}

if (closeSidebar) {
  closeSidebar.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  });
}

if (overlay) {
  overlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  });
}

if (newChatBtn) {
  newChatBtn.addEventListener('click', () => {
    history = [];
    messageCount = 0;
    chat.innerHTML = '';
    if (welcome) {
      welcome.style.display = '';
      chat.appendChild(welcome);
    }
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  });
}

updateCharCount();
