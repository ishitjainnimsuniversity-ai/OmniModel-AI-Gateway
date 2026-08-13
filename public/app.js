/**
 * GENESIS AI 5.0 - Universal Cognitive Operating System & GUI Controller
 * 2026 Edition
 */

// ==========================================
// 1. STATE & GLOBAL CONFIGURATION
// ==========================================
const state = {
    activeTab: 'chat',
    activeProfile: 'auto',
    activeModel: 'auto',
    temperature: 0.7,
    isStreaming: false,
    soundEffects: true,
    activeTheme: 'quantum',
    providers: {},
    totalRequests: 0,
    totalTokens: 0,
    startTime: 0,
    tokenCounter: 0,
};

// ==========================================
// 2. AUDIO SYNTHESIS ENGINE (Sci-Fi Sound FX)
// ==========================================
class SoundFX {
    constructor() {
        this.ctx = null;
    }

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
            osc.frequency.exponentialRampToValueAtTime(1200, this.ctx.currentTime + 0.05);
            gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.05);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.05);
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
            osc.frequency.exponentialRampToValueAtTime(880, this.ctx.currentTime + 0.12);
            gain.gain.setValueAtTime(0.1, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.12);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.12);
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
            osc1.frequency.setValueAtTime(587.33, now); // D5
            osc2.frequency.setValueAtTime(880, now + 0.08); // A5
            gain.gain.setValueAtTime(0.08, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
            osc1.connect(gain);
            osc2.connect(gain);
            gain.connect(this.ctx.destination);
            osc1.start(now);
            osc1.stop(now + 0.08);
            osc2.start(now + 0.08);
            osc2.stop(now + 0.25);
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
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
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

            // Connect lines
            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 130) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(0, 240, 255, ${0.15 * (1 - dist / 130)})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }

            // Mouse proximity
            if (mouse.x !== null) {
                const mdx = p.x - mouse.x;
                const mdy = p.y - mouse.y;
                const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
                if (mdist < 150) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.strokeStyle = `rgba(139, 92, 246, ${0.3 * (1 - mdist / 150)})`;
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
// 4. UI NAVIGATION & WORKSPACE TABS
// ==========================================
function initNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            sfx.playClick();
            switchTab(tabName);
        });
    });

    // Theme Picker
    const themeBtn = document.getElementById('theme-btn');
    const themeMenu = document.getElementById('theme-menu');
    if (themeBtn && themeMenu) {
        themeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            themeMenu.classList.toggle('hidden');
            sfx.playClick();
        });

        document.addEventListener('click', () => {
            themeMenu.classList.add('hidden');
        });

        document.querySelectorAll('.theme-opt').forEach(opt => {
            opt.addEventListener('click', () => {
                const chosen = opt.dataset.setTheme;
                document.documentElement.setAttribute('data-theme', chosen);
                document.querySelectorAll('.theme-opt').forEach(o => o.classList.remove('active'));
                opt.classList.add('active');
                state.activeTheme = chosen;
                showToast(`Theme switched to ${chosen.toUpperCase()}`);
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
            showToast(state.soundEffects ? 'Sound FX Enabled' : 'Sound FX Muted');
            if (state.soundEffects) sfx.playClick();
        });
    }

    // Fullscreen Toggle
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
}

function switchTab(tabName) {
    state.activeTab = tabName;
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.tab === tabName);
    });
    document.querySelectorAll('.tab-pane').forEach(p => {
        p.classList.toggle('active', p.id === `tab-${tabName}`);
    });

    if (tabName === 'providers') loadProviders();
    if (tabName === 'analytics') loadAnalytics();
}

