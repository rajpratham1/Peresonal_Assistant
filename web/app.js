"use strict";
/* ════════════════════════════════════════════════════════════════════════════
   Viru AI Assistant – app.js  v3.0
   Full frontend logic: Dashboard, Chat, Notes, Reminders, Contacts,
   System Monitor, File Browser, History, Screenshots.
════════════════════════════════════════════════════════════════════════════ */

// ── Config ───────────────────────────────────────────────────────────────────
let TYPING_SPEED = 7;
let ttsEnabled   = true;
let selectedVoice = null;
let sidebarCollapsed = false;
let cpuChart, ramChart;
let sysInterval = null;

// Default file-browser paths (server provides real paths via API)
let desktopPath   = "";
let docsPath      = "";
let downloadsPath = "";
let currentPath   = "";
let parentPath    = "";

// Chat message counter for badge
let unreadChat = 0;
let activePanel = "dashboard";

// ── DOM helpers ──────────────────────────────────────────────────────────────
const $  = id => document.getElementById(id);
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
};

// ── Toast ────────────────────────────────────────────────────────────────────
function toast(msg, type="info") {
  const t = $("toast");
  t.textContent = msg;
  t.style.background = type === "error" ? "var(--surface1)" : "var(--surface1)";
  t.style.borderLeft = `3px solid ${type==="error"?"var(--red)":type==="ok"?"var(--green)":"var(--accent)"}`;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3000);
}

// ── Sidebar toggle ───────────────────────────────────────────────────────────
function toggleSidebar() {
  sidebarCollapsed = !sidebarCollapsed;
  document.querySelector(".sidebar").classList.toggle("collapsed", sidebarCollapsed);
}

// ── Panel navigation ─────────────────────────────────────────────────────────
function goto(name) {
  activePanel = name;
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  $(`panel-${name}`)?.classList.add("active");
  $(`nb-${name}`)?.classList.add("active");

  // Reset unread chat badge when entering chat
  if (name === "chat") {
    unreadChat = 0;
    $("badge-chat").style.display = "none";
  }

  // Lazy-load data for each panel
  if (name === "dashboard")   loadDashboard();
  if (name === "notes")       loadNotes();
  if (name === "reminders")   loadReminders();
  if (name === "contacts")    loadContacts();
  if (name === "system")      startSysMonitor();
  if (name === "files")       initFileBrowser();
  if (name === "history")     loadHistory();
  if (name === "screenshots") loadScreenshots();

  // Stop system monitor when leaving
  if (name !== "system" && sysInterval) {
    clearInterval(sysInterval);
    sysInterval = null;
  }
}

// ── Status polling ───────────────────────────────────────────────────────────
async function pollStatus() {
  try {
    const d = await fetch("/api/status").then(r => r.json());
    const dot = $("sdot"), txt = $("stxt");
    if (d.llm_online) {
      dot.className = "sdot on"; txt.textContent = "LLM Online";
    } else {
      dot.className = "sdot off"; txt.textContent = "LLM Offline";
    }
  } catch {
    $("sdot").className = "sdot off";
    $("stxt").textContent = "Server Down";
  }
}
pollStatus();
setInterval(pollStatus, 12000);

