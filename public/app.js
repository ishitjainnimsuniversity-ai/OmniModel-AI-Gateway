/**
 * GENESIS AI 5.0 - Universal ChatGPT-Style Cognitive Operating System & GUI Controller
 * 2026 Edition
 */

// ==========================================
// 1. STATE & LOCAL PERSISTENCE
// ==========================================
const state = {
    activeTab: 'chat',
    activeModel: 'auto',
    activeProfile: 'auto',
    currentChatId: null,
    chats: {}, // { id: { id, title, model, profile, timestamp, messages: [] } }
    isStreaming: false,
    soundEffects: true,
    activeTheme: 'quantum',
    providers: {},
    searchToggled: false,
    reasonToggled: false,
    startTime: 0,
    tokenCounter: 0,
};

// ==========================================
// 2. AUDIO SYNTHESIS ENGINE (Sci-Fi Sound FX)
// ==========================================
class SoundFX {
    constructor() { this.ctx = null; }
    init() {
        if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
    }
    playClick() {
        if (!state.soundEffects) return;
        this.init();
        if (!this.ctx) return;
        try {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(800, this.ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(1200, this.ctx.currentTime + 0.04);
            gain.gain.setValueAtTime(0.06, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.04);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.04);
        } catch(e) {}
    }
    playTransmit() {
        if (!state.soundEffects) return;
        this.init();
        if (!this.ctx) return;
        try {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(440, this.ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(880, this.ctx.currentTime + 0.1);
            gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.1);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.1);
        } catch(e) {}
    }
    playComplete() {
        if (!state.soundEffects) return;
        this.init();
        if (!this.ctx) return;
        try {
            const now = this.ctx.currentTime;
            const osc1 = this.ctx.createOscillator();
            const osc2 = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc1.type = 'sine';
            osc2.type = 'sine';
            osc1.frequency.setValueAtTime(587.33, now);
            osc2.frequency.setValueAtTime(880, now + 0.06);
            gain.gain.setValueAtTime(0.06, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
            osc1.connect(gain);
            osc2.connect(gain);
            gain.connect(this.ctx.destination);
            osc1.start(now);
            osc1.stop(now + 0.06);
            osc2.start(now + 0.06);
            osc2.stop(now + 0.22);
        } catch(e) {}
    }
}
const sfx = new SoundFX();

// ==========================================
// 3. INTERACTIVE PARTICLE CANVAS BACKGROUND
// ==========================================
function initNeuralCanvas() {
    const canvas = document.getElementById('neural-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const particleCount = Math.min(Math.floor((width * height) / 18000), 75);

    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.35,
            vy: (Math.random() - 0.5) * 0.35,
            radius: Math.random() * 2 + 1,
            alpha: Math.random() * 0.5 + 0.2
        });
    }

    let mouse = { x: null, y: null };
    window.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    function draw() {
        ctx.clearRect(0, 0, width, height);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0 || p.x > width) p.vx *= -1;
            if (p.y < 0 || p.y > height) p.vy *= -1;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 240, 255, ${p.alpha})`;
            ctx.fill();

            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 130) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(0, 240, 255, ${0.12 * (1 - dist / 130)})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }

            if (mouse.x !== null) {
                const mdx = p.x - mouse.x;
                const mdy = p.y - mouse.y;
                const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
                if (mdist < 140) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.strokeStyle = `rgba(139, 92, 246, ${0.25 * (1 - mdist / 140)})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }
    draw();
}

// ==========================================
// 4. CHATGPT MULTI-CONVERSATION MANAGER
// ==========================================
function loadSavedChats() {
    try {
        const raw = localStorage.getItem('genesis_chats');
        if (raw) state.chats = JSON.parse(raw);
    } catch(e) { state.chats = {}; }

    renderChatHistory();

    const chatIds = Object.keys(state.chats);
    if (chatIds.length > 0) {
        switchChat(chatIds[chatIds.length - 1]);
    } else {
        createNewChat();
    }
}

