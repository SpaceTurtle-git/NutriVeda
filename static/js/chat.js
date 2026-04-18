/* ── CHAT STATE ── */
let chatOpen = false;
let chatHistory = [];  // [{role, content}]

/* ── TOGGLE CHAT WINDOW ── */
function toggleChat() {
  chatOpen = !chatOpen;
  const win  = document.getElementById('chat-window');
  const icon = document.getElementById('chat-icon');

  if (chatOpen) {
    win.classList.remove('hidden');
    icon.textContent = '✕';
    document.getElementById('chat-input').focus();
    scrollToBottom();
  } else {
    win.classList.add('hidden');
    icon.textContent = '🌿';
  }
}

/* ── SEND MESSAGE ── */
async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text  = input.value.trim();
  if (!text) return;

  input.value = '';

  // Add user bubble
  appendMessage('user', text);
  chatHistory.push({ role: 'user', content: text });

  // Thinking indicator
  const thinkingId = appendThinking();

  // Disable send while waiting
  document.getElementById('chat-send').disabled = true;

  try {
    const payload = {
      messages: chatHistory,
      user_context: typeof USER_DATA !== 'undefined' ? USER_DATA : null,
    };

    const res  = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    removeThinking(thinkingId);

    if (!res.ok) {
      appendMessage('assistant', '⚠️ Sorry, I encountered an error. Please try again.');
      return;
    }

    const reply = data.reply;
    chatHistory.push({ role: 'assistant', content: reply });
    appendMessage('assistant', reply);

  } catch (err) {
    removeThinking(thinkingId);
    appendMessage('assistant', '⚠️ Network error. Please check your connection.');
    console.error(err);
  } finally {
    document.getElementById('chat-send').disabled = false;
    input.focus();
  }
}

/* ── ENTER KEY TO SEND ── */
document.getElementById('chat-input')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

/* ── DOM HELPERS ── */
function appendMessage(role, text) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;

  // Simple markdown: bold **text**, line breaks
  const formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>');
  div.innerHTML = formatted;

  container.appendChild(div);
  scrollToBottom();
  return div;
}

let thinkingCounter = 0;
function appendThinking() {
  const id = `thinking-${thinkingCounter++}`;
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-msg thinking';
  div.id = id;
  div.innerHTML = `
    <span class="inline-flex gap-1 items-center">
      <span class="thinking-dot"></span>
      <span class="thinking-dot" style="animation-delay:0.2s"></span>
      <span class="thinking-dot" style="animation-delay:0.4s"></span>
    </span>
  `;
  container.appendChild(div);

  // Inject thinking dot animation if not present
  if (!document.getElementById('thinking-style')) {
    const style = document.createElement('style');
    style.id = 'thinking-style';
    style.textContent = `
      .thinking-dot {
        width: 6px; height: 6px;
        background: #2C2416;
        border-radius: 50%;
        display: inline-block;
        animation: blink 1s infinite;
      }
      @keyframes blink {
        0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
        40% { opacity: 1; transform: scale(1); }
      }
    `;
    document.head.appendChild(style);
  }

  scrollToBottom();
  return id;
}

function removeThinking(id) {
  document.getElementById(id)?.remove();
}

function scrollToBottom() {
  const el = document.getElementById('chat-messages');
  if (el) el.scrollTop = el.scrollHeight;
}