/* ══════════════════════════════════════════════════════════════════════════
   DASHBOARD
══════════════════════════════════════════════════════════════════════════ */
async function loadDashboard() {
  loadWeather();
  loadQR();
  try {
    const d = await fetch("/api/dashboard").then(r => r.json());

    // Stat rings
    setRing("cpu-ring","cpu-val", d.cpu_percent);
    setRing("ram-ring","ram-val", d.ram_percent);
    setRing("disk-ring","disk-val", d.disk_percent);

    // Tiles
    $("tile-notes").textContent    = d.notes_count;
    $("tile-rem").textContent      = d.pending_reminders;
    $("tile-contacts").textContent = "–";
    $("tile-msgs").textContent     = d.recent_commands?.length ?? 0;

    // Reminder badge
    if (d.pending_reminders > 0) {
      $("badge-rem").textContent    = d.pending_reminders;
      $("badge-rem").style.display  = "flex";
    }

    // Recent commands
    const rc = $("recent-list");
    rc.innerHTML = "";
    if (!d.recent_commands?.length) {
      rc.innerHTML = '<div class="empty"><div class="empty-icon">💬</div><div class="empty-text">No commands yet</div></div>';
    } else {
      d.recent_commands.forEach(c => {
        const row = el("div","recent-item");
        row.innerHTML = `<span class="recent-intent">${c.intent||"?"}</span><span class="recent-cmd">${esc(c.command)}</span>`;
        rc.appendChild(row);
      });
    }

    // Contacts tile (load separately)
    fetch("/api/contacts").then(r=>r.json()).then(cs => {
      $("tile-contacts").textContent = cs.length;
    }).catch(()=>{});

  } catch(e) { console.error("Dashboard load error:", e); }
}

function setRing(ringId, valId, pct) {
  const r = $(ringId), v = $(valId);
  if (!r || !v) return;
  r.setAttribute("stroke-dasharray", `${pct.toFixed(1)}, 100`);
  v.textContent = pct.toFixed(0) + "%";
}

async function loadWeather() {
  try {
    const w = await fetch("/api/weather").then(r => r.json());
    if (w.error) { $("w-desc").textContent = "Weather unavailable"; return; }
    $("w-icon").textContent  = w.icon;
    $("w-temp").textContent  = `${w.temp_c}°C`;
    $("w-desc").textContent  = w.desc;
    $("w-city").textContent  = w.city;
    $("w-humidity").textContent = `💧 ${w.humidity}%`;
    $("w-wind").textContent     = `💨 ${w.wind_kmph} km/h`;
    $("w-feels").textContent    = `🌡️ ${w.feels_like}°C feels`;
  } catch { $("w-desc").textContent = "Weather unavailable"; }
}

async function loadQR() {
  try {
    const q = await fetch("/api/qrcode").then(r => r.json());
    const c = $("qr-container");
    if (q.img) {
      c.innerHTML = `<img src="${q.img}" alt="QR Code"/>`;
    } else {
      c.innerHTML = `<div style="font-size:2rem">📲</div>`;
    }
    $("qr-url").textContent = q.url;
  } catch { $("qr-container").innerHTML = ""; }
}

async function quickCmd(cmd) {
  goto("chat");
  await new Promise(r => setTimeout(r, 100));
  $("msg-in").value = cmd;
  sendMsg(null);
}

/* ══════════════════════════════════════════════════════════════════════════
   CHAT
══════════════════════════════════════════════════════════════════════════ */
function appendBubble(role, text, badge) {
  const vp   = $("chat-vp");
  const row  = el("div", `brow ${role}`);
  const rl   = el("div", "brow-role", role === "user" ? "You" : "Viru");
  const bub  = el("div", "bub");
  row.appendChild(rl);
  row.appendChild(bub);
  if (badge) {
    const b = el("div","bub-badge", `🎯 ${esc(badge)}`);
    row.appendChild(b);
  }
  vp.appendChild(row);
  scrollChat();
  return bub;
}

function scrollChat() {
  const vp = $("chat-vp");
  vp.scrollTop = vp.scrollHeight;
}

function showThinking() {
  const vp  = $("chat-vp");
  const row = el("div","brow ai");
  row.id    = "thinking-row";
  const rl  = el("div","brow-role","Viru");
  const dots = el("div","thinking-dots","<span></span><span></span><span></span>");
  row.appendChild(rl);
  row.appendChild(dots);
  vp.appendChild(row);
  scrollChat();
}

function removeThinking() {
  $("thinking-row")?.remove();
}

function typeText(el, text, onDone) {
  el.classList.add("typing-cur");
  let i = 0;
  const tick = () => {
    if (i <= text.length) {
      el.textContent = text.slice(0, i++);
      setTimeout(tick, TYPING_SPEED);
    } else {
      el.classList.remove("typing-cur");
      scrollChat();
      onDone?.();
    }
  };
  tick();
}