function saveChatsToStorage() {
    try {
        localStorage.setItem('genesis_chats', JSON.stringify(state.chats));
    } catch(e) {}
}

function createNewChat() {
    const id = 'chat-' + Date.now();
    state.currentChatId = id;
    state.chats[id] = {
        id: id,
        title: 'New chat',
        model: state.activeModel,
        profile: state.activeProfile,
        timestamp: Date.now(),
        messages: []
    };
    saveChatsToStorage();
    renderChatHistory();
    renderChatMessages();
    sfx.playClick();
}

function switchChat(chatId) {
    if (!state.chats[chatId]) return;
    state.currentChatId = chatId;
    renderChatHistory();
    renderChatMessages();
    sfx.playClick();
}

function deleteChat(chatId, e) {
    if (e) e.stopPropagation();
    delete state.chats[chatId];
    saveChatsToStorage();
    const remaining = Object.keys(state.chats);
    if (remaining.length > 0) {
        switchChat(remaining[remaining.length - 1]);
    } else {
        createNewChat();
    }
    showToast('Chat deleted');
    sfx.playClick();
}

function renderChatHistory() {
    const container = document.getElementById('chat-history-list');
    if (!container) return;

    container.innerHTML = '';
    const sorted = Object.values(state.chats).sort((a, b) => b.timestamp - a.timestamp);

    sorted.forEach(chat => {
        const item = document.createElement('div');
        item.className = `history-item ${chat.id === state.currentChatId ? 'active' : ''}`;
        item.innerHTML = `
            <span class="history-title"><i class="fa-regular fa-message" style="margin-right:8px; font-size:11px;"></i>${escapeHtml(chat.title)}</span>
            <div class="history-actions">
                <button class="history-btn" title="Delete chat" onclick="deleteChat('${chat.id}', event)"><i class="fa-solid fa-trash-can"></i></button>
            </div>
        `;
        item.onclick = () => switchChat(chat.id);
        container.appendChild(item);
    });
}

function renderChatMessages() {
    const feed = document.getElementById('chat-messages');
    if (!feed) return;

    const chat = state.chats[state.currentChatId];
    if (!chat || !chat.messages || chat.messages.length === 0) {
        feed.innerHTML = `
            <div class="chatgpt-welcome" id="chatgpt-welcome-screen">
                <div class="welcome-hero-logo">
                    <img src="logo.png" alt="GENESIS AI 5.0" class="hero-logo-img">
                    <div class="hero-logo-halo"></div>
                </div>
                <h1>What can I help with today?</h1>
                <p class="welcome-tagline">GENESIS AI 5.0 connects 20+ frontier models with instant auto-routing, deep reasoning, and zero-cost fallbacks.</p>
                <div class="chatgpt-prompt-cards">
                    <button class="prompt-card" data-prompt="Explain quantum key distribution (BB84 protocol) with a complete Python simulation script.">
                        <div class="card-icon"><i class="fa-solid fa-atom"></i></div>
                        <div class="card-text">
                            <strong>Quantum Key Distribution</strong>
                            <span>BB84 simulation with Python code</span>
                        </div>
                    </button>
                    <button class="prompt-card" data-prompt="Prove by mathematical induction that for all n >= 1: 1 + 2 + 3 + ... + n = n(n+1)/2. Show full reasoning.">
                        <div class="card-icon"><i class="fa-solid fa-brain"></i></div>
                        <div class="card-text">
                            <strong>Mathematical Induction Proof</strong>
                            <span>Deep step-by-step reasoning proof</span>
                        </div>
                    </button>
                    <button class="prompt-card" data-prompt="Compare Transformer attention mechanisms vs Mamba state-space models in 3 ultra-fast bullet points.">
                        <div class="card-icon"><i class="fa-solid fa-bolt"></i></div>
                        <div class="card-text">
                            <strong>Transformer vs Mamba</strong>
                            <span>Ultra-speed architectural summary</span>
                        </div>
                    </button>
                    <button class="prompt-card" data-prompt="What are the latest frontier AI agent advancements and breakthroughs in 2026?">
                        <div class="card-icon"><i class="fa-solid fa-globe"></i></div>
                        <div class="card-text">
                            <strong>2026 AI Agent Advancements</strong>
                            <span>Autonomous multi-agent research</span>
                        </div>
                    </button>
                </div>
            </div>
        `;
        bindPromptCards();
        return;
    }

    feed.innerHTML = '';
    chat.messages.forEach(msg => {
        if (msg.role === 'user') {
            const userWrap = document.createElement('div');
            userWrap.className = 'message-wrap user';
            userWrap.innerHTML = `
                <div class="msg-content-box">${escapeHtml(msg.content)}</div>
            `;
            feed.appendChild(userWrap);
        } else {
            const aiWrap = document.createElement('div');
            aiWrap.className = 'message-wrap ai';
            const parsedHtml = window.marked ? marked.parse(msg.content) : escapeHtml(msg.content);
            aiWrap.innerHTML = `
                <div class="msg-avatar-col">
                    <div class="msg-ai-avatar"><i class="fa-solid fa-brain-circuit"></i></div>
                </div>
                <div class="msg-content-box">
                    ${parsedHtml}
                    <div class="msg-actions-strip">
                        <button class="msg-action-btn" title="Copy text" onclick="copyRawText(this)"><i class="fa-regular fa-copy"></i></button>
                        <button class="msg-action-btn" title="Speak aloud" onclick="speakRawText(this)"><i class="fa-solid fa-volume-high"></i></button>
                    </div>
                </div>
            `;
            feed.appendChild(aiWrap);
        }
    });

    // Code syntax highlighting
    if (window.hljs) {
        feed.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
    }
    feed.scrollTop = feed.scrollHeight;
}

