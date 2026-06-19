const chat = document.getElementById("chat");
const emptyState = document.getElementById("empty-state");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const uploadBtn = document.getElementById("upload-btn");
const fileInput = document.getElementById("file-input");
const typingIndicator = document.getElementById("typing-indicator");
const modeSelect = document.getElementById("mode-select");

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function addUserRow(text) {
  if (emptyState && emptyState.parentNode) emptyState.remove();
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

  // Expandable individual model responses for multi-model modes
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
  } catch (err) {
    addAxiomRow({ response: "Could not reach AXIOM. Is the server running?", isError: true });
  } finally {
    typingIndicator.classList.add("hidden");
    sendBtn.disabled = false;
    messageInput.focus();
  }
}

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