async function sendMsg(e) {
  if (e) e.preventDefault();
  const inp  = $("msg-in");
  const text = inp.value.trim();
  if (!text) return;
  inp.value = "";

  appendBubble("user", text);
  scrollChat();
  showThinking();

  try {
    const res  = await fetch("/api/chat",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({message: text})
    });
    const data = await res.json();
    removeThinking();

    const badge = data.intent ? `Intent: ${data.intent}` : null;
    const bub   = appendBubble("ai","",badge);
    typeText(bub, data.reply || "I didn't understand that.", () => {
      speakText(data.reply || "");
    });

    // Increment badge if not on chat panel
    if (activePanel !== "chat") {
      unreadChat++;
      $("badge-chat").textContent    = unreadChat;
      $("badge-chat").style.display  = "flex";
    }

  } catch(err) {
    removeThinking();
    const b = appendBubble("ai","");
    typeText(b, `Server error: ${err.message}. Is the Flask server running?`);
  }
}

// Boot message
(function() {
  const b = appendBubble("ai","");
  typeText(b, "System online. Ask me anything — I can search the web, open apps, set reminders, read your screen, and much more.");
})();

/* ══════════════════════════════════════════════════════════════════════════
   NOTES
══════════════════════════════════════════════════════════════════════════ */
let allNotes = [];

async function loadNotes() {
  const g = $("notes-grid");
  g.innerHTML = '<div class="spinner"></div>';
  try {
    allNotes = await fetch("/api/notes").then(r => r.json());
    renderNotes(allNotes);
  } catch { g.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-text">Failed to load notes</div></div>'; }
}

function renderNotes(notes) {
  const g = $("notes-grid");
  g.innerHTML = "";
  if (!notes.length) {
    g.innerHTML = '<div class="empty"><div class="empty-icon">📝</div><div class="empty-text">No notes yet. Add your first!</div></div>';
    return;
  }
  notes.forEach(n => {
    const c = el("div","note-card");
    c.innerHTML = `
      <button class="note-del" onclick="deleteNote(${n.id},this.parentElement)" title="Delete">✕</button>
      <div class="note-text">${esc(n.content)}</div>
      <div class="note-meta">${fmtDate(n.created_at)}</div>`;
    g.appendChild(c);
  });
}

function filterNotes() {
  const q = $("notes-search").value.toLowerCase();
  renderNotes(q ? allNotes.filter(n => n.content.toLowerCase().includes(q)) : allNotes);
}

function showAddNote() { openModal("note-modal"); $("note-content").value = ""; $("note-content").focus(); }

async function saveNote() {
  const content = $("note-content").value.trim();
  if (!content) { toast("Note cannot be empty","error"); return; }
  try {
    await fetch("/api/notes",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content})});
    closeModal("note-modal");
    toast("Note saved","ok");
    loadNotes();
  } catch { toast("Failed to save note","error"); }
}

async function deleteNote(id, el) {
  if (!confirm("Delete this note?")) return;
  await fetch(`/api/notes/${id}`,{method:"DELETE"});
  el.remove();
  allNotes = allNotes.filter(n => n.id !== id);
  toast("Note deleted");
}