function bindPromptCards() {
    document.querySelectorAll('.prompt-card').forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.dataset.prompt;
            const input = document.getElementById('chat-input');
            if (input) {
                input.value = prompt;
                submitChatMessage();
            }
        });
    });
}

// ==========================================
// 5. SIDEBAR & NAVIGATION CONTROLS
// ==========================================
function initNavigation() {
    const sidebar = document.getElementById('app-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    const newChatBtn = document.getElementById('new-chat-btn');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            sfx.playClick();
        });
    }

    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChat);
    }

    // Keyboard shortcut Ctrl+K
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            createNewChat();
        }
    });

    // Workspace Navigation Tabs
    const navItems = document.querySelectorAll('.side-nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabName = item.dataset.tab;
            sfx.playClick();
            switchWorkspaceTab(tabName);
        });
    });

    // Model Dropdown Trigger (Top Bar)
    const modelBtn = document.getElementById('model-dropdown-trigger');
    const modelMenu = document.getElementById('model-dropdown-menu');
    if (modelBtn && modelMenu) {
        modelBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            modelMenu.classList.toggle('hidden');
            sfx.playClick();
        });

        document.addEventListener('click', () => {
            modelMenu.classList.add('hidden');
        });

        document.querySelectorAll('.model-option').forEach(opt => {
            opt.addEventListener('click', () => {
                const model = opt.dataset.model;
                const profile = opt.dataset.profile;
                state.activeModel = model;
                state.activeProfile = profile;

                document.querySelectorAll('.model-option').forEach(o => o.classList.remove('active'));
                opt.classList.add('active');

                const label = document.getElementById('header-model-label');
                const badge = document.getElementById('header-model-badge');
                if (label) label.innerText = opt.querySelector('.model-opt-title').childNodes[0].nodeValue.trim();
                if (badge) badge.innerText = profile.toUpperCase();

                showToast(`Model switched to ${model}`);
                sfx.playClick();
            });
        });
    }

    // Theme Picker
    const themeBtn = document.getElementById('theme-btn');
    const themeMenu = document.getElementById('theme-menu');
    if (themeBtn && themeMenu) {
        themeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            themeMenu.classList.toggle('hidden');
            sfx.playClick();
        });
        document.addEventListener('click', () => themeMenu.classList.add('hidden'));

        document.querySelectorAll('.theme-opt').forEach(opt => {
            opt.addEventListener('click', () => {
                const chosen = opt.dataset.setTheme;
                document.documentElement.setAttribute('data-theme', chosen);
                document.querySelectorAll('.theme-opt').forEach(o => o.classList.remove('active'));
                opt.classList.add('active');
                state.activeTheme = chosen;
                showToast(`Theme: ${chosen.toUpperCase()}`);
                sfx.playClick();
            });
        });
    }

    // Audio SFX Toggle
    const sfxBtn = document.getElementById('sfx-toggle-btn');
    if (sfxBtn) {
        sfxBtn.addEventListener('click', () => {
            state.soundEffects = !state.soundEffects;
            sfxBtn.classList.toggle('active', state.soundEffects);
            sfxBtn.innerHTML = state.soundEffects ? '<i class="fa-solid fa-volume-high"></i>' : '<i class="fa-solid fa-volume-xmark"></i>';
            showToast(state.soundEffects ? 'Sound FX On' : 'Sound FX Off');
            if (state.soundEffects) sfx.playClick();
        });
    }

    // Fullscreen
    const fsBtn = document.getElementById('fullscreen-btn');
    if (fsBtn) {
        fsBtn.addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(() => {});
            } else {
                document.exitFullscreen().catch(() => {});
            }
            sfx.playClick();
        });
    }

    // Settings trigger
    document.getElementById('open-settings-btn')?.addEventListener('click', () => {
        openKeyModal('gemini', 'Google Gemini (Free Tier)', 'GEMINI_API_KEY', 'https://aistudio.google.com/app/apikey');
    });
}

