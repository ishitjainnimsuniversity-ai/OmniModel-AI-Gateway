// GENESIS AI Mobile & Desktop Dashboard — Embedded in ESP32-C5 Flash (PROGMEM).
// Completely self-contained: zero external dependencies, no CDN links, works 100% offline.
// Supports: Direct Google Gemini AI (no dead relay URL), Multi-Modal Image Studio, and TFT streaming.
#pragma once
#include <Arduino.h>

const char DASHBOARD_HTML[] PROGMEM = R"rawliteral(<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#050b18">
<title>GENESIS AI — Universal Portable Device</title>
<style>
:root{--bg:#050b18;--panel:#0b1426;--card:#101e38;--card-hi:#16274a;--line:#1c3558;--cyan:#22d3ee;--blue:#3b82f6;--purple:#a855f7;--text:#e6f1ff;--dim:#7d93b2;--ok:#34d399;--warn:#fbbf24;--bad:#f87171}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
html,body{height:100%}
body{background:radial-gradient(1200px 600px at 50% -10%,#0c2347 0%,var(--bg) 65%);color:var(--text);font:14px/1.5 system-ui,-apple-system,sans-serif;display:flex;flex-direction:column}
header{display:flex;align-items:center;gap:10px;padding:calc(10px + env(safe-area-inset-top)) 14px 10px;border-bottom:1px solid var(--line);background:rgba(5,11,24,.92);backdrop-filter:blur(8px);flex:none}
header svg{width:28px;height:28px;flex:none}
.brand{font-weight:900;letter-spacing:.12em;font-size:14px;color:var(--cyan)}
.sub{font-size:11px;color:var(--dim)}
.grow{flex:1;min-width:0}
.tabs{display:flex;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:2px;gap:2px}
.tab{background:none;border:none;color:var(--dim);font-weight:700;font-size:12px;padding:5px 12px;border-radius:8px;cursor:pointer;display:inline-flex;align-items:center;gap:5px;transition:all .15s}
.tab.active{background:linear-gradient(135deg,var(--card),var(--card-hi));color:var(--cyan);box-shadow:0 1px 3px rgba(0,0,0,.3)}
.chip{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;color:var(--text);border:1px solid var(--line);border-radius:99px;padding:3px 8px;background:var(--panel)}
.dot{width:7px;height:7px;border-radius:50%;background:var(--bad)}
.dot.on{background:var(--ok);box-shadow:0 0 8px var(--ok)}
.dot.busy{background:var(--warn);animation:pulse 1s infinite}
@keyframes pulse{50%{opacity:.35}}
.tbar{display:flex;gap:8px;padding:6px 14px;background:var(--panel);border-bottom:1px solid var(--line);font-size:11px;color:var(--dim);align-items:center;overflow-x:auto;flex:none}
.tbar span{display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
.tbar b{color:var(--text)}
.view{flex:1;overflow-y:auto;display:none;flex-direction:column}
.view.active{display:flex}
/* CHAT VIEW */
#chatView{padding:12px;display:none;flex-direction:column;gap:10px;scroll-behavior:smooth}
#chatView.active{display:flex}
.empty{margin:auto;text-align:center;color:var(--dim);max-width:400px;padding:16px}
.empty svg{width:64px;height:64px;margin-bottom:8px}
.empty h2{color:var(--text);font-size:17px;margin-bottom:4px}
.banner{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px;font-size:12px;margin:8px 0;line-height:1.4}
.banner b{color:var(--cyan)}
.sugg{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-top:10px}
.sugg button{font-size:12px;border-radius:99px;color:var(--cyan);background:var(--panel);border:1px solid var(--line);padding:4px 10px;cursor:pointer}
.msg{max-width:92%;padding:10px 13px;border-radius:14px;overflow-wrap:anywhere;white-space:pre-wrap}
.me{align-self:flex-end;background:linear-gradient(135deg,#0e4a6b,#12306b);border:1px solid #1d5a85;border-bottom-right-radius:4px}
.ai{align-self:flex-start;background:var(--panel);border:1px solid var(--line);border-bottom-left-radius:4px}
.ai.err{border-color:#7f1d1d;background:#220d12;color:#fecaca}
.meta{font-size:10px;font-weight:700;color:var(--dim);margin-top:6px;display:flex;align-items:center;gap:6px}
.meta span{padding:1px 5px;border-radius:4px;border:1px solid var(--line)}
.meta .tag-relay{border-color:var(--cyan);color:var(--cyan)}
.meta .tag-tft{border-color:var(--ok);color:var(--ok)}
.ai pre{background:#030712;border:1px solid var(--line);border-radius:8px;padding:9px;margin:8px 0;overflow-x:auto;font:13px/1.45 monospace}
.ai code{font:13px monospace;background:#030712;padding:1px 4px;border-radius:4px}
.ai pre code{background:none;padding:0}
.think{display:inline-flex;gap:5px;padding:4px 0}
.think i{width:8px;height:8px;border-radius:50%;background:var(--cyan);animation:bounce 1.2s infinite}
.think i:nth-child(2){animation-delay:.15s}.think i:nth-child(3){animation-delay:.3s}
@keyframes bounce{0%,80%,100%{transform:translateY(0);opacity:.35}40%{transform:translateY(-6px);opacity:1}}
#chatForm{display:flex;gap:8px;padding:8px 12px calc(8px + env(safe-area-inset-bottom));border-top:1px solid var(--line);background:rgba(5,11,24,.94);flex:none}
textarea{flex:1;resize:none;max-height:120px;background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:12px;padding:9px 12px;font:inherit;outline:none}
textarea:focus{border-color:var(--cyan)}
button{font:inherit;cursor:pointer}
.btn-send{background:linear-gradient(135deg,var(--cyan),var(--blue));color:#02131f;font-weight:800;border:0;border-radius:12px;padding:0 16px}
.btn-send:disabled{opacity:.45}

/* IMAGE STUDIO VIEW */
#studioView{padding:14px;gap:14px;max-width:1200px;margin:0 auto;width:100%}
.studio-grid{display:grid;grid-template-columns:1fr;gap:14px;width:100%}
@media (min-width:768px){.studio-grid{grid-template-columns:380px 1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:12px}
.card-title{font-size:13px;font-weight:800;letter-spacing:.05em;color:var(--cyan);text-transform:uppercase;display:flex;align-items:center;justify-content:space-between}
.p-label{font-size:11px;font-weight:700;color:var(--dim);margin-bottom:4px}
.chip-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(84px,1fr));gap:6px}
.c-btn{padding:6px 8px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text);font-size:11px;font-weight:600;text-align:center;cursor:pointer;transition:all .15s}
.c-btn.sel{border-color:var(--cyan);background:rgba(34,211,238,.12);color:var(--cyan);box-shadow:0 0 8px rgba(34,211,238,.2)}
.aspect-row{display:flex;gap:6px}
.a-btn{flex:1;padding:6px 0;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text);font-size:11px;font-weight:700;text-align:center;cursor:pointer}
.a-btn.sel{border-color:var(--blue);background:rgba(59,130,246,.15);color:var(--cyan)}
.drop-zone{border:1px dashed var(--line);border-radius:10px;padding:10px;text-align:center;color:var(--dim);font-size:11px;cursor:pointer;position:relative}
.drop-zone:hover{border-color:var(--cyan)}
.drop-zone img{max-height:80px;border-radius:6px;display:none;margin:4px auto}
.btn-gen{background:linear-gradient(135deg,var(--cyan),var(--purple));color:#02131f;font-weight:800;border:0;border-radius:10px;padding:10px;font-size:13px;display:flex;align-items:center;justify-content:center;gap:6px;box-shadow:0 2px 10px rgba(34,211,238,.25)}
.btn-gen:disabled{opacity:.45}
.progress-bar{height:4px;border-radius:2px;background:var(--line);overflow:hidden;display:none}
.progress-fill{height:100%;width:0%;background:linear-gradient(90deg,var(--cyan),var(--purple));transition:width .3s}
.canvas-card{align-items:center;justify-content:center;min-height:300px;position:relative;background:#030712;border:1px solid var(--line);border-radius:14px;overflow:hidden}
.canvas-card img{max-width:100%;max-height:480px;object-fit:contain;border-radius:8px;display:none}
.canvas-empty{display:flex;flex-direction:column;align-items:center;gap:8px;color:var(--dim);padding:30px 16px;text-align:center}
.canvas-empty svg{width:54px;height:54px;stroke:var(--line)}
.canvas-bar{display:flex;gap:8px;width:100%;padding:10px;background:var(--panel);border-top:1px solid var(--line);border-radius:0 0 14px 14px}
.btn-sub{flex:1;padding:8px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text);font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;gap:5px;cursor:pointer}
.btn-sub:hover{border-color:var(--cyan)}
.history-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(72px,1fr));gap:6px;margin-top:6px}
.history-item{aspect-ratio:1/1;border-radius:6px;overflow:hidden;border:1px solid var(--line);cursor:pointer;position:relative}
.history-item img{width:100%;height:100%;object-fit:cover}

/* DRAWER */
.drawer{position:fixed;inset:0;background:rgba(2,6,15,.9);display:none;align-items:flex-end;z-index:9}
.drawer.show{display:flex}
.dcard{background:var(--panel);border-top:1px solid var(--line);border-radius:16px 16px 0 0;padding:16px;width:100%;max-height:88vh;overflow-y:auto}
.dcard h3{margin-bottom:8px;font-size:16px}
.dcard label{display:block;font-size:11px;color:var(--dim);margin:10px 0 4px}
.dcard input,.dcard select{width:100%;padding:8px;border-radius:8px;border:1px solid var(--line);background:#030712;color:var(--text);font:inherit}
.row-btn{display:flex;gap:8px;margin-top:14px}
.row-btn button{flex:1;padding:9px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)}
.btn-pri{background:linear-gradient(135deg,var(--cyan),var(--blue)) !important;color:#02131f !important;font-weight:800}
</style>
</head>
<body>
<header>
  <svg viewBox="0 0 64 64">
    <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
    <circle cx="32" cy="32" r="28" fill="none" stroke="url(#g)" stroke-width="3"/>
    <ellipse cx="32" cy="32" rx="28" ry="11" fill="none" stroke="url(#g)" stroke-width="2" transform="rotate(35 32 32)"/>
    <ellipse cx="32" cy="32" rx="28" ry="11" fill="none" stroke="url(#g)" stroke-width="2" transform="rotate(-35 32 32)"/>
    <circle cx="32" cy="32" r="6" fill="url(#g)"/>
  </svg>
  <div>
    <div class="brand">GENESIS AI</div>
    <div class="sub">Universal Portable Device</div>
  </div>
  <div class="grow"></div>
  <div class="tabs">
    <button class="tab active" id="tabChat">&#128172; Chat</button>
    <button class="tab" id="tabStudio">&#127912; Image Studio</button>
  </div>
  <div class="chip"><span class="dot on" id="espDot"></span><span id="espState">ESP32 OK</span></div>
  <button id="gear" style="background:none;border:none;color:var(--dim);padding:4px;font-size:16px" title="Settings">&#9881;</button>
</header>
<div class="tbar">
  <span>AP: <b>GENESIS_AI</b></span>
  <span>IP: <b>192.168.4.1</b></span>
  <span>Clients: <b id="apNum">1</b></span>
  <span>Brain: <b id="brainName">GEMINI 3.5</b></span>
  <span>Heap: <b id="heapKb">--</b>KB</span>
</div>

<!-- CHAT VIEW -->
<div class="view active" id="chatView"></div>
<form id="chatForm">
  <textarea id="q" rows="1" placeholder="Ask anything (world knowledge, math, coding, essays)..."></textarea>
  <button class="btn-send" id="send" type="submit">Send</button>
</form>

<!-- IMAGE STUDIO VIEW -->
<div class="view" id="studioView">
  <div class="studio-grid">
    <div class="card">
      <div class="card-title">
        <span>Prompt &amp; Style</span>
        <span style="font-size:10px;color:var(--cyan)">FLUX.1 NEURAL</span>
      </div>
      <div>
        <div class="p-label">Prompt:</div>
        <textarea id="imgPrompt" rows="3" placeholder="Describe the image you want to create..."></textarea>
      </div>
      <div class="sugg" style="justify-content:flex-start">
        <button type="button" class="s-preset">Neon cybernetic owl</button>
        <button type="button" class="s-preset">Bioluminescent forest</button>
        <button type="button" class="s-preset">Mars rover at sunset</button>
      </div>
      <div>
        <div class="p-label">Artistic Style:</div>
        <div class="chip-grid" id="styleGrid">
          <button type="button" class="c-btn sel" data-style="Photorealistic">Photoreal</button>
          <button type="button" class="c-btn" data-style="Anime / Manga">Anime</button>
          <button type="button" class="c-btn" data-style="Cyberpunk">Cyberpunk</button>
          <button type="button" class="c-btn" data-style="Cinematic">Cinematic</button>
          <button type="button" class="c-btn" data-style="Digital Art">Digital Art</button>
          <button type="button" class="c-btn" data-style="Dark Fantasy">Fantasy</button>
          <button type="button" class="c-btn" data-style="Watercolor">Watercolor</button>
          <button type="button" class="c-btn" data-style="3D Render">3D Render</button>
        </div>
      </div>
      <div>
        <div class="p-label">Aspect Ratio:</div>
        <div class="aspect-row" id="aspectRow">
          <button type="button" class="a-btn sel" data-aspect="1:1">1:1</button>
          <button type="button" class="a-btn" data-aspect="16:9">16:9</button>
          <button type="button" class="a-btn" data-aspect="9:16">9:16</button>
          <button type="button" class="a-btn" data-aspect="4:3">4:3</button>
          <button type="button" class="a-btn" data-aspect="3:4">3:4</button>
        </div>
      </div>
      <div>
        <div class="p-label">Reference Image (Optional Edit / Variation):</div>
        <div class="drop-zone" id="dropZone">
          <span id="dropText">&#128247; Tap or drag image to upload</span>
          <img id="refPreview" alt="Ref">
          <input type="file" id="refFile" accept="image/*" style="display:none">
        </div>
      </div>
      <button class="btn-gen" id="btnGen" type="button">&#10024; Generate Image</button>
      <div class="progress-bar" id="pBar"><div class="progress-fill" id="pFill"></div></div>
      <div id="genStatus" style="font-size:11px;color:var(--dim);text-align:center">Ready for generation</div>
    </div>

    <div style="display:flex;flex-direction:column;gap:14px">
      <div class="card" style="padding:0">
        <div class="canvas-card">
          <div class="canvas-empty" id="canvasEmpty">
            <svg viewBox="0 0 24 24" fill="none" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
            <div style="font-weight:700">Image Studio Canvas</div>
            <div style="font-size:11px">Generated artwork will render here and sync to your ESP32 TFT.</div>
          </div>
          <img id="mainImg" alt="Generated Art">
        </div>
        <div class="canvas-bar">
          <button class="btn-sub" id="btnDownload" disabled>&#11015; Save to Device</button>
          <button class="btn-sub" id="btnSyncTft" disabled>&#128250; Sync to TFT</button>
        </div>
      </div>
      <div class="card">
        <div class="card-title">
          <span>Previous Creations</span>
          <button id="btnClearHist" style="background:none;border:none;color:var(--dim);font-size:10px">Clear</button>
        </div>
        <div class="history-grid" id="histGrid"></div>
      </div>
    </div>
  </div>
</div>

<!-- SETTINGS DRAWER -->
<div class="drawer" id="drawer">
  <div class="dcard">
    <h3>GENESIS AI Configuration</h3>
    <label>AI Mode:</label>
    <select id="providerMode">
      <option value="cloudflare_gateway">OmniModel Gateway (Claude 3.7, Ollama &amp; Gemini)</option>
      <option value="direct_gemini">Google Gemini AI (Direct Cloud)</option>
      <option value="custom_relay">Custom HTTPS Relay Service</option>
    </select>
    <div id="geminiConfigBlock">
      <label>Google Gemini API Key:</label>
      <input id="geminiKeyInput" type="text" placeholder="Enter Gemini API key">
      <label>Model Version:</label>
      <select id="modelSel">
        <option value="gemini-3.5-flash-lite">Gemini 3.5 Flash-Lite (Fastest &amp; SOTA)</option>
        <option value="gemini-3.5-flash">Gemini 3.5 Flash (Deep Thinking)</option>
        <option value="gemini-flash-latest">Gemini Flash (Latest)</option>
      </select>
    </div>
    <div id="relayConfigBlock" style="display:none">
      <label>Relay URL:</label>
      <input id="relayUrl" type="url" placeholder="https://your-relay-domain.workers.dev/api/chat">
    </div>
    <div class="banner">
      <b>Mobile Data Note:</b> When your phone is connected to Wi-Fi <code>GENESIS_AI</code>, Android may show a prompt: <i>"Wi-Fi has no internet"</i>. Tap it and select <b>"Stay connected / Use mobile data"</b> so the browser can reach Google Gemini over cellular data while commanding the ESP32 over Wi-Fi.
    </div>
    <div class="row-btn">
      <button id="btnPage">Next TFT Page</button>
      <button id="btnClear">Clear Screen</button>
    </div>
    <div class="row-btn">
      <button id="btnSave" class="btn-pri">Save &amp; Close</button>
      <button id="btnClose">Close</button>
    </div>
  </div>
</div>

<script>
const $ = s => document.querySelector(s), $$ = s => document.querySelectorAll(s);
const chatView = $('#chatView'), studioView = $('#studioView'), q = $('#q'), send = $('#send');
const tabChat = $('#tabChat'), tabStudio = $('#tabStudio'), chatForm = $('#chatForm');
const espDot = $('#espDot'), espState = $('#espState'), brainName = $('#brainName'), apNum = $('#apNum'), heapKb = $('#heapKb');
const drawer = $('#drawer'), providerMode = $('#providerMode'), geminiKeyInput = $('#geminiKeyInput'), modelSel = $('#modelSel'), relayUrl = $('#relayUrl');
const geminiConfigBlock = $('#geminiConfigBlock'), relayConfigBlock = $('#relayConfigBlock');
const imgPrompt = $('#imgPrompt'), btnGen = $('#btnGen'), pBar = $('#pBar'), pFill = $('#pFill'), genStatus = $('#genStatus');
const canvasEmpty = $('#canvasEmpty'), mainImg = $('#mainImg'), btnDownload = $('#btnDownload'), btnSyncTft = $('#btnSyncTft'), histGrid = $('#histGrid');
const dropZone = $('#dropZone'), dropText = $('#dropText'), refPreview = $('#refPreview'), refFile = $('#refFile');

let busy = false, curAbort = null, curGenImg = null;
let curStyle = 'Photorealistic', curAspect = '1:1', refBase64 = null;
let chatHistory = [];

let activeMode = localStorage.getItem('genesis_provider_mode') || 'cloudflare_gateway';
let activeGeminiKey = localStorage.getItem('genesis_gemini_key') || '';
let activeModel = localStorage.getItem('genesis_model') || 'gemini-3.5-flash-lite';
let activeRelayUrl = localStorage.getItem('genesis_relay_url') || 'https://modules-similar-which-equality.trycloudflare.com/api/iot/chat';

providerMode.value = activeMode;
geminiKeyInput.value = activeGeminiKey;
modelSel.value = activeModel;
relayUrl.value = activeRelayUrl;
brainName.textContent = activeMode === 'cloudflare_gateway' ? 'CLAUDE + OMNI' : activeModel.replace('gemini-','').toUpperCase();

function updateSettingsUI(){
  if(providerMode.value === 'direct_gemini'){
    geminiConfigBlock.style.display = 'block';
    relayConfigBlock.style.display = 'none';
  } else if(providerMode.value === 'cloudflare_gateway'){
    geminiConfigBlock.style.display = 'none';
    relayConfigBlock.style.display = 'none';
  } else {
    geminiConfigBlock.style.display = 'none';
    relayConfigBlock.style.display = 'block';
  }
}
providerMode.onchange = updateSettingsUI;
updateSettingsUI();

// Tab Switching
tabChat.onclick = () => { tabChat.classList.add('active'); tabStudio.classList.remove('active'); chatView.classList.add('active'); studioView.classList.remove('active'); chatForm.style.display = 'flex'; };
tabStudio.onclick = () => { tabStudio.classList.add('active'); tabChat.classList.remove('active'); studioView.classList.add('active'); chatView.classList.remove('active'); chatForm.style.display = 'none'; };

// Style & Aspect Selection
$$('#styleGrid .c-btn').forEach(b => b.onclick = () => { $$('#styleGrid .c-btn').forEach(x => x.classList.remove('sel')); b.classList.add('sel'); curStyle = b.dataset.style; });
$$('#aspectRow .a-btn').forEach(b => b.onclick = () => { $$('#aspectRow .a-btn').forEach(x => x.classList.remove('sel')); b.classList.add('sel'); curAspect = b.dataset.aspect; });
$$('.s-preset').forEach(b => b.onclick = () => { imgPrompt.value = b.textContent; });

// Reference Image Upload
dropZone.onclick = () => refFile.click();
refFile.onchange = e => {
  const f = e.target.files[0];
  if(!f) return;
  const reader = new FileReader();
  reader.onload = ev => {
    refBase64 = ev.target.result;
    refPreview.src = refBase64;
    refPreview.style.display = 'block';
    dropText.textContent = 'Reference Loaded (Tap to Change)';
  };
  reader.readAsDataURL(f);
};

function esc(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function md(s){
  let t = esc(s), blocks = [];
  t = t.replace(/```[\w+-]*\n?([\s\S]*?)```/g,(_,c)=>{blocks.push('<pre><code>'+c.replace(/\n$/,'')+'</code></pre>');return '\u0000'+(blocks.length-1)+'\u0000'});
  t = t.replace(/`([^`\n]+)`/g,'<code>$1</code>').replace(/\*\*([^*\n]+)\*\*/g,'<b>$1</b>')
       .replace(/^#{1,6}\s*(.+)$/gm,'<b>$1</b>').replace(/^\s*[-*]\s+/gm,'• ');
  return t.replace(/\u0000(\d+)\u0000/g,(_,i)=>blocks[+i]);
}

function initChatWelcome(){
  chatView.innerHTML = `<div class="empty">
    <svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="28" fill="none" stroke="#22d3ee" stroke-width="2"/><ellipse cx="32" cy="32" rx="28" ry="11" fill="none" stroke="#3b82f6" stroke-width="2" transform="rotate(35 32 32)"/><ellipse cx="32" cy="32" rx="28" ry="11" fill="none" stroke="#3b82f6" stroke-width="2" transform="rotate(-35 32 32)"/><circle cx="32" cy="32" r="6" fill="#22d3ee"/></svg>
    <h2>GENESIS AI Assistant</h2>
    <div style="font-size:12px;margin:8px 0">Ask anything: coding, math, world facts, explanations, or creative writing. Answers sync live to the 2.4" display.</div>
    <div class="sugg"></div>
  </div>`;
  ['What is quantum computing?','Write a python factorial function','Explain gravity simply','How do rocket engines work?'].forEach(t=>{
    const b=document.createElement('button');b.textContent=t;b.onclick=()=>{q.value=t;chatForm.requestSubmit()};chatView.querySelector('.sugg').appendChild(b)});
}

function addMsg(cls, html){const d=document.createElement('div');d.className='msg '+cls;d.innerHTML=html;chatView.appendChild(d);chatView.scrollTop=chatView.scrollHeight;return d}
function setBusy(b, label){
  busy = b; send.disabled = b;
  if(b){ espDot.className='dot busy'; espState.textContent=label||'THINKING'; }
  else { espDot.className='dot on'; espState.textContent='ESP32 OK'; }
}

async function syncEsp32(){
  try{
    const r = await fetch('/api/status', {cache:'no-store'});
    if(r.ok){
      const j = await r.json();
      apNum.textContent = j.clients !== undefined ? j.clients : '1';
      heapKb.textContent = Math.round((j.heap || 0) / 1024);
      if(!busy){ espDot.className = 'dot on'; espState.textContent = 'ESP32 OK'; }
    }
  }catch(e){
    if(!busy){ espDot.className = 'dot'; espState.textContent = 'ESP32 UNREACHABLE'; }
  }
}

async function notifyEsp32(payload){
  try{
    await fetch('/api/feed', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
  }catch(e){}
}

// ------------------------------------------------------------- Direct Cloud AI Engine
async function callGeminiDirect(questionText, signal){
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${activeModel}:generateContent?key=${activeGeminiKey}`;
  const contents = chatHistory.slice(-8).concat([{ role: 'user', parts: [{ text: questionText }] }]);
  const payload = {
    contents: contents,
    generationConfig: { temperature: 0.7, maxOutputTokens: 2048 }
  };
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: signal
  });
  if(!r.ok){
    const errData = await r.json().catch(() => ({}));
    throw new Error(errData?.error?.message || `Google API HTTP ${r.status}`);
  }
  const data = await r.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if(!text) throw new Error('Model returned empty response');
  return text;
}

async function callRelay(questionText, signal){
  const endpoint = activeMode === 'cloudflare_gateway'
    ? 'https://modules-similar-which-equality.trycloudflare.com/api/iot/chat?format=json'
    : activeRelayUrl;
  const r = await fetch(endpoint, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ prompt: questionText, q: questionText }),
    signal: signal
  });
  if(!r.ok) throw new Error(`Gateway HTTP ${r.status}`);
  const data = await r.json();
  return data.text || data.response || (typeof data === 'string' ? data : JSON.stringify(data));
}

async function ask(questionText){
  if(!chatView.querySelector('.msg')) chatView.innerHTML='';
  addMsg('me', esc(questionText));
  const bubble = addMsg('ai', '<span class="think"><i></i><i></i><i></i></span>');
  setBusy(true, 'AI GENERATING');

  notifyEsp32({ state: 'THINKING', question: questionText, provider: 'gemini', model: activeModel, text: '' });
  curAbort = new AbortController();

  try{
    let answerText = '';
    let usedProvider = activeMode;
    if(activeMode === 'direct_gemini'){
      answerText = await callGeminiDirect(questionText, curAbort.signal);
      usedProvider = 'Google Gemini 3.5';
    } else {
      try {
        answerText = await callRelay(questionText, curAbort.signal);
        usedProvider = 'Gateway (Claude/Ollama)';
      } catch(relayErr) {
        console.warn('Gateway relay offline (PC off), falling back to Direct Gemini AI:', relayErr);
        answerText = await callGeminiDirect(questionText, curAbort.signal);
        usedProvider = 'Gemini 3.5 (PC Offline Mode)';
      }
    }

    // Record turn in chat history
    chatHistory.push({ role: 'user', parts: [{ text: questionText }] });
    chatHistory.push({ role: 'model', parts: [{ text: answerText }] });

    // Smooth typewriter reveal
    for(let i = 0; i < answerText.length; i += 4){
      bubble.innerHTML = md(answerText.substring(0, i + 4));
      chatView.scrollTop = chatView.scrollHeight;
      if(answerText.length < 800) await new Promise(res => setTimeout(res, 5));
    }

    const metaHtml = `<div class="meta"><span class="tag-relay">GOOGLE AI</span><span>${esc(activeModel)}</span><span class="tag-tft">TFT SYNCED</span></div>`;
    bubble.innerHTML = md(answerText) + metaHtml;
    chatView.scrollTop = chatView.scrollHeight;

    notifyEsp32({ state: 'ANSWERED', question: questionText, provider: 'gemini', model: activeModel, text: answerText });
  }catch(err){
    bubble.classList.add('err');
    let helpMsg = '';
    if(err.message.includes('Failed to fetch') || err.message.includes('NetworkError')){
      helpMsg = `<br><br><b>How to enable Mobile Data on Android:</b><br>
1. Check your top notification bar for <i>"Wi-Fi has no internet access"</i>.<br>
2. Tap it and select <b>"Stay connected / Use mobile data"</b>.<br>
3. In Android <i>Settings &rarr; Wi-Fi &rarr; Advanced</i>: enable <b>"Switch to mobile data"</b>.<br>
4. If on Laptop: connect to internet or check Wi-Fi.<br><br>
<button class="btn-sub" style="width:auto;padding:5px 12px;margin-top:4px" onclick="ask('${esc(questionText)}')">&#8635; Retry Question</button>`;
    }
    bubble.innerHTML = `<b>AI Error:</b> ${esc(err.message)}${helpMsg}`;
    notifyEsp32({ state: 'ERROR', question: questionText, provider: 'gemini', model: activeModel, text: err.message });
  }
  setBusy(false); curAbort = null;
}

// ------------------------------------------------------------- Image Studio Generation
const STYLE_PROMPTS = {
  'Photorealistic': 'photorealistic, 8k raw photography, hyper-detailed, depth of field, studio lighting',
  'Anime / Manga': 'anime aesthetic, clean linework, vibrant makoto shinkai aesthetic, high quality illustration',
  'Cyberpunk': 'cyberpunk style, neon lights, rainy reflections, futuristic cityscape, octane render',
  'Cinematic': 'cinematic film still, 35mm photograph, dramatic movie lighting, depth of field',
  'Digital Art': 'digital art masterpiece, trending on artstation, concept art, intricate details',
  'Dark Fantasy': 'dark fantasy, dramatic shadows, mysterious fog, glowing runes, unreal engine 5 render',
  'Watercolor': 'watercolor painting, expressive pigment bleeding, textured paper, pastel colors',
  '3D Render': '3d octane render, ray tracing, smooth textures, ambient occlusion, 8k cgi'
};

const ASPECT_DIMS = {
  '1:1': [512, 512],
  '16:9': [768, 432],
  '9:16': [432, 768],
  '4:3': [640, 480],
  '3:4': [480, 640]
};

async function generateImage(){
  const prompt = imgPrompt.value.trim();
  if(!prompt || busy) return;

  setBusy(true, 'GENERATING ART');
  btnGen.disabled = true;
  pBar.style.display = 'block';
  pFill.style.width = '20%';
  genStatus.textContent = 'Synthesizing FLUX.1 neural latents...';

  const [w, h] = ASPECT_DIMS[curAspect] || [512, 512];
  const mod = STYLE_PROMPTS[curStyle] || '';
  const fullPrompt = `${prompt}, ${mod}`;
  const seed = Math.floor(Math.random() * 999999);
  const encoded = encodeURIComponent(fullPrompt);
  const genUrl = `https://image.pollinations.ai/prompt/${encoded}?width=${w}&height=${h}&seed=${seed}&model=flux&nologo=true`;

  try{
    pFill.style.width = '55%';
    genStatus.textContent = 'Downloading high-resolution render...';

    const resp = await fetch(genUrl);
    if(!resp.ok) throw new Error(`Provider HTTP ${resp.status}`);

    const blob = await resp.blob();
    const blobUrl = URL.createObjectURL(blob);

    pFill.style.width = '80%';
    genStatus.textContent = 'Rendering preview canvas...';

    mainImg.src = blobUrl;
    mainImg.style.display = 'block';
    canvasEmpty.style.display = 'none';
    btnDownload.disabled = false;
    btnSyncTft.disabled = false;

    curGenImg = {
      id: 'img_' + Date.now(),
      prompt: prompt,
      style: curStyle,
      aspect: curAspect,
      blobUrl: blobUrl,
      blob: blob
    };

    saveHistory(curGenImg);
    pFill.style.width = '90%';
    genStatus.textContent = 'Streaming RGB565 thumbnail to ESP32 TFT...';

    await streamToTft(mainImg, prompt, curStyle, curAspect);

    pFill.style.width = '100%';
    genStatus.textContent = 'Generated & Synced to TFT successfully!';
  }catch(err){
    genStatus.textContent = `Generation error: ${err.message}. If using phone, ensure mobile data is enabled.`;
  }finally{
    setTimeout(() => { pBar.style.display = 'none'; pFill.style.width = '0%'; }, 2000);
    setBusy(false);
    btnGen.disabled = false;
  }
}

// ------------------------------------------------------------- TFT Chunked RGB565 Streamer
async function streamToTft(imgEl, prompt, style, aspect){
  let tw = 160, th = 120;
  if(aspect === '1:1'){ tw = 140; th = 140; }
  else if(aspect === '16:9'){ tw = 240; th = 135; }
  else if(aspect === '9:16'){ tw = 84; th = 150; }
  else if(aspect === '4:3'){ tw = 192; th = 144; }
  else if(aspect === '3:4'){ tw = 112; th = 150; }

  const tx = Math.floor((320 - tw) / 2);
  const ty = Math.floor(54 + (156 - th) / 2);

  const canvas = document.createElement('canvas');
  canvas.width = tw; canvas.height = th;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(imgEl, 0, 0, tw, th);
  const data = ctx.getImageData(0, 0, tw, th).data;

  try{
    await fetch('/api/tft/image/start', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ x: tx, y: ty, w: tw, h: th, prompt: prompt, style: style, aspect: aspect })
    });
  }catch(e){ return; }

  const linesPerChunk = 10;
  for(let y = 0; y < th; y += linesPerChunk){
    const chunkH = Math.min(linesPerChunk, th - y);
    let rawStr = '';
    for(let cy = y; cy < y + chunkH; cy++){
      for(let cx = 0; cx < tw; cx++){
        const i = (cy * tw + cx) * 4;
        const r = data[i], g = data[i+1], b = data[i+2];
        const rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
        rawStr += String.fromCharCode((rgb565 >> 8) & 0xFF, rgb565 & 0xFF);
      }
    }
    const b64 = btoa(rawStr);
    try{
      await fetch('/api/tft/image/chunk', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ x: tx, y: ty + y, w: tw, h: chunkH, data: b64 })
      });
    }catch(e){}
  }

  try{
    await fetch('/api/tft/image/finish', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ style: style, aspect: aspect })
    });
  }catch(e){}
}