/* ══════════════════════════════════════════════════════════════════════════
   REMINDERS
══════════════════════════════════════════════════════════════════════════ */
async function loadReminders() {
  const c = $("rem-list");
  c.innerHTML = '<div class="spinner"></div>';
  try {
    const items = await fetch("/api/reminders").then(r => r.json());
    c.innerHTML = "";
    if (!items.length) {
      c.innerHTML = '<div class="empty"><div class="empty-icon">⏰</div><div class="empty-text">No reminders. Add one!</div></div>';
      return;
    }
    items.forEach(r => c.appendChild(remCard(r)));
    // Update badge
    const pending = items.filter(r => r.status==="pending").length;
    if (pending > 0) { $("badge-rem").textContent = pending; $("badge-rem").style.display = "flex"; }
    else $("badge-rem").style.display = "none";
  } catch { c.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-text">Failed to load</div></div>'; }
}

function remCard(r) {
  const kindIco = {alarm:"⏰",message:"💬",task:"✅"}[r.kind] || "📌";
  const d = el("div", `rem-item${r.status==="done"?" done":""}`);
  d.id = `rem-${r.id}`;
  d.innerHTML = `
    <div class="rem-kind-badge">${kindIco}</div>
    <div class="rem-body">
      <div class="rem-msg">${esc(r.message||r.target||"Reminder")}</div>
      <div class="rem-time">${fmtDate(r.trigger_at)}${r.target?" → "+esc(r.target):""}</div>
    </div>
    <div class="rem-actions">
      ${r.status==="pending"?`<button class="ra-btn done-btn" onclick="doneReminder(${r.id})">✓ Done</button>`:""}
      <button class="ra-btn del-btn" onclick="delReminder(${r.id})">🗑</button>
    </div>`;
  return d;
}

function showAddReminder() {
  openModal("rem-modal");
  // Default to now + 1 hour
  const d = new Date(Date.now() + 3600000);
  $("rem-time").value = d.toISOString().slice(0,16);
}

async function saveReminder() {
  const kind   = $("rem-kind").value;
  const time   = $("rem-time").value;
  const msg    = $("rem-msg").value.trim();
  const target = $("rem-target").value.trim() || null;
  if (!time) { toast("Please set a date/time","error"); return; }
  const trigger_at = new Date(time).toISOString().slice(0,19);
  await fetch("/api/reminders",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({kind,trigger_at,message:msg,target})});
  closeModal("rem-modal");
  toast("Reminder added","ok");
  loadReminders();
}

async function doneReminder(id) {
  await fetch(`/api/reminders/${id}/done`,{method:"POST"});
  const el = $(`rem-${id}`);
  if (el) el.classList.add("done");
  toast("Marked done","ok");
  loadReminders();
}

async function delReminder(id) {
  await fetch(`/api/reminders/${id}`,{method:"DELETE"});
  $(`rem-${id}`)?.remove();
  toast("Reminder deleted");
}

/* ══════════════════════════════════════════════════════════════════════════
   CONTACTS
══════════════════════════════════════════════════════════════════════════ */
let allContacts = [];

async function loadContacts() {
  const g = $("contacts-grid");
  g.innerHTML = '<div class="spinner"></div>';
  try {
    allContacts = await fetch("/api/contacts").then(r => r.json());
    renderContacts(allContacts);
  } catch { g.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-text">Failed to load</div></div>'; }
}

function renderContacts(contacts) {
  const g = $("contacts-grid");
  g.innerHTML = "";
  if (!contacts.length) {
    g.innerHTML = '<div class="empty"><div class="empty-icon">👥</div><div class="empty-text">No contacts. Add one!</div></div>';
    return;
  }
  contacts.forEach(c => {
    const initials = (c.name||"?").charAt(0).toUpperCase();
    const card = el("div","contact-card");
    card.innerHTML = `
      <button class="contact-del" onclick="delContact(${c.id},this.parentElement)">✕</button>
      <div class="contact-avatar">${initials}</div>
      <div class="contact-name">${esc(c.name)}</div>
      <div class="contact-phone">${c.phone ? "📞 "+esc(c.phone) : ""}</div>
      <div class="contact-email">${c.email ? "✉ "+esc(c.email) : ""}</div>
      <div class="contact-actions">
        ${c.phone ? `<button class="ca-btn" onclick="quickCmd('call ${esc(c.name)}')">📞 Call</button>` : ""}
        <button class="ca-btn" onclick="msgContact('${esc(c.name)}')">💬 Msg</button>
      </div>`;
    g.appendChild(card);
  });
}

function filterContacts() {
  const q = $("contacts-search").value.toLowerCase();
  renderContacts(q ? allContacts.filter(c => c.name.includes(q) || (c.phone||"").includes(q)) : allContacts);
}

function showAddContact() { openModal("contact-modal"); ["c-name","c-phone","c-email","c-wa"].forEach(id => $(id).value = ""); }

async function saveContact() {
  const name  = $("c-name").value.trim();
  const phone = $("c-phone").value.trim();
  const email = $("c-email").value.trim();
  const wa    = $("c-wa").value.trim();
  if (!name) { toast("Name is required","error"); return; }
  await fetch("/api/contacts",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({name,phone,email,whatsapp_name:wa})});
  closeModal("contact-modal");
  toast("Contact saved","ok");
  loadContacts();
}