function switchWorkspaceTab(tabName) {
    state.activeTab = tabName;
    document.querySelectorAll('.side-nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.tab === tabName);
    });
    document.querySelectorAll('.workspace-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `tab-${tabName}`);
    });

    if (tabName === 'providers') loadProviders();
    if (tabName === 'analytics') loadAnalytics();
}

// ==========================================
// 6. CHATGPT INPUT & STREAM CONTROLLER
// ==========================================
function initChatInput() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const searchBtn = document.getElementById('toggle-search-btn');
    const reasonBtn = document.getElementById('toggle-reason-btn');

    if (input) {
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 140) + 'px';
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitChatMessage();
            }
        });
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', submitChatMessage);
    }

    // Search Toggle Button
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            state.searchToggled = !state.searchToggled;
            searchBtn.classList.toggle('active', state.searchToggled);
            if (state.searchToggled) {
                state.activeProfile = 'search';
                state.activeModel = 'genesis-5.0-search';
            } else {
                state.activeProfile = 'auto';
                state.activeModel = 'auto';
            }
            sfx.playClick();
        });
    }

    // Reason Toggle Button
    if (reasonBtn) {
        reasonBtn.addEventListener('click', () => {
            state.reasonToggled = !state.reasonToggled;
            reasonBtn.classList.toggle('active', state.reasonToggled);
            if (state.reasonToggled) {
                state.activeProfile = 'reasoning';
                state.activeModel = 'genesis-5.0-reasoning';
            } else {
                state.activeProfile = 'auto';
                state.activeModel = 'auto';
            }
            sfx.playClick();
        });
    }

    initVoiceInput();
}