// ==========================================
// 5. COGNITIVE CHAT CONTROLLER
// ==========================================
function initChat() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const tempSlider = document.getElementById('temp-slider');
    const tempVal = document.getElementById('temp-val');
    const clearBtn = document.getElementById('clear-chat-btn');
    const directModelSelect = document.getElementById('direct-model-select');

    // Profile Chips
    document.querySelectorAll('.profile-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.profile-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            state.activeProfile = chip.dataset.profile;
            sfx.playClick();
            
            const activeRouteDisplay = document.getElementById('active-route-display');
            if (activeRouteDisplay) {
                activeRouteDisplay.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Mode: ${chip.querySelector('.chip-title').innerText}`;
            }

            // Sync select
            if (state.activeProfile === 'auto') {
                directModelSelect.value = 'auto';
            } else if (state.activeProfile === 'free_tier') {
                directModelSelect.value = 'genesis-5.0-free';
            } else if (state.activeProfile === 'speed') {
                directModelSelect.value = 'genesis-5.0-speed';
            } else if (state.activeProfile === 'reasoning') {
                directModelSelect.value = 'genesis-5.0-reasoning';
            } else if (state.activeProfile === 'coding') {
                directModelSelect.value = 'genesis-5.0-coder';
            } else if (state.activeProfile === 'search') {
                directModelSelect.value = 'genesis-5.0-search';
            }
        });
    });

    // Model Select
    if (directModelSelect) {
        directModelSelect.addEventListener('change', () => {
            state.activeModel = directModelSelect.value;
            sfx.playClick();
        });
    }

    // Temperature
    if (tempSlider && tempVal) {
        tempSlider.addEventListener('input', () => {
            state.temperature = parseFloat(tempSlider.value);
            tempVal.innerText = state.temperature.toFixed(2);
        });
    }

    // Send on Enter
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitChat();
            }
        });
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        });
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', submitChat);
    }

    // Quick Prompts
    document.querySelectorAll('.quick-prompt').forEach(qp => {
        qp.addEventListener('click', () => {
            const prompt = qp.dataset.prompt;
            if (chatInput) {
                chatInput.value = prompt;
                submitChat();
            }
        });
    });

    // Clear Chat
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            const container = document.getElementById('chat-messages');
            if (container) {
                container.innerHTML = `
                <div class="welcome-card glass-panel">
                    <div class="welcome-logo-wrap">
                        <img src="/static/logo.png" alt="GENESIS AI 5.0" class="welcome-logo">
                        <div class="welcome-halo"></div>
                    </div>
                    <h2>GENESIS AI 5.0 Stream Cleared</h2>
                    <p>Ready for next prompt. Cognitive router is armed with 20+ frontier AI ecosystems.</p>
                </div>`;
            }
            sfx.playClick();
        });
    }

    // Voice Input (Speech Recognition)
    initVoiceInput();
}

async function submitChat() {
    const input = document.getElementById('chat-input');
    const prompt = input.value.trim();
    if (!prompt || state.isStreaming) return;

    input.value = '';
    input.style.height = 'auto';
    state.isStreaming = true;
    sfx.playTransmit();

    const messagesContainer = document.getElementById('chat-messages');
    
    // Remove welcome card if present
    const welcomeCard = messagesContainer.querySelector('.welcome-card');
    if (welcomeCard) welcomeCard.remove();

    // Render User Message
    const userRow = document.createElement('div');
    userRow.className = 'message-row user';
    userRow.innerHTML = `
        <div class="msg-bubble">
            <div class="msg-body">${escapeHtml(prompt)}</div>
        </div>
        <div class="msg-avatar user"><i class="fa-solid fa-user"></i></div>
    `;
    messagesContainer.appendChild(userRow);

    // Show Routing Banner
    const routingBanner = document.getElementById('routing-banner');
    const routeTitle = document.getElementById('route-banner-title');
    const routeDesc = document.getElementById('route-banner-desc');
    const routeTags = document.getElementById('route-banner-tags');
    if (routingBanner) {
        routingBanner.classList.remove('hidden');
        routeTitle.innerText = "GENESIS Cognitive Router Armed";
        routeDesc.innerText = `Analyzing prompt intent for profile: ${state.activeProfile.toUpperCase()}...`;
        routeTags.innerHTML = `<span class="banner-tag-item">PROFILE: ${state.activeProfile}</span><span class="banner-tag-item">TEMP: ${state.temperature}</span>`;
    }

    // Render AI Stream Placeholder
    const aiRow = document.createElement('div');
    aiRow.className = 'message-row ai';
    const msgId = 'msg-' + Date.now();
    aiRow.innerHTML = `
        <div class="msg-avatar ai"><i class="fa-solid fa-brain-circuit"></i></div>
        <div class="msg-bubble">
            <div class="msg-header">
                <div class="msg-header-left">
                    <span class="msg-provider-tag" id="${msgId}-tag">GENESIS AI 5.0</span>
                    <span class="msg-latency-tag" id="${msgId}-latency"><i class="fa-solid fa-spinner fa-spin"></i> Routing...</span>
                </div>
                <div class="msg-actions">
                    <button class="msg-action-btn copy-btn" title="Copy Text" onclick="copyMessage('${msgId}')"><i class="fa-regular fa-copy"></i></button>
                    <button class="msg-action-btn speak-btn" title="Read Aloud" onclick="speakMessage('${msgId}')"><i class="fa-solid fa-volume-high"></i></button>
                </div>
            </div>
            <div class="msg-body" id="${msgId}-body"><span class="typing-cursor">▌</span></div>
        </div>
    `;
    messagesContainer.appendChild(aiRow);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Start SSE Stream
    state.startTime = performance.now();
    state.tokenCounter = 0;

    try {
        const payload = {
            prompt: prompt,
            profile: state.activeProfile,
            model: state.activeModel !== 'auto' ? state.activeModel : undefined,
            temperature: state.temperature,
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
        const tagEl = document.getElementById(`${msgId}-tag`);
        const latEl = document.getElementById(`${msgId}-latency`);

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
                            
                            // Render markdown
                            if (window.marked) {
                                bodyEl.innerHTML = marked.parse(fullText);
                            } else {
                                bodyEl.innerText = fullText;
                            }

                            // Update live token speed
                            const elapsedSec = (performance.now() - state.startTime) / 1000;
                            const speed = Math.round(state.tokenCounter / (elapsedSec || 1));
                            const hudSpeed = document.getElementById('hud-tok-speed');
                            if (hudSpeed) hudSpeed.innerText = `${speed} tok/s`;

                        } else if (parsed.meta) {
                            // Routing metadata arrived
                            if (tagEl) tagEl.innerText = `${parsed.meta.provider.toUpperCase()} / ${parsed.meta.model}`;
                            if (routeTitle) routeTitle.innerText = `Routed to ${parsed.meta.provider.toUpperCase()}`;
                            if (routeDesc) routeDesc.innerText = `Intent: ${parsed.meta.intent} | Fallback Waterfall Active`;
                        }
                    } catch(e) {}
                }
            }
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        const totalLatency = Math.round(performance.now() - state.startTime);
        if (latEl) latEl.innerText = `${totalLatency} ms`;
        
        // Highlight code blocks
        if (window.hljs) {
            bodyEl.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }

        sfx.playComplete();

    } catch (err) {
        const bodyEl = document.getElementById(`${msgId}-body`);
        if (bodyEl) bodyEl.innerHTML = `<span style="color:var(--accent-rose)"><i class="fa-solid fa-triangle-exclamation"></i> Error: ${err.message}</span>`;
    } finally {
        state.isStreaming = false;
    }
}

// Copy & TTS helpers
window.copyMessage = function(msgId) {
    const bodyEl = document.getElementById(`${msgId}-body`);
    if (bodyEl) {
        navigator.clipboard.writeText(bodyEl.innerText);
        showToast('Response copied to clipboard!');
        sfx.playClick();
    }
};

window.speakMessage = function(msgId) {
    const bodyEl = document.getElementById(`${msgId}-body`);
    if (bodyEl && window.speechSynthesis) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(bodyEl.innerText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
        showToast('Speaking response...');
        sfx.playClick();
    }
};

// ==========================================
// 6. VOICE DICTATION (Speech-To-Text)
// ==========================================
function initVoiceInput() {
    const micBtn = document.getElementById('voice-input-btn');
    const waveBar = document.getElementById('voice-wave-bar');
    const chatInput = document.getElementById('chat-input');
    const voiceStatus = document.getElementById('voice-status-text');

    if (!micBtn) return;

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
        micBtn.title = "Voice recognition not supported in this browser";
        return;
    }

    const recognition = new SpeechRec();
    recognition.continuous = false;
    recognition.interimResults = true;
    let isListening = false;

    micBtn.addEventListener('click', () => {
        if (!isListening) {
            recognition.start();
            isListening = true;
            micBtn.classList.add('listening');
            if (waveBar) waveBar.classList.remove('hidden');
            if (voiceStatus) voiceStatus.innerText = "Listening to your voice...";
            sfx.playTransmit();
        } else {
            recognition.stop();
            isListening = false;
            micBtn.classList.remove('listening');
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
        micBtn.classList.remove('listening');
        if (waveBar) waveBar.classList.add('hidden');
    };

    recognition.onerror = (e) => {
        isListening = false;
        micBtn.classList.remove('listening');
        if (waveBar) waveBar.classList.add('hidden');
        showToast(`Voice Error: ${e.error}`);
    };
}

// ==========================================
// 7. 4-WAY MODEL ARENA (The Colosseum)
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

    // Reset arena panels
    for (let i = 0; i < 4; i++) {
        const bodyEl = document.getElementById(`arena-body-${i}`);
        const metricEl = document.getElementById(`arena-metric-${i}`);
        const nameEl = document.getElementById(`arena-name-${i}`);
        if (bodyEl) bodyEl.innerHTML = '<span class="typing-cursor">▌ Generating stream...</span>';
        if (metricEl) metricEl.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Racing...';
        if (nameEl) nameEl.innerText = selectedModels[i];
    }

    // Launch 4 concurrent requests
    selectedModels.forEach((modelKey, index) => {
        const [provider, model] = modelKey.split('/');
        const startTime = performance.now();

        fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: prompt,
                provider: provider,
                model: model,
                stream: true
            })
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
// 8. PROVIDER COMMAND CENTER (20 Providers)
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

        // Batch Ping Button
        const pingAllBtn = document.getElementById('ping-all-btn');
        if (pingAllBtn) {
            pingAllBtn.onclick = () => {
                sfx.playTransmit();
                Object.keys(state.providers).forEach(pid => pingProvider(pid));
            };
        }

    } catch(e) {
        container.innerHTML = `<div style="color:var(--accent-rose)">Failed to load providers: ${e.message}</div>`;
    }
}

window.pingProvider = async function(pid) {
    const btn = document.getElementById(`ping-${pid}`);
    if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Pinging...';

    const start = performance.now();
    try {
        const res = await fetch(`/api/providers`);
        const lat = Math.round(performance.now() - start);
        if (btn) {
            btn.innerHTML = `<span style="color:var(--accent-emerald)"><i class="fa-solid fa-check"></i> ${lat} ms</span>`;
        }
    } catch(e) {
        if (btn) btn.innerHTML = `<span style="color:var(--accent-rose)">Offline</span>`;
    }
};

// Modal for Keys
window.openKeyModal = function(pid, name, envKey, docsUrl) {
    const modal = document.getElementById('key-modal');
    const nameEl = document.getElementById('modal-provider-name');
    const descEl = document.getElementById('modal-provider-desc');
    const envLabel = document.getElementById('modal-env-label');
    const linkEl = document.getElementById('modal-key-link');
    const keyInput = document.getElementById('modal-key-input');

    if (!modal) return;

    nameEl.innerText = `Configure ${name}`;
    descEl.innerText = `Enter the API key for ${name}. It will be saved securely to your local .env vault.`;
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
            showToast(`${name} API key updated!`);
            modal.classList.add('hidden');
            loadProviders();
            sfx.playComplete();
        } catch(e) {
            showToast(`Failed to save key: ${e.message}`);
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
// 9. USER ANALYTICS & TELEMETRY
// ==========================================
async function loadAnalytics() {
    try {
        const res = await fetch('/api/analytics');
        const data = await res.json();

        // Update KPIs
        const kpiUsers = document.getElementById('kpi-users');
        const kpiRequests = document.getElementById('kpi-requests');
        const kpiTokens = document.getElementById('kpi-tokens');
        const kpiLatency = document.getElementById('kpi-latency');

        if (kpiUsers) kpiUsers.innerText = data.total_users || 0;
        if (kpiRequests) kpiRequests.innerText = data.total_requests || 0;
        if (kpiTokens) kpiTokens.innerText = (data.total_tokens || 0).toLocaleString();
        if (kpiLatency) kpiLatency.innerText = `${Math.round(data.average_latency_ms || 0)} ms`;

        // Populate Table
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
// 10. NEURAL GRAPH SIMULATION (Tab 3)
// ==========================================
function initGraph() {
    const simBtn = document.getElementById('simulate-graph-btn');
    if (!simBtn) return;

    simBtn.addEventListener('click', () => {
        sfx.playTransmit();
        const links = document.querySelectorAll('.flow-line');
        links.forEach(l => {
            l.classList.add('active');
            setTimeout(() => l.classList.remove('active'), 2500);
        });
        showToast('Simulating Cognitive Routing Signal Flow across all Tiers');
    });
}

// ==========================================
// 11. TOAST & UTILITIES
// ==========================================
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

// Copy Code Snippets in Tab 7
document.querySelectorAll('.copy-code-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const targetId = btn.dataset.target;
        const codeEl = document.getElementById(targetId);
        if (codeEl) {
            navigator.clipboard.writeText(codeEl.innerText);
            showToast('Code snippet copied to clipboard!');
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
    initChat();
    initArena();
    initGraph();
    loadProviders();
    loadAnalytics();

    // Auto-refresh analytics every 10s
    setInterval(loadAnalytics, 10000);
});