async function delContact(id, el) {
  if (!confirm("Delete this contact?")) return;
  await fetch(`/api/contacts/${id}`,{method:"DELETE"});
  el.remove();
  toast("Contact deleted");
}

function msgContact(name) {
  goto("chat");
  setTimeout(() => {
    $("msg-in").value = `message ${name} saying `;
    $("msg-in").focus();
  }, 150);
}

/* ══════════════════════════════════════════════════════════════════════════
   SYSTEM MONITOR
══════════════════════════════════════════════════════════════════════════ */
function startSysMonitor() {
  initCharts();
  fetchSysInfo();
  if (!sysInterval) sysInterval = setInterval(fetchSysInfo, 2500);
}

function initCharts() {
  const cfg = (label, color) => ({
    type: "line",
    data: {
      labels: Array(30).fill(""),
      datasets:[{
        label, data: Array(30).fill(0),
        borderColor: color, backgroundColor: color+"22",
        borderWidth: 2, fill: true,
        tension: 0.4, pointRadius: 0
      }]
    },
    options:{
      responsive:true, animation:{duration:300},
      plugins:{legend:{display:false}},
      scales:{
        x:{display:false},
        y:{min:0,max:100,grid:{color:"rgba(255,255,255,.05)"},
           ticks:{color:"#6c7086",callback:v=>v+"%"}}
      }
    }
  });

  if (!cpuChart) {
    cpuChart = new Chart($("cpu-chart"), cfg("CPU","#cba6f7"));
    ramChart = new Chart($("ram-chart"), cfg("RAM","#89dceb"));
  }
}

async function fetchSysInfo() {
  try {
    const d = await fetch("/api/sysinfo").then(r=>r.json());

    // Push to charts
    const push = (chart, val) => {
      chart.data.datasets[0].data.push(val);
      chart.data.datasets[0].data.shift();
      chart.update("none");
    };
    push(cpuChart, d.cpu);
    push(ramChart, d.ram);

    $("cpu-chart-val").textContent = d.cpu.toFixed(0)+"%";
    $("ram-chart-val").textContent = d.ram.toFixed(0)+"%";
    $("si-disk").textContent  = d.disk.toFixed(0)+"%";
    $("si-sent").textContent  = d.net_sent_mb+" MB";
    $("si-recv").textContent  = d.net_recv_mb+" MB";

    // Full info on first load
    if (!$("si-boot").textContent || $("si-boot").textContent === "--") {
      const full = await fetch("/api/dashboard").then(r=>r.json());
      $("si-boot").textContent = full.boot_time;
      $("si-host").textContent = full.platform;
    }
  } catch {}
}

/* ══════════════════════════════════════════════════════════════════════════
   FILE BROWSER
══════════════════════════════════════════════════════════════════════════ */
async function initFileBrowser() {
  if (desktopPath) { filesLoad(desktopPath); return; }
  // Discover default paths from API
  try {
    const d = await fetch("/api/dashboard").then(r=>r.json());
    const home = d.platform || "";
    // Attempt desktop path from server home
    const test = await fetch(`/api/files?path=${encodeURIComponent(
      navigator.platform.includes("Win") ?
        `C:\\Users\\${(d.platform||"").split("\\").pop()}\\Desktop` :
        "/home"
    )}`).then(r=>r.json()).catch(()=>null);
    if (test?.path) { desktopPath = test.path; }
  } catch {}
  // Fall back
  desktopPath   = desktopPath   || "C:\\Users";
  docsPath      = docsPath      || "C:\\Users";
  downloadsPath = downloadsPath || "C:\\Users";
  filesLoad(desktopPath);
}