async function submitChatMessage() {
    const input = document.getElementById('chat-input');
    const prompt = input.value.trim();
    if (!prompt || state.isStreaming) return;

    input.value = '';
    input.style.height = 'auto';
    state.isStreaming = true;
    sfx.playTransmit();

    if (!state.currentChatId || !state.chats[state.currentChatId]) {
        createNewChat();
    }

    const currentChat = state.chats[state.currentChatId];

    // Set title from first user prompt
    if (currentChat.messages.length === 0) {
        currentChat.title = prompt.length > 28 ? prompt.substring(0, 28) + '...' : prompt;
        renderChatHistory();
    }

    // Add user message
    currentChat.messages.push({ role: 'user', content: prompt });
    saveChatsToStorage();

    const feed = document.getElementById('chat-messages');
    const welcome = document.getElementById('chatgpt-welcome-screen');
    if (welcome) welcome.remove();

    // Render User Message
    const userWrap = document.createElement('div');
    userWrap.className = 'message-wrap user';
    userWrap.innerHTML = `<div class="msg-content-box">${escapeHtml(prompt)}</div>`;
    feed.appendChild(userWrap);

    // AI Message Placeholder
    const aiWrap = document.createElement('div');
    aiWrap.className = 'message-wrap ai';
    const msgId = 'msg-' + Date.now();
    aiWrap.innerHTML = `
        <div class="msg-avatar-col">
            <div class="msg-ai-avatar"><i class="fa-solid fa-brain-circuit"></i></div>
        </div>
        <div class="msg-content-box" id="${msgId}-content">
            <div class="thought-accordion hidden" id="${msgId}-thought">
                <div class="thought-header" onclick="toggleThought('${msgId}')">
                    <i class="fa-solid fa-brain"></i>
                    <span>Thinking Process...</span>
                    <i class="fa-solid fa-chevron-down" style="margin-left:auto; font-size:10px;"></i>
                </div>
                <div class="thought-body" id="${msgId}-thought-body"></div>
            </div>
            <div class="msg-text-body" id="${msgId}-body"><span class="typing-cursor">▌</span></div>
        </div>
    `;
    feed.appendChild(aiWrap);
    feed.scrollTop = feed.scrollHeight;

    // Stream SSE
    state.startTime = performance.now();
    state.tokenCounter = 0;

    try {
        const payload = {
            prompt: prompt,
            profile: state.activeProfile,
            model: state.activeModel !== 'auto' ? state.activeModel : undefined,
            temperature: 0.7,
            stream: true
        };

        const res = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        const bodyEl = document.getElementById(`${msgId}-body`);

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6).trim();
                    if (!dataStr) continue;

                    try {
                        const parsed = JSON.parse(dataStr);
                        if (parsed.content) {
                            fullText += parsed.content;
                            state.tokenCounter += parsed.content.split(/\s+/).length || 1;

                            if (window.marked) {
                                bodyEl.innerHTML = marked.parse(fullText);
                            } else {
                                bodyEl.innerText = fullText;
                            }

                            // Live tok/s velocity
                            const elapsedSec = (performance.now() - state.startTime) / 1000;
                            const speed = Math.round(state.tokenCounter / (elapsedSec || 1));
                            const hudSpeed = document.getElementById('hud-tok-speed');
                            if (hudSpeed) hudSpeed.innerText = `${speed} tok/s`;
                        }
                    } catch(e) {}
                }
            }
            feed.scrollTop = feed.scrollHeight;
        }

        // Save AI message to history
        currentChat.messages.push({ role: 'assistant', content: fullText });
        saveChatsToStorage();

        // Highlight code
        if (window.hljs) {
            bodyEl.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
        }

        // Add action buttons
        const contentBox = document.getElementById(`${msgId}-content`);
        if (contentBox) {
            const actions = document.createElement('div');
            actions.className = 'msg-actions-strip';
            actions.innerHTML = `
                <button class="msg-action-btn" title="Copy text" onclick="copyRawText(this)"><i class="fa-regular fa-copy"></i></button>
                <button class="msg-action-btn" title="Speak aloud" onclick="speakRawText(this)"><i class="fa-solid fa-volume-high"></i></button>
            `;
            contentBox.appendChild(actions);
        }

        sfx.playComplete();

    } catch(err) {
        const bodyEl = document.getElementById(`${msgId}-body`);
        if (bodyEl) bodyEl.innerHTML = `<span style="color:var(--accent-rose)"><i class="fa-solid fa-triangle-exclamation"></i> Error: ${err.message}</span>`;
    } finally {
        state.isStreaming = false;
    }
}

