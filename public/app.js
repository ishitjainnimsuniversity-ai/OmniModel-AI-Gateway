/**
 * OmniModel AI Gateway - Frontend Controller & Real-Time SSE Stream Manager
 */

document.addEventListener("DOMContentLoaded", () => {
    // App State
    const state = {
        activeTab: "chat",
        selectedProfile: "auto",
        selectedModel: "auto",
        temperature: 0.7,
        providers: {},
        messages: [],
        isStreaming: false
    };

    // DOM Elements
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const activeProvidersCountEl = document.getElementById("active-providers-count");
    
    // Chat Elements
    const chatMessagesEl = document.getElementById("chat-messages");
    const chatInputEl = document.getElementById("chat-input");
    const sendBtnEl = document.getElementById("send-btn");
    const profileSelector = document.getElementById("profile-selector");
    const directModelSelect = document.getElementById("direct-model-select");
    const tempSlider = document.getElementById("temp-slider");
    const tempValEl = document.getElementById("temp-val");
    const routingBanner = document.getElementById("routing-banner");
    const routeBannerTitle = document.getElementById("route-banner-title");
    const routeBannerDesc = document.getElementById("route-banner-desc");
    const routeBannerTags = document.getElementById("route-banner-tags");
    const activeRouteDisplay = document.getElementById("active-route-display");
    const clearChatBtn = document.getElementById("clear-chat-btn");

    // Arena Elements
    const arenaPromptInput = document.getElementById("arena-prompt-input");
    const arenaBroadcastBtn = document.getElementById("arena-broadcast-btn");

    // Modal Elements
    const keyModal = document.getElementById("key-modal");
    const modalCloseBtn = document.getElementById("modal-close-btn");
    const modalCancelBtn = document.getElementById("modal-cancel-btn");
    const modalSaveBtn = document.getElementById("modal-save-btn");
    const modalProviderName = document.getElementById("modal-provider-name");
    const modalProviderDesc = document.getElementById("modal-provider-desc");
    const modalEnvLabel = document.getElementById("modal-env-label");
    const modalKeyInput = document.getElementById("modal-key-input");
    const modalKeyLink = document.getElementById("modal-key-link");

    // Toast Element
    const toastEl = document.getElementById("toast");

    let currentEditingEnvVar = null;

    // ------------------------------------------------------------------------
    // 1. Toast Notification Utility
    // ------------------------------------------------------------------------
    function showToast(message, duration = 3000) {
        toastEl.textContent = message;
        toastEl.classList.remove("hidden");
        setTimeout(() => {
            toastEl.classList.add("hidden");
        }, duration);
    }

    // ------------------------------------------------------------------------
    // 2. Tab Navigation
    // ------------------------------------------------------------------------
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.dataset.tab;
            tabButtons.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");
            state.activeTab = targetTab;
        });
    });

    // ------------------------------------------------------------------------
    // 3. Provider Data & Model Loading
    // ------------------------------------------------------------------------
    async function loadProviders() {
        try {
            const res = await fetch("/api/providers");
            const data = await res.json();
            if (data.success) {
                state.providers = data.providers;
                renderProvidersGrid();
                populateModelDropdowns();
                updateActiveProvidersCount();
            }
        } catch (err) {
            console.error("Failed to load providers:", err);
            activeProvidersCountEl.textContent = "Gateway Offline";
        }
    }

    function updateActiveProvidersCount() {
        const total = Object.keys(state.providers).length;
        const active = Object.values(state.providers).filter(p => p.has_key).length;
        activeProvidersCountEl.textContent = `${active}/${total} Providers Ready`;
    }

    function renderProvidersGrid() {
        const container = document.getElementById("providers-grid-container");
        if (!container) return;
        container.innerHTML = "";

        Object.values(state.providers).forEach(p => {
            const card = document.createElement("div");
            card.className = "provider-card glass-panel";
            
            const isLocal = p.id === "ollama";
            const badgeClass = p.has_key ? "status-active" : "status-missing";
            const badgeText = isLocal ? "Local Offline" : (p.has_key ? "Configured" : "Key Needed");
            const icon = p.has_key ? "fa-circle-check" : "fa-key";

            card.innerHTML = `
                <div class="provider-card-header">
                    <div class="provider-info">
                        <h4>${p.name}</h4>
                        <span class="provider-cat">${p.category}</span>
                    </div>
                    <span class="provider-status-badge ${badgeClass}">
                        <i class="fa-solid ${icon}"></i> ${badgeText}
                    </span>
                </div>
                <div class="provider-meta-notes">
                    <strong>${p.free_tier ? "🆓 Free Tier:" : "💳 Tier:"}</strong> ${p.free_note || "Standard API Access"}
                </div>
                <div class="provider-actions">
                    <button class="ping-btn" data-pid="${p.id}">
                        <i class="fa-solid fa-satellite-dish"></i> Test Ping
                    </button>
                    ${!isLocal ? `
                    <button class="config-btn" data-pid="${p.id}">
                        <i class="fa-solid fa-gear"></i> ${p.has_key ? "Update Key" : "Set API Key"}
                    </button>
                    ` : `
                    <span style="font-size:0.75rem; color:var(--text-muted);">http://localhost:11434</span>
                    `}
                </div>
            `;
            container.appendChild(card);
        });

        // Attach event handlers
        container.querySelectorAll(".ping-btn").forEach(btn => {
            btn.addEventListener("click", () => pingProvider(btn.dataset.pid, btn));
        });

        container.querySelectorAll(".config-btn").forEach(btn => {
            btn.addEventListener("click", () => openKeyModal(btn.dataset.pid));
        });
    }

    function populateModelDropdowns() {
        // Chat dropdown
        const freeGroup = document.getElementById("optgroup-free");
        const frontierGroup = document.getElementById("optgroup-frontier");
        const fastGroup = document.getElementById("optgroup-fast");
        const codeGroup = document.getElementById("optgroup-code");
        const searchGroup = document.getElementById("optgroup-search");
        const localGroup = document.getElementById("optgroup-local");

        if (freeGroup) freeGroup.innerHTML = "";
        if (frontierGroup) frontierGroup.innerHTML = "";
        if (fastGroup) fastGroup.innerHTML = "";
        if (codeGroup) codeGroup.innerHTML = "";
        if (searchGroup) searchGroup.innerHTML = "";
        if (localGroup) localGroup.innerHTML = "";

        Object.values(state.providers).forEach(p => {
            p.models.forEach(m => {
                const opt = document.createElement("option");
                opt.value = `${p.id}/${m.id}`;
                opt.textContent = `${p.name} - ${m.name} (${m.context})`;

                if (p.id === "ollama" && localGroup) {
                    localGroup.appendChild(opt);
                } else if (m.free && freeGroup) {
                    freeGroup.appendChild(opt);
                } else if (m.tags.includes("coding") && codeGroup) {
                    codeGroup.appendChild(opt);
                } else if (m.tags.includes("speed") && fastGroup) {
                    fastGroup.appendChild(opt);
                } else if (m.tags.includes("search") && searchGroup) {
                    searchGroup.appendChild(opt);
                } else if (frontierGroup) {
                    frontierGroup.appendChild(opt);
                }
            });
        });
    }

    // ------------------------------------------------------------------------
    // 4. Provider Ping & Testing
    // ------------------------------------------------------------------------
    async function pingProvider(pid, btnEl) {
        const origText = btnEl.innerHTML;
        btnEl.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Pinging...`;
        try {
            const res = await fetch(`/api/ping/${pid}`, { method: "POST" });
            const data = await res.json();
            if (data.status === "active") {
                btnEl.innerHTML = `<i class="fa-solid fa-check" style="color:var(--accent-emerald);"></i> ${data.latency_ms}ms`;
                showToast(`✓ ${pid.toUpperCase()} connected successfully (${data.latency_ms}ms)`);
            } else if (data.status === "missing_key") {
                btnEl.innerHTML = `<i class="fa-solid fa-key" style="color:var(--accent-amber);"></i> Key Missing`;
                showToast(`⚠ ${pid.toUpperCase()}: API key not configured in .env`);
            } else {
                btnEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="color:var(--accent-rose);"></i> Error`;
                showToast(`❌ ${pid.toUpperCase()}: ${data.message || 'Error'}`);
            }
        } catch (err) {
            btnEl.innerHTML = `<i class="fa-solid fa-xmark"></i> Failed`;
            showToast(`Ping failed: ${err.message}`);
        }
        setTimeout(() => { btnEl.innerHTML = origText; }, 4000);
    }

    document.getElementById("ping-all-btn")?.addEventListener("click", () => {
        showToast("Pinging all 20 AI providers in parallel...");
        document.querySelectorAll(".ping-btn").forEach(btn => btn.click());
    });

    // ------------------------------------------------------------------------
    // 5. Key Configuration Modal
    // ------------------------------------------------------------------------
    function openKeyModal(pid) {
        const p = state.providers[pid];
        if (!p) return;
        currentEditingEnvVar = p.env_var;
        modalProviderName.textContent = `Configure ${p.name}`;
        modalProviderDesc.textContent = `${p.category}. ${p.free_note || ''}`;
        modalEnvLabel.textContent = `Environment Variable: ${p.env_var}`;
        modalKeyInput.value = "";
        modalKeyLink.href = p.free_key_url || "https://ai.google.dev/";
        modalKeyLink.textContent = p.free_tier ? "Get Free API Key" : "Open Provider API Console";
        keyModal.classList.remove("hidden");
        modalKeyInput.focus();
    }

    modalCloseBtn?.addEventListener("click", () => keyModal.classList.add("hidden"));
    modalCancelBtn?.addEventListener("click", () => keyModal.classList.add("hidden"));

    modalSaveBtn?.addEventListener("click", async () => {
        const val = modalKeyInput.value.trim();
        if (!val || !currentEditingEnvVar) {
            showToast("Please enter a valid API key.");
            return;
        }

        try {
            const res = await fetch("/api/keys", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ env_var: currentEditingEnvVar, value: val })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`✓ Saved ${currentEditingEnvVar} to .env!`);
                keyModal.classList.add("hidden");
                loadProviders();
            } else {
                showToast(`Failed: ${data.detail || 'Error'}`);
            }
        } catch (err) {
            showToast(`Error saving key: ${err.message}`);
        }
    });

    // ------------------------------------------------------------------------
    // 6. Profile & Model Controls
    // ------------------------------------------------------------------------
    profileSelector?.querySelectorAll(".profile-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            profileSelector.querySelectorAll(".profile-chip").forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            state.selectedProfile = chip.dataset.profile;
            directModelSelect.value = "auto";
            state.selectedModel = "auto";
            activeRouteDisplay.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Mode: ${chip.querySelector(".chip-title").textContent}`;
        });
    });

    directModelSelect?.addEventListener("change", (e) => {
        state.selectedModel = e.target.value;
        if (state.selectedModel !== "auto") {
            profileSelector.querySelectorAll(".profile-chip").forEach(c => c.classList.remove("active"));
            activeRouteDisplay.innerHTML = `<i class="fa-solid fa-microchip"></i> Override: ${state.selectedModel}`;
        } else {
            const autoChip = profileSelector.querySelector('[data-profile="auto"]');
            autoChip?.classList.add("active");
            state.selectedProfile = "auto";
            activeRouteDisplay.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Mode: Auto Intent`;
        }
    });

    tempSlider?.addEventListener("input", (e) => {
        state.temperature = parseFloat(e.target.value);
        tempValEl.textContent = state.temperature.toFixed(2);
    });

    clearChatBtn?.addEventListener("click", () => {
        state.messages = [];
        chatMessagesEl.innerHTML = `
            <div class="welcome-card">
                <div class="welcome-icon"><i class="fa-solid fa-atom"></i></div>
                <h2>OmniModel Gateway Online</h2>
                <p>History cleared. Ready for your next multi-model query or code prompt.</p>
            </div>
        `;
        routingBanner.classList.add("hidden");
    });

    // Quick Prompts
    document.addEventListener("click", (e) => {
        const qp = e.target.closest(".quick-prompt");
        if (qp) {
            chatInputEl.value = qp.dataset.prompt;
            handleSendMessage();
        }
    });

    // ------------------------------------------------------------------------
    // 7. Interactive Streaming Chat Manager
    // ------------------------------------------------------------------------
    chatInputEl?.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    sendBtnEl?.addEventListener("click", handleSendMessage);

    async function handleSendMessage() {
        const text = chatInputEl.value.trim();
        if (!text || state.isStreaming) return;

        // Remove welcome card if present
        const welcomeCard = chatMessagesEl.querySelector(".welcome-card");
        if (welcomeCard) welcomeCard.remove();

        // Add user message
        state.messages.push({ role: "user", content: text });
        appendMessageBubble("user", text);
        chatInputEl.value = "";
        state.isStreaming = true;
        sendBtnEl.disabled = true;

        // Prepare AI streaming bubble
        const aiBubbleEl = appendMessageBubble("ai", "", "OmniModel Router", "Connecting...");
        const contentEl = aiBubbleEl.querySelector(".msg-body");
        const headerTagEl = aiBubbleEl.querySelector(".msg-provider-tag");
        const latencyTagEl = aiBubbleEl.querySelector(".msg-latency-tag");

        let fullAiText = "";
        const startTime = performance.now();

        try {
            const payload = {
                messages: state.messages,
                provider: state.selectedModel !== "auto" ? state.selectedModel.split("/")[0] : null,
                model: state.selectedModel !== "auto" ? state.selectedModel.split("/")[1] : null,
                profile: state.selectedModel === "auto" ? (state.selectedProfile === "auto" ? null : state.selectedProfile) : null,
                temperature: state.temperature
            };

            const response = await fetch("/api/chat/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop(); // Keep partial line in buffer

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed || !trimmed.startsWith("data: ")) continue;
                    const jsonStr = trimmed.slice(6);
                    if (jsonStr === "[DONE]") break;

                    try {
                        const data = JSON.parse(jsonStr);
                        
                        // Handle routing decision metadata event
                        if (data.meta_event === "routing_decision") {
                            routingBanner.classList.remove("hidden");
                            routeBannerTitle.textContent = `Auto-Routed to: ${data.profile_name}`;
                            routeBannerDesc.textContent = data.rationale;
                            routeBannerTags.innerHTML = data.chain.map(c => `<span class="banner-tag-item">${c.provider_name}</span>`).join(" ");
                        }

                        // Handle provider fallback alert
                        if (data.meta_event === "provider_fallback") {
                            showToast(`⚠ Fallback: ${data.failed_provider} unavailable. Switching to next provider...`);
                        }

                        // Handle delta chunk
                        if (data.delta) {
                            fullAiText += data.delta;
                            contentEl.innerHTML = marked.parse(fullAiText);
                            contentEl.querySelectorAll("pre code").forEach(el => hljs.highlightElement(el));
                            chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
                        }

                        if (data.provider) {
                            headerTagEl.textContent = `${data.provider.toUpperCase()} / ${data.model || ''}`;
                        }

                        if (data.latency_ms) {
                            latencyTagEl.textContent = `Latency: ${data.latency_ms}ms`;
                        }

                    } catch (parseErr) {
                        console.warn("SSE Parse Warning:", parseErr);
                    }
                }
            }

            // Save completed assistant message to history
            state.messages.push({ role: "assistant", content: fullAiText });
            const totalTime = Math.round(performance.now() - startTime);
            latencyTagEl.textContent = `Completed in ${totalTime}ms`;

        } catch (err) {
            contentEl.innerHTML = `<span style="color:var(--accent-rose)">Error connecting to OmniModel Gateway: ${err.message}</span>`;
        } finally {
            state.isStreaming = false;
            sendBtnEl.disabled = false;
        }
    }

    function appendMessageBubble(role, text, providerTag = "You", latencyTag = "") {
        const row = document.createElement("div");
        row.className = `message-row ${role}`;
        
        const avatarIcon = role === "user" ? "fa-user" : "fa-brain";
        row.innerHTML = `
            <div class="msg-avatar ${role}">
                <i class="fa-solid ${avatarIcon}"></i>
            </div>
            <div class="msg-bubble">
                <div class="msg-header">
                    <span class="msg-provider-tag">${providerTag}</span>
                    <span class="msg-latency-tag">${latencyTag}</span>
                </div>
                <div class="msg-body">${role === "user" ? text : '<span class="pulsing-text">Thinking...</span>'}</div>
            </div>
        `;

        chatMessagesEl.appendChild(row);
        chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
        return row;
    }

    // ------------------------------------------------------------------------
    // 8. Model Arena (Multi-Duel Parallel Broadcast)
    // ------------------------------------------------------------------------
    arenaBroadcastBtn?.addEventListener("click", handleArenaBroadcast);
    arenaPromptInput?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") handleArenaBroadcast();
    });

    async function handleArenaBroadcast() {
        const prompt = arenaPromptInput.value.trim();
        if (!prompt) return;

        const selectedModels = [
            document.getElementById("arena-model-0").value,
            document.getElementById("arena-model-1").value,
            document.getElementById("arena-model-2").value,
            document.getElementById("arena-model-3").value
        ];

        // Reset cards
        for (let i = 0; i < 4; i++) {
            const [prov, mod] = selectedModels[i].split("/");
            document.getElementById(`arena-name-${i}`).textContent = `${prov.toUpperCase()} (${mod})`;
            document.getElementById(`arena-metric-${i}`).textContent = "Streaming...";
            document.getElementById(`arena-body-${i}`).innerHTML = `<span style="color:var(--accent-cyan);"><i class="fa-solid fa-spinner fa-spin"></i> Generating...</span>`;
        }

        const modelPayloads = selectedModels.map(sm => {
            const [prov, mod] = sm.split("/");
            return { provider: prov, model: mod };
        });

        const responsesText = ["", "", "", ""];
        const startTimes = [performance.now(), performance.now(), performance.now(), performance.now()];

        try {
            const res = await fetch("/api/arena/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    models: modelPayloads,
                    messages: [{ role: "user", content: prompt }]
                })
            });

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop();

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed || !trimmed.startsWith("data: ")) continue;
                    const jsonStr = trimmed.slice(6);
                    if (jsonStr === "[DONE]") break;

                    try {
                        const item = JSON.parse(jsonStr);
                        const wid = item.arena_worker_id;
                        if (wid !== undefined && wid >= 0 && wid < 4) {
                            if (item.delta) {
                                responsesText[wid] += item.delta;
                                const bodyEl = document.getElementById(`arena-body-${wid}`);
                                bodyEl.innerHTML = marked.parse(responsesText[wid]);
                                bodyEl.querySelectorAll("pre code").forEach(el => hljs.highlightElement(el));
                            }
                            if (item.done) {
                                const totalMs = Math.round(performance.now() - startTimes[wid]);
                                const wordCount = responsesText[wid].split(/\s+/).length;
                                const speed = Math.round((wordCount / (totalMs / 1000)) * 1.3);
                                document.getElementById(`arena-metric-${wid}`).textContent = `${totalMs}ms (~${speed} tok/s)`;
                            }
                        }
                    } catch (e) {}
                }
            }
        } catch (err) {
            showToast(`Arena error: ${err.message}`);
        }
    }

    // ------------------------------------------------------------------------
    // 9. Copy Code Snippets
    // ------------------------------------------------------------------------
    document.querySelectorAll(".copy-code-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.dataset.target;
            const codeEl = document.getElementById(targetId);
            if (codeEl) {
                navigator.clipboard.writeText(codeEl.innerText);
                btn.innerHTML = `<i class="fa-solid fa-check"></i> Copied!`;
                setTimeout(() => {
                    btn.innerHTML = `<i class="fa-regular fa-copy"></i> Copy`;
                }, 2000);
            }
        });
    });

    // ------------------------------------------------------------------------
    // 10. User Analytics & Telemetry Loader
    // ------------------------------------------------------------------------
    async function loadAnalytics() {
        try {
            const res = await fetch("/api/analytics");
            const data = await res.json();
            if (data.success && data.analytics) {
                const a = data.analytics;
                document.getElementById("kpi-users").textContent = a.unique_users || 0;
                document.getElementById("kpi-requests").textContent = a.total_requests || 0;
                document.getElementById("kpi-tokens").textContent = a.total_tokens ? a.total_tokens.toLocaleString() : 0;
                document.getElementById("kpi-latency").textContent = `${a.avg_latency_ms || 0} ms`;

                const tbody = document.getElementById("analytics-tbody");
                if (a.recent_activity && a.recent_activity.length > 0) {
                    tbody.innerHTML = a.recent_activity.map(r => `
                        <tr>
                            <td><span style="font-family:var(--font-mono); font-size:0.75rem;">${r.timestamp}</span></td>
                            <td><span style="font-family:var(--font-mono); color:var(--accent-cyan);">${r.client_ip}</span></td>
                            <td><span style="font-size:0.75rem;">${r.platform}</span></td>
                            <td><strong>${r.provider.toUpperCase()}</strong> / ${r.model}</td>
                            <td><span style="font-family:var(--font-mono);">${r.latency_ms}ms</span></td>
                            <td><span class="badge ${r.status === 'success' ? 'badge-c' : 'badge-d'}">${r.status}</span></td>
                        </tr>
                    `).join("");
                } else {
                    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:20px;">No requests recorded yet. Make a query to see live telemetry!</td></tr>`;
                }
            }
        } catch (err) {
            console.error("Failed to load analytics:", err);
        }
    }

    document.getElementById("refresh-analytics-btn")?.addEventListener("click", () => {
        showToast("Refreshing user activity logs...");
        loadAnalytics();
    });

    document.getElementById("clear-analytics-btn")?.addEventListener("click", async () => {
        await fetch("/api/analytics/clear", { method: "POST" });
        showToast("Analytics history cleared.");
        loadAnalytics();
    });

    // Load analytics when switching to analytics tab
    document.querySelector('[data-tab="analytics"]')?.addEventListener("click", loadAnalytics);

    // Initial load
    loadProviders();
    loadAnalytics();
});