async function filesLoad(path) {
  const g = $("file-grid");
  g.innerHTML = '<div class="spinner"></div>';
  try {
    const d = await fetch(`/api/files?path=${encodeURIComponent(path)}`).then(r=>r.json());
    if (d.error) { g.innerHTML = `<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-text">${d.error}</div></div>`; return; }

    currentPath = d.path;
    parentPath  = d.parent;
    $("fb-path").textContent = d.path;

    g.innerHTML = "";
    d.items.forEach(f => {
      const item = el("div","file-item");
      const ico  = f.is_dir ? "📁" : fileIcon(f.name);
      item.innerHTML = `
        <div class="file-ico">${ico}</div>
        <div class="file-name">${esc(f.name)}</div>
        <div class="file-meta">${f.is_dir ? "Folder" : (f.size_kb+" KB")}</div>`;
      item.onclick = () => f.is_dir ? filesLoad(f.path) : openFilePath(f.path);
      g.appendChild(item);
    });

    if (!d.items.length) g.innerHTML = '<div class="empty"><div class="empty-icon">📂</div><div class="empty-text">Empty folder</div></div>';
  } catch(e) {
    g.innerHTML = `<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-text">${e.message}</div></div>`;
  }
}

function filesUp() { if (parentPath) filesLoad(parentPath); }

async function openFilePath(path) {
  try {
    const r = await fetch("/api/files/open",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({path})});
    const d = await r.json();
    toast(d.reply||"Opened","ok");
  } catch { toast("Could not open file","error"); }
}

function fileIcon(name) {
  const ext = name.split(".").pop().toLowerCase();
  const map = {pdf:"📄",doc:"📝",docx:"📝",txt:"📄",py:"🐍",js:"📜",html:"🌐",
                css:"🎨",png:"🖼️",jpg:"🖼️",jpeg:"🖼️",gif:"🖼️",mp4:"🎬",mp3:"🎵",
                zip:"📦",rar:"📦",exe:"⚙️",json:"{}",csv:"📊",xls:"📊",xlsx:"📊"};
  return map[ext] || "📄";
}

/* ══════════════════════════════════════════════════════════════════════════
   CHAT HISTORY
══════════════════════════════════════════════════════════════════════════ */
let allHistory = [];