window.toggleThought = function(msgId) {
    const body = document.getElementById(`${msgId}-thought-body`);
    if (body) body.classList.toggle('hidden');
    sfx.playClick();
};

window.copyRawText = function(btn) {
    const parentBox = btn.closest('.msg-content-box');
    if (parentBox) {
        const text = parentBox.querySelector('.msg-text-body')?.innerText || parentBox.innerText;
        navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!');
        sfx.playClick();
    }
};

window.speakRawText = function(btn) {
    const parentBox = btn.closest('.msg-content-box');
    if (parentBox && window.speechSynthesis) {
        window.speechSynthesis.cancel();
        const text = parentBox.querySelector('.msg-text-body')?.innerText || parentBox.innerText;
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        window.speechSynthesis.speak(utterance);
        showToast('Reading response aloud...');
        sfx.playClick();
    }
};

// ==========================================
// 7. VOICE INPUT (Speech-to-Text)
// ==========================================
function initVoiceInput() {
    const micBtn = document.getElementById('voice-input-btn');
    const waveBar = document.getElementById('voice-wave-bar');
    const chatInput = document.getElementById('chat-input');

    if (!micBtn) return;
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;

    const recognition = new SpeechRec();
    recognition.continuous = false;
    recognition.interimResults = true;
    let isListening = false;

    micBtn.addEventListener('click', () => {
        if (!isListening) {
            recognition.start();
            isListening = true;
            micBtn.style.color = 'var(--accent-rose)';
            if (waveBar) waveBar.classList.remove('hidden');
            sfx.playTransmit();
        } else {
            recognition.stop();
            isListening = false;
            micBtn.style.color = '';
            if (waveBar) waveBar.classList.add('hidden');
        }
    });

    recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        if (chatInput) chatInput.value = transcript;
    };

    recognition.onend = () => {
        isListening = false;
        micBtn.style.color = '';
        if (waveBar) waveBar.classList.add('hidden');
    };
}

// ==========================================
// 8. 4-WAY MODEL ARENA CONTROLLER
// ==========================================
function initArena() {
    const broadcastBtn = document.getElementById('arena-broadcast-btn');
    const promptInput = document.getElementById('arena-prompt-input');

    if (!broadcastBtn || !promptInput) return;
    broadcastBtn.addEventListener('click', launchArenaDuel);
    promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') launchArenaDuel();
    });
}

async function launchArenaDuel() {
    const promptInput = document.getElementById('arena-prompt-input');
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    sfx.playTransmit();

    const selectedModels = [
        document.getElementById('arena-model-0').value,
        document.getElementById('arena-model-1').value,
        document.getElementById('arena-model-2').value,
        document.getElementById('arena-model-3').value,
    ];

    for (let i = 0; i < 4; i++) {
        const bodyEl = document.getElementById(`arena-body-${i}`);
        const metricEl = document.getElementById(`arena-metric-${i}`);
        const nameEl = document.getElementById(`arena-name-${i}`);
        if (bodyEl) bodyEl.innerHTML = '<span class="typing-cursor">▌ Generating stream...</span>';
        if (metricEl) metricEl.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Racing...';
        if (nameEl) nameEl.innerText = selectedModels[i];
    }

    selectedModels.forEach((modelKey, index) => {
        const [provider, model] = modelKey.split('/');
        const startTime = performance.now();

        fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt, provider: provider, model: model, stream: true })
        }).then(res => {
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let text = '';
            const bodyEl = document.getElementById(`arena-body-${index}`);
            const metricEl = document.getElementById(`arena-metric-${index}`);

            function readChunk() {
                reader.read().then(({ value, done }) => {
                    if (done) {
                        const totalLat = Math.round(performance.now() - startTime);
                        if (metricEl) metricEl.innerHTML = `<span style="color:var(--accent-emerald); font-weight:700;">✓ ${totalLat} ms</span>`;
                        if (window.marked && bodyEl) bodyEl.innerHTML = marked.parse(text);
                        return;
                    }
                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const p = JSON.parse(line.slice(6));
                                if (p.content) text += p.content;
                            } catch(e) {}
                        }
                    }
                    if (bodyEl) bodyEl.innerText = text;
                    readChunk();
                });
            }
            readChunk();
        }).catch(err => {
            const bodyEl = document.getElementById(`arena-body-${index}`);
            const metricEl = document.getElementById(`arena-metric-${index}`);
            if (bodyEl) bodyEl.innerHTML = `<span style="color:var(--accent-rose)">Failed: ${err.message}</span>`;
            if (metricEl) metricEl.innerText = "Error";
        });
    });
}