function saveHistory(item){
  try{
    let hist = JSON.parse(localStorage.getItem('genesis_img_hist') || '[]');
    hist.unshift({ id: item.id, prompt: item.prompt, style: item.style, aspect: item.aspect });
    if(hist.length > 12) hist.pop();
    localStorage.setItem('genesis_img_hist', JSON.stringify(hist));
    renderHistory();
  }catch(e){}
}

function renderHistory(){
  try{
    let hist = JSON.parse(localStorage.getItem('genesis_img_hist') || '[]');
    histGrid.innerHTML = '';
    hist.forEach(h => {
      const d = document.createElement('div');
      d.className = 'history-item';
      d.title = `${h.prompt} (${h.style})`;
      d.innerHTML = `<div style="background:var(--card);width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:9px;color:var(--cyan);padding:4px;text-align:center">${esc(h.prompt.substring(0,20))}</div>`;
      d.onclick = () => { imgPrompt.value = h.prompt; };
      histGrid.appendChild(d);
    });
  }catch(e){}
}

btnGen.onclick = generateImage;
btnDownload.onclick = () => {
  if(!curGenImg || !curGenImg.blobUrl) return;
  const a = document.createElement('a');
  a.href = curGenImg.blobUrl;
  a.download = `genesis_ai_${Date.now()}.jpg`;
  a.click();
};
btnSyncTft.onclick = () => {
  if(mainImg && curGenImg) streamToTft(mainImg, curGenImg.prompt, curGenImg.style, curGenImg.aspect);
};
$('#btnClearHist').onclick = () => { localStorage.removeItem('genesis_img_hist'); renderHistory(); };

