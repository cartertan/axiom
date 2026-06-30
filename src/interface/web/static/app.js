const chat = document.getElementById("chat");
const emptyState = document.getElementById("empty-state");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const uploadBtn = document.getElementById("upload-btn");
const fileInput = document.getElementById("file-input");
const typingIndicator = document.getElementById("typing-indicator");
const modeSelect = document.getElementById("mode-select");
const micBtn = document.getElementById("mic-btn");
const councilControls = document.getElementById("council-controls");
const quickCouncil = document.getElementById("quick-council");
const saveVaultCheck = document.getElementById("save-vault");

// ── helpers ──────────────────────────────────────────────────────────────────

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function removeEmptyState() {
  if (emptyState && emptyState.parentNode) emptyState.remove();
}

// ── row renderers ─────────────────────────────────────────────────────────────

function addUserRow(text) {
  removeEmptyState();
  const row = document.createElement("div");
  row.className = "row user";
  row.innerHTML = `<div class="bubble"></div>`;
  row.querySelector(".bubble").textContent = text;
  chat.appendChild(row);
  scrollToBottom();
}

function addAxiomRow({ response, task_type, model, latency, isError, individual_responses, stages, round1 }) {
  const row = document.createElement("div");
  row.className = "row axiom";

  const badgeRow = document.createElement("div");
  badgeRow.className = "badge-row";

  if (!isError) {
    const badge = document.createElement("span");
    badge.className = `badge ${(task_type || "general").toLowerCase()}`;
    badge.textContent = task_type;
    badgeRow.appendChild(badge);

    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = `${model} · ${latency}s`;
    badgeRow.appendChild(meta);
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble" + (isError ? " error-text" : "");
  bubble.textContent = response;

  row.appendChild(badgeRow);
  row.appendChild(bubble);

  const details = individual_responses || stages || round1;
  if (details && details.length > 0) {
    const disclosure = document.createElement("details");
    disclosure.className = "model-details";
    const summary = document.createElement("summary");
    summary.textContent = `Show individual model responses (${details.length})`;
    disclosure.appendChild(summary);

    details.forEach((item) => {
      const label = item.model || `${item.stage} / ${item.model}`;
      const text = item.response || "";
      const div = document.createElement("div");
      div.className = "model-response";
      div.innerHTML = `<strong>${label}</strong><p>${text.slice(0, 800)}${text.length > 800 ? "…" : ""}</p>`;
      disclosure.appendChild(div);
    });

    row.appendChild(disclosure);
  }

  chat.appendChild(row);
  scrollToBottom();
}

function addCouncilRow({ question, roles, reviewer, vault_path, duration_seconds }) {
  removeEmptyState();
  const row = document.createElement("div");
  row.className = "row axiom";

  // Badge + meta
  const badgeRow = document.createElement("div");
  badgeRow.className = "badge-row";

  const badge = document.createElement("span");
  badge.className = "badge council";
  badge.textContent = "COUNCIL";
  badgeRow.appendChild(badge);

  const modelNames = [...new Set((roles || []).map((r) => r.model))].join(", ");
  const meta = document.createElement("span");
  meta.className = "meta";
  meta.textContent = `${modelNames} · ${duration_seconds}s`;
  badgeRow.appendChild(meta);

  // Final reviewer answer
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = reviewer || "(no reviewer output)";

  row.appendChild(badgeRow);
  row.appendChild(bubble);

  // Vault badge
  if (vault_path) {
    const vaultBadge = document.createElement("div");
    vaultBadge.className = "vault-badge";
    vaultBadge.textContent = "Saved to Vault";
    row.appendChild(vaultBadge);
  }

  // Deliberation thread
  if (roles && roles.length > 0) {
    const disclosure = document.createElement("details");
    disclosure.className = "model-details";
    const summary = document.createElement("summary");
    summary.textContent = `Show deliberation (${roles.length} agents)`;
    disclosure.appendChild(summary);

    roles.forEach((r) => {
      const slug = r.role.toLowerCase().replace(/[^a-z]/g, "-");
      const card = document.createElement("div");
      card.className = `council-card role-${slug}`;
      const whereRun = r.where_run || "local";
      const preview = (r.content || "").slice(0, 600);
      const truncated = (r.content || "").length > 600;
      card.innerHTML =
        `<div class="role-label">` +
        `<strong>${r.role}</strong>` +
        `<span class="meta">${r.model}</span>` +
        `<span class="where-pill">${whereRun}</span>` +
        `</div>` +
        `<p>${preview}${truncated ? "…" : ""}</p>`;
      disclosure.appendChild(card);
    });

    row.appendChild(disclosure);
  }

  chat.appendChild(row);
  scrollToBottom();
}

// ── send ──────────────────────────────────────────────────────────────────────

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text) return;

  addUserRow(text);
  messageInput.value = "";
  messageInput.style.height = "auto";
  sendBtn.disabled = true;
  typingIndicator.classList.remove("hidden");

  const mode = modeSelect ? modeSelect.value : "single";

  try {
    if (mode === "council") {
      const quick = quickCouncil ? quickCouncil.checked : false;
      const saveVault = saveVaultCheck ? saveVaultCheck.checked : false;

      const res = await fetch("/council", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, quick, save_vault: saveVault, force_complex: false }),
      });
      const data = await res.json();

      if (!res.ok) {
        addAxiomRow({ response: data.error || "Council deliberation failed.", isError: true });
      } else {
        addCouncilRow(data);
      }
    } else {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, mode }),
      });
      const data = await res.json();

      if (!res.ok) {
        addAxiomRow({ response: data.error || "Something went wrong.", isError: true });
      } else {
        addAxiomRow(data);
      }
    }
  } catch (err) {
    addAxiomRow({ response: "Could not reach AXIOM. Is the server running?", isError: true });
  } finally {
    typingIndicator.classList.add("hidden");
    sendBtn.disabled = false;
    messageInput.focus();
  }
}