// ==========================================
// 9. PROVIDERS DIRECTORY & KEYS
// ==========================================
async function loadProviders() {
    const container = document.getElementById('providers-grid-container');
    if (!container) return;

    try {
        const res = await fetch('/api/providers');
        const data = await res.json();
        state.providers = data.providers || {};

        container.innerHTML = '';
        Object.entries(state.providers).forEach(([pid, p]) => {
            const isConfigured = p.configured;
            const card = document.createElement('div');
            card.className = 'provider-card glass-panel';
            card.innerHTML = `
                <div class="provider-card-header">
                    <div class="provider-info">
                        <h4>${p.name}</h4>
                        <span class="provider-cat">${p.category.toUpperCase()} • ${p.models ? p.models.length : 0} Models</span>
                    </div>
                    <span class="provider-status-badge ${isConfigured ? 'status-active' : 'status-missing'}">
                        <i class="fa-solid ${isConfigured ? 'fa-circle-check' : 'fa-circle-exclamation'}"></i>
                        ${isConfigured ? 'Active' : 'Missing Key'}
                    </span>
                </div>
                <div class="provider-meta-notes">
                    ${p.notes || 'Frontier AI ecosystem integrated with streaming support.'}
                </div>
                <div class="provider-actions">
                    <button class="ping-btn" onclick="pingProvider('${pid}')" id="ping-${pid}">
                        <i class="fa-solid fa-satellite-dish"></i> Ping Latency
                    </button>
                    <button class="config-btn" onclick="openKeyModal('${pid}', '${p.name}', '${p.env_key}', '${p.docs_url}')">
                        <i class="fa-solid fa-gear"></i> ${isConfigured ? 'Update Key' : 'Configure Key'}
                    </button>
                </div>
            `;
            container.appendChild(card);
        });

        const pingAllBtn = document.getElementById('ping-all-btn');
        if (pingAllBtn) {
            pingAllBtn.onclick = () => {
                sfx.playTransmit();
                Object.keys(state.providers).forEach(pid => pingProvider(pid));
            };
        }
    } catch(e) {}
}

window.pingProvider = async function(pid) {
    const btn = document.getElementById(`ping-${pid}`);
    if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Pinging...';
    const start = performance.now();
    try {
        await fetch(`/api/providers`);
        const lat = Math.round(performance.now() - start);
        if (btn) btn.innerHTML = `<span style="color:var(--accent-emerald)"><i class="fa-solid fa-check"></i> ${lat} ms</span>`;
    } catch(e) {
        if (btn) btn.innerHTML = `<span style="color:var(--accent-rose)">Offline</span>`;
    }
};