async function loadHistory() {
  const c = $("hist-list");
  c.innerHTML = '<div class="spinner"></div>';
  try {
    allHistory = await fetch("/api/history").then(r=>r.json());
    renderHistory(allHistory);
  } catch { c.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-text">Failed to load history</div></div>'; }
}

function renderHistory(items) {
  const c = $("hist-list");
  c.innerHTML = "";
  if (!items.length) {
    c.innerHTML = '<div class="empty"><div class="empty-icon">🕑</div><div class="empty-text">No chat history yet</div></div>';
    return;
  }
  // Show newest first
  [...items].reverse().forEach(h => {
    const d = el("div","hist-item");
    d.innerHTML = `
      <span class="hist-role" style="color:${h.role==='user'?'var(--accent)':'var(--sky)'}">${h.role}</span>
      <span class="hist-content">${esc(h.content)}</span>
      <span class="hist-time">${fmtDate(h.created_at)}</span>`;
    c.appendChild(d);
  });
}

function filterHistory() {
  const q = $("hist-search").value.toLowerCase();
  renderHistory(q ? allHistory.filter(h => h.content.toLowerCase().includes(q)) : allHistory);
}

async function clearHistory() {
  if (!confirm("Delete all chat history? This cannot be undone.")) return;
  await fetch("/api/history",{method:"DELETE"});
  allHistory = [];
  renderHistory([]);
  toast("History cleared");
}

function exportHistory() {
  const lines = [...allHistory].reverse()
    .map(h => `[${h.created_at}] ${h.role.toUpperCase()}: ${h.content}`)
    .join("\n");
  const blob = new Blob([lines], {type:"text/plain"});
  const a    = document.createElement("a");
  a.href     = URL.createObjectURL(blob);
  a.download = `viru-history-${new Date().toISOString().slice(0,10)}.txt`;
  a.click();
  toast("Exported","ok");
}

/* ══════════════════════════════════════════════════════════════════════════
   SCREENSHOTS
══════════════════════════════════════════════════════════════════════════ */
async function loadScreenshots() {
  const g = $("ss-grid");
  g.innerHTML = '<div class="spinner"></div>';
  try {
    const items = await fetch("/api/screenshots").then(r=>r.json());
    g.innerHTML = "";
    if (!items.length) {
      g.innerHTML = '<div class="empty"><div class="empty-icon">🖼️</div><div class="empty-text">No screenshots yet. Say "take screenshot"!</div></div>';
      return;
    }
    items.forEach(s => {
      const item = el("div","ss-item");
      item.innerHTML = `
        <img class="ss-thumb" src="${s.url}" alt="${esc(s.name)}" loading="lazy"/>
        <div class="ss-info">
          <span class="ss-name">${esc(s.name)}</span>
          <span class="ss-size">${s.size_kb} KB</span>
        </div>`;
      item.onclick = () => openLightbox(s.url);
      g.appendChild(item);
    });
  } catch { g.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-text">Failed to load screenshots</div></div>'; }
}

function openLightbox(url) {
  $("lb-img").src = url;
  $("lightbox").classList.add("open");
}
function closeLightbox() { $("lightbox").classList.remove("open"); }

/* ══════════════════════════════════════════════════════════════════════════
   VOICE / MIC
══════════════════════════════════════════════════════════════════════════ */
let recognition = null;
let isRec = false;

function toggleMic() {
  if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
    toast("Web Speech API not supported in this browser. Use Chrome/Edge.","error");
    return;
  }
  if (isRec) { recognition?.stop(); return; }

  const SR  = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.lang = ($("lang-sel")?.value==="hi") ? "hi-IN" : "en-US";
  recognition.interimResults = false;

  recognition.onstart = () => { isRec=true; $("mic-btn").classList.add("rec"); $("mic-btn").textContent="🔴"; };
  recognition.onresult = e => {
    const t = e.results[0][0].transcript.trim();
    if (t) { $("msg-in").value=t; sendMsg(null); }
  };
  recognition.onend = recognition.onerror = () => {
    isRec=false; $("mic-btn").classList.remove("rec"); $("mic-btn").textContent="🎙";
  };
  recognition.start();
}

/* ══════════════════════════════════════════════════════════════════════════
   TTS
══════════════════════════════════════════════════════════════════════════ */
function speakText(text) {
  if (!ttsEnabled || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.voice = selectedVoice;
  u.rate  = 1.05;
  window.speechSynthesis.speak(u);
}

function loadVoices() {
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return;
  selectedVoice = voices.find(v => v.lang.startsWith("en") &&
    (v.name.toLowerCase().includes("female") || v.name.toLowerCase().includes("zira")))
    || voices[0];
}
window.speechSynthesis.onvoiceschanged = loadVoices;
loadVoices();

/* ══════════════════════════════════════════════════════════════════════════
   MODALS
══════════════════════════════════════════════════════════════════════════ */
function openModal(id)  { $(id).classList.add("open"); }
function closeModal(id) { $(id).classList.remove("open"); }

/* ══════════════════════════════════════════════════════════════════════════
   UTILS
══════════════════════════════════════════════════════════════════════════ */
function esc(str) {
  return String(str||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function fmtDate(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-IN",{day:"2-digit",month:"short",hour:"2-digit",minute:"2-digit"});
  } catch { return iso; }
}

// Keyboard shortcuts
document.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    closeLightbox();
    document.querySelectorAll(".modal-backdrop.open").forEach(m => m.classList.remove("open"));
    window.speechSynthesis?.cancel();
  }
  if ((e.ctrlKey || e.metaKey) && e.key === "/") {
    goto("chat");
    setTimeout(() => $("msg-in")?.focus(), 100);
  }
});

// ── Boot: load dashboard immediately ─────────────────────────────────────────
loadDashboard();