chatForm.onsubmit = e => { e.preventDefault(); const t = q.value.trim(); if(!t || busy) return; q.value = ''; q.style.height = 'auto'; ask(t); };
q.addEventListener('keydown', e => { if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); chatForm.requestSubmit(); } });
q.addEventListener('input', () => { q.style.height = 'auto'; q.style.height = Math.min(q.scrollHeight, 120) + 'px'; });

$('#gear').onclick = () => drawer.classList.add('show');
$('#btnClose').onclick = () => drawer.classList.remove('show');
$('#btnSave').onclick = () => {
  activeMode = providerMode.value;
  activeGeminiKey = geminiKeyInput.value.trim() || activeGeminiKey;
  activeModel = modelSel.value;
  activeRelayUrl = relayUrl.value.trim() || activeRelayUrl;

  localStorage.setItem('genesis_provider_mode', activeMode);
  localStorage.setItem('genesis_gemini_key', activeGeminiKey);
  localStorage.setItem('genesis_model', activeModel);
  localStorage.setItem('genesis_relay_url', activeRelayUrl);
  brainName.textContent = activeModel.replace('gemini-','').toUpperCase();
  drawer.classList.remove('show');
};
$('#btnPage').onclick = () => fetch('/api/page', {method: 'POST'});
$('#btnClear').onclick = () => { fetch('/api/clear', {method: 'POST'}); initChatWelcome(); drawer.classList.remove('show'); };

initChatWelcome();
renderHistory();
syncEsp32();
setInterval(syncEsp32, 4000);
</script>
</body>
</html>
)rawliteral";