window.openKeyModal = function(pid, name, envKey, docsUrl) {
    const modal = document.getElementById('key-modal');
    const nameEl = document.getElementById('modal-provider-name');
    const descEl = document.getElementById('modal-provider-desc');
    const envLabel = document.getElementById('modal-env-label');
    const linkEl = document.getElementById('modal-key-link');
    const keyInput = document.getElementById('modal-key-input');

    if (!modal) return;
    nameEl.innerText = `Configure ${name}`;
    descEl.innerText = `Enter the API key for ${name}. Saved locally in .env.`;
    envLabel.innerText = `Environment Variable: ${envKey}`;
    linkEl.href = docsUrl || '#';
    keyInput.value = '';

    modal.classList.remove('hidden');
    sfx.playClick();

    document.getElementById('modal-save-btn').onclick = async () => {
        const val = keyInput.value.trim();
        if (!val) return;
        try {
            await fetch('/api/keys', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ env_key: envKey, api_key: val })
            });
            showToast(`${name} key updated!`);
            modal.classList.add('hidden');
            loadProviders();
            sfx.playComplete();
        } catch(e) {
            showToast(`Error: ${e.message}`);
        }
    };
};

document.getElementById('modal-close-btn')?.addEventListener('click', () => {
    document.getElementById('key-modal')?.classList.add('hidden');
});
document.getElementById('modal-cancel-btn')?.addEventListener('click', () => {
    document.getElementById('key-modal')?.classList.add('hidden');
});

// ==========================================
// 10. REAL-TIME USER ANALYTICS
// ==========================================
async function loadAnalytics() {
    try {
        const res = await fetch('/api/analytics');
        const data = await res.json();

        document.getElementById('kpi-users').innerText = data.total_users || 0;
        document.getElementById('kpi-requests').innerText = data.total_requests || 0;
        document.getElementById('kpi-tokens').innerText = (data.total_tokens || 0).toLocaleString();
        document.getElementById('kpi-latency').innerText = `${Math.round(data.average_latency_ms || 0)} ms`;

        const tbody = document.getElementById('analytics-tbody');
        if (tbody) {
            tbody.innerHTML = '';
            const logs = data.recent_logs || [];
            if (logs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:20px;">No requests recorded yet. Make a query to see live telemetry!</td></tr>`;
            } else {
                logs.forEach(log => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${escapeHtml(log.timestamp || '')}</td>
                        <td><code>${escapeHtml(log.client_ip || '127.0.0.1')}</code></td>
                        <td>${escapeHtml(log.platform || 'Antigravity / Web')}</td>
                        <td><strong>${escapeHtml(log.provider || '')}</strong> / ${escapeHtml(log.model || '')}</td>
                        <td>${Math.round(log.latency_ms || 0)} ms</td>
                        <td><span style="color:var(--accent-emerald); font-weight:700;">SUCCESS</span></td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }
    } catch(e) {}
}

document.getElementById('refresh-analytics-btn')?.addEventListener('click', () => {
    loadAnalytics();
    sfx.playClick();
    showToast('Analytics Refreshed');
});

// ==========================================
// 11. GRAPH SIMULATION & TOAST UTILITIES
// ==========================================
function initGraph() {
    const simBtn = document.getElementById('simulate-graph-btn');
    if (!simBtn) return;
    simBtn.addEventListener('click', () => {
        sfx.playTransmit();
        document.querySelectorAll('.flow-line').forEach(l => {
            l.classList.add('active');
            setTimeout(() => l.classList.remove('active'), 2500);
        });
        showToast('Simulating Cognitive Routing Signal Flow across all Tiers');
    });
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.innerText = msg;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

document.querySelectorAll('.copy-code-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const targetId = btn.dataset.target;
        const codeEl = document.getElementById(targetId);
        if (codeEl) {
            navigator.clipboard.writeText(codeEl.innerText);
            showToast('Code copied to clipboard!');
            sfx.playClick();
        }
    });
});

// ==========================================
// 12. BOOTSTRAP APPLICATION
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    initNeuralCanvas();
    initNavigation();
    initChatInput();
    initArena();
    initGraph();
    loadSavedChats();
    loadProviders();
    loadAnalytics();
    setInterval(loadAnalytics, 10000);
});