// ── events ────────────────────────────────────────────────────────────────────

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

messageInput.addEventListener("input", () => {
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 160) + "px";
});

modeSelect.addEventListener("change", () => {
  if (modeSelect.value === "council") {
    councilControls.classList.remove("hidden");
  } else {
    councilControls.classList.add("hidden");
  }
});

// ── PDF upload ────────────────────────────────────────────────────────────────

uploadBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  uploadBtn.disabled = true;
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      addAxiomRow({ response: data.error || "Could not extract PDF text.", isError: true });
    } else {
      const prefix = messageInput.value ? messageInput.value + "\n\n" : "";
      messageInput.value = prefix + data.text;
      messageInput.dispatchEvent(new Event("input"));
      messageInput.focus();
    }
  } catch (err) {
    addAxiomRow({ response: "Upload failed. Is the server running?", isError: true });
  } finally {
    uploadBtn.disabled = false;
    fileInput.value = "";
  }
});

// ── mic / voice transcription ─────────────────────────────────────────────────

let mediaRecorder = null;
let audioChunks = [];

micBtn.addEventListener("click", async () => {
  // Stop if already recording
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      micBtn.classList.remove("recording");
      micBtn.disabled = true;

      const mimeType = audioChunks[0]?.type || "audio/webm";
      const ext = mimeType.includes("ogg") ? ".ogg" : ".webm";
      const blob = new Blob(audioChunks, { type: mimeType });
      const formData = new FormData();
      formData.append("file", blob, `recording${ext}`);

      try {
        const res = await fetch("/voice/transcribe", { method: "POST", body: formData });
        const data = await res.json();

        if (res.ok && data.text) {
          const prefix = messageInput.value ? messageInput.value + " " : "";
          messageInput.value = prefix + data.text;
          messageInput.dispatchEvent(new Event("input"));
          messageInput.focus();
        } else {
          addAxiomRow({ response: data.error || "Transcription returned no text.", isError: true });
        }
      } catch (err) {
        addAxiomRow({ response: "Voice transcription failed. Is the server running?", isError: true });
      } finally {
        micBtn.disabled = false;
      }
    };

    mediaRecorder.start();
    micBtn.classList.add("recording");
  } catch (err) {
    addAxiomRow({ response: "Microphone access denied or unavailable.", isError: true });
  }
});
