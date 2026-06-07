// DOM Elements
const chatListEl = document.getElementById("chatList");
const messagesEl = document.getElementById("messages");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const newChatBtn = document.getElementById("newChatBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const deleteChatBtn = document.getElementById("deleteChatBtn");
const settingsBtn = document.getElementById("settingsBtn");
const settingsDrawer = document.getElementById("settingsDrawer");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const drawerBackdrop = document.getElementById("drawerBackdrop");
const addFilesBtn = document.getElementById("addFilesBtn");
const fileInput = document.getElementById("fileInput");
const statusMessage = document.getElementById("statusMessage");

const apiUrlInput = document.getElementById("apiUrlInput");
const apiKeyInput = document.getElementById("apiKeyInput");
const modelInput = document.getElementById("modelInput");
const temperatureInput = document.getElementById("temperatureInput");
const temperatureValue = document.getElementById("temperatureValue");
const maxTokensInput = document.getElementById("maxTokensInput");
const topPInput = document.getElementById("topPInput");
const topPValue = document.getElementById("topPValue");
const extractUrlInput = document.getElementById("extractUrlInput");

// New Settings elements
const languageSelect = document.getElementById("languageSelect");
const systemPromptInput = document.getElementById("systemPromptInput");
const resetSettingsBtn = document.getElementById("resetSettingsBtn");

// Confirmation Modal elements
const confirmModal = document.getElementById("confirmModal");
const confirmTitle = document.getElementById("confirmTitle");
const confirmBody = document.getElementById("confirmBody");
const confirmCancelBtn = document.getElementById("confirmCancelBtn");
const confirmOkBtn = document.getElementById("confirmOkBtn");

const STORAGE_CHAT_KEY = "llmchat.chats";
const STORAGE_CHAT_CURRENT = "llmchat.current";
const STORAGE_SETTINGS = "llmchat.settings";

// Configure Marked.js renderer with custom code styling and escape helper
const renderer = new marked.Renderer();
renderer.code = function({ text, lang }) {
  const language = lang || "plaintext";
  let highlighted;
  try {
    highlighted = hljs.highlight(text, { language: hljs.getLanguage(language) ? language : 'plaintext' }).value;
  } catch {
    highlighted = text;
  }
  
  // Clean text for copy operation
  const escapedText = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
    
  return `
    <div class="code-block-wrapper">
      <div class="code-block-header">
        <span>${language}</span>
        <button class="code-block-copy-btn" type="button" onclick="copyCodeBlock(this, \`${escapedText}\`)">Copy</button>
      </div>
      <pre><code class="hljs language-${language}">${highlighted}</code></pre>
    </div>
  `;
};
marked.use({ renderer });

// Global helper for code block copying
window.copyCodeBlock = function(btn, text) {
  const textarea = document.createElement("textarea");
  textarea.innerHTML = text;
  const decodedText = textarea.value;

  navigator.clipboard.writeText(decodedText).then(() => {
    const originalText = btn.textContent;
    btn.textContent = "Copied!";
    btn.style.color = "var(--accent)";
    setTimeout(() => {
      btn.textContent = originalText;
      btn.style.color = "";
    }, 1500);
  }).catch(() => {
    btn.textContent = "Error";
  });
};

// Collapsible attachments toggle
window.toggleRawAttachments = function(badge) {
  const contentEl = badge.nextElementSibling;
  if (contentEl.style.display === "none") {
    contentEl.style.display = "block";
    badge.textContent = badge.textContent.replace("click to view raw text", "click to hide");
  } else {
    contentEl.style.display = "none";
    badge.textContent = badge.textContent.replace("click to hide", "click to view raw text");
  }
};

// Fallback config configuration (Preventions race condition)
let config = {
  api_url: "http://localhost:8000/v1/chat/completions",
  model: "local-model",
  extract_api_url: "http://localhost:7555",
  system_message: "You are a helpful AI assistant.",
  system_messages: {
    en: "You are a helpful AI assistant.",
    ru: "Я - полезный ИИ-ассистент. Я говорю по-русски и стараюсь помогать людям."
  },
  params: {
    temperature: 0.1,
    max_tokens: 2048,
    top_p: 0.9,
  }
};

let settings = null;
let chats = {};
let currentChat = "Default";
let isSending = false;
let pendingAttachments = [];

// Custom Confirm modal promise handler
let confirmPromise = null;
function askConfirm(title, message) {
  confirmTitle.textContent = title;
  confirmBody.textContent = message;
  confirmModal.classList.add("open");
  return new Promise((resolve) => {
    confirmPromise = resolve;
  });
}

function closeConfirm(value) {
  confirmModal.classList.remove("open");
  if (confirmPromise) {
    confirmPromise(value);
    confirmPromise = null;
  }
}

confirmCancelBtn.addEventListener("click", () => closeConfirm(false));
confirmOkBtn.addEventListener("click", () => closeConfirm(true));

function loadSettings() {
  const raw = localStorage.getItem(STORAGE_SETTINGS);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveSettings() {
  localStorage.setItem(STORAGE_SETTINGS, JSON.stringify(settings));
}

function loadChats() {
  const raw = localStorage.getItem(STORAGE_CHAT_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveChats() {
  localStorage.setItem(STORAGE_CHAT_KEY, JSON.stringify(chats));
  localStorage.setItem(STORAGE_CHAT_CURRENT, currentChat);
}

function ensureSystemMessage(chat) {
  if (!chat.some((msg) => msg.role === "system")) {
    const defaultSys = settings && settings.system_prompt 
      ? settings.system_prompt 
      : (config.system_messages[settings?.language || "en"] || config.system_message);
    chat.unshift({ role: "system", content: defaultSys });
  }
}

function createChat(name) {
  const chatName = name || `Chat ${Object.keys(chats).length + 1}`;
  if (chats[chatName]) return;
  const defaultSys = settings && settings.system_prompt 
    ? settings.system_prompt 
    : (config.system_messages[settings?.language || "en"] || config.system_message);
  chats[chatName] = [{ role: "system", content: defaultSys }];
  currentChat = chatName;
  saveChats();
  render();
}

async function deleteChat() {
  if (currentChat === "Default") return;
  const ok = await askConfirm("Delete Chat", `Are you sure you want to delete "${currentChat}"? This action cannot be undone.`);
  if (!ok) return;

  delete chats[currentChat];
  currentChat = "Default";
  if (!chats[currentChat]) {
    const defaultSys = settings && settings.system_prompt 
      ? settings.system_prompt 
      : (config.system_messages[settings?.language || "en"] || config.system_message);
    chats[currentChat] = [{ role: "system", content: defaultSys }];
  }
  saveChats();
  render();
}

async function clearChat() {
  const ok = await askConfirm("Clear Chat", `Are you sure you want to clear all messages in "${currentChat}"?`);
  if (!ok) return;

  const system = chats[currentChat].find((msg) => msg.role === "system");
  chats[currentChat] = system ? [system] : [];
  ensureSystemMessage(chats[currentChat]);
  saveChats();
  renderMessages();
}

function addMessage(role, content) {
  chats[currentChat].push({ role, content });
  saveChats();
  renderMessages();
}

function renderChatList() {
  chatListEl.innerHTML = "";
  Object.keys(chats).forEach((name) => {
    const item = document.createElement("div");
    item.className = `chat-item${name === currentChat ? " active" : ""}`;
    item.textContent = name;
    
    item.addEventListener("click", () => {
      if (item.contentEditable === "true") return;
      currentChat = name;
      saveChats();
      render();
    });

    // Inline rename chat on double click
    item.addEventListener("dblclick", () => {
      item.contentEditable = true;
      item.focus();
      const range = document.createRange();
      range.selectNodeContents(item);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    });

    const saveRename = () => {
      item.contentEditable = false;
      const newName = item.textContent.trim();
      if (!newName || newName === name) {
        item.textContent = name;
        return;
      }
      if (chats[newName]) {
        showStatus("A chat with this name already exists", "error");
        item.textContent = name;
        return;
      }
      chats[newName] = chats[name];
      delete chats[name];
      if (currentChat === name) {
        currentChat = newName;
      }
      saveChats();
      render();
    };

    item.addEventListener("blur", saveRename);
    item.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        saveRename();
      } else if (e.key === "Escape") {
        e.preventDefault();
        item.textContent = name;
        item.contentEditable = false;
      }
    });

    chatListEl.appendChild(item);
  });
}

function renderMessages() {
  messagesEl.innerHTML = "";
  chats[currentChat].forEach((msg) => {
    if (msg.role === "system") return;
    const el = document.createElement("div");
    el.className = `message ${msg.role}`;
    
    const textNode = document.createElement("div");
    textNode.className = "message-text";

    let contentToRender = msg.content;
    let attachmentsHtml = "";

    // Parse files preview if present
    if (msg.role === "user" && msg.content.includes("File: ")) {
      const parts = msg.content.split("\n\nUser Question: ");
      if (parts.length === 2) {
        const filesPart = parts[0];
        const questionPart = parts[1];
        contentToRender = questionPart;

        const fileMatches = [...filesPart.matchAll(/File: ([^\n]+)/g)].map(m => m[1]);
        attachmentsHtml = `
          <div class="msg-attachments-badge" onclick="toggleRawAttachments(this)">📁 Attached: ${fileMatches.join(", ")} (click to view raw text)</div>
          <div class="msg-attachments-content" style="display: none;"><pre>${filesPart}</pre></div>
        `;
      }
    }

    textNode.innerHTML = marked.parse(contentToRender);
    if (attachmentsHtml) {
      textNode.insertAdjacentHTML("afterbegin", attachmentsHtml);
    }
    
    el.appendChild(textNode);
    
    const copyBtn = document.createElement("button");
    copyBtn.className = "copy-btn";
    copyBtn.type = "button";
    copyBtn.textContent = "Copy";
    copyBtn.addEventListener("click", () => {
      navigator.clipboard
        .writeText(msg.content)
        .then(() => showStatus("Text copied to clipboard", "success"))
        .catch(() => showStatus("Unable to copy text", "error"));
    });
    el.appendChild(copyBtn);
    messagesEl.appendChild(el);
  });
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function render() {
  renderChatList();
  renderMessages();
}

async function sendMessage() {
  const text = messageInput.value.trim();
  if ((!text && pendingAttachments.length === 0) || isSending) return;
  
  let fullText = text;
  if (pendingAttachments.length > 0) {
    const attachedTexts = pendingAttachments.map(att => `File: ${att.filename}\n${att.text}`).join("\n\n");
    fullText = `${attachedTexts}\n\nUser Question: ${text || "(analyzing attached files)"}`;
    pendingAttachments = [];
    renderAttachments();
  }

  messageInput.value = "";
  addMessage("user", fullText);
  isSending = true;
  sendBtn.disabled = true;

  ensureSystemMessage(chats[currentChat]);
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: chats[currentChat],
        api_url: settings.api_url,
        api_key: settings.api_key || null,
        model: settings.model,
        params: {
          temperature: settings.temperature,
          max_tokens: settings.max_tokens,
          top_p: settings.top_p,
        },
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Request failed");
    }

    const payload = await response.json();
    addMessage("assistant", payload.message);
  } catch (err) {
    showStatus(`Error: ${err.message}`, "error");
    // Show temporary inline error inside bubbles container without polluting chats array
    const errEl = document.createElement("div");
    errEl.className = "message assistant error-message";
    errEl.style.borderLeft = "4px solid var(--danger)";
    errEl.style.background = "rgba(255, 92, 92, 0.08)";
    errEl.innerHTML = `<div class="message-text">⚠️ <strong>Error contacting API:</strong> ${err.message}</div>`;
    messagesEl.appendChild(errEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  } finally {
    isSending = false;
    sendBtn.disabled = false;
  }
}

async function handleFiles(files) {
  if (!files || files.length === 0) return;
  showStatus("Extracting files content...", "success");

  const data = new FormData();
  Array.from(files).forEach((file) => data.append("files", file, file.name));
  data.append("extract_api_url", settings.extract_api_url || "");

  try {
    const response = await fetch("/api/extract", { method: "POST", body: data });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Extraction failed");
    }
    const payload = await response.json();
    if (!payload.text) {
      showStatus("No text extracted from files.", "error");
      return;
    }
    
    // Distribute text segments or store
    Array.from(files).forEach((file, idx) => {
      const fileData = payload.files ? payload.files[idx] : null;
      const text = fileData ? fileData.text : payload.text;
      pendingAttachments.push({
        filename: file.name,
        text: text || ""
      });
    });

    renderAttachments();
    showStatus("Files processed and attached successfully.", "success");
  } catch (err) {
    showStatus(`Extraction error: ${err.message}`, "error");
  }
}

function renderAttachments() {
  const listEl = document.getElementById("attachmentsList");
  listEl.innerHTML = "";
  if (pendingAttachments.length === 0) {
    listEl.style.display = "none";
    return;
  }
  listEl.style.display = "flex";
  pendingAttachments.forEach((att, idx) => {
    const pill = document.createElement("div");
    pill.className = "attachment-pill";
    pill.textContent = att.filename;

    const remove = document.createElement("button");
    remove.className = "remove-btn";
    remove.innerHTML = "&times;";
    remove.type = "button";
    remove.addEventListener("click", () => {
      pendingAttachments.splice(idx, 1);
      renderAttachments();
    });
    pill.appendChild(remove);
    listEl.appendChild(pill);
  });
}

function showStatus(message, type = "success") {
  if (!statusMessage) return;
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
  clearTimeout(statusMessage._timer);
  statusMessage._timer = setTimeout(() => {
    statusMessage.textContent = "";
    statusMessage.className = "status-message";
  }, 5000);
}

function openSettings() {
  settingsDrawer.classList.add("open");
  drawerBackdrop.classList.add("open");
}

function closeSettings() {
  settingsDrawer.classList.remove("open");
  drawerBackdrop.classList.remove("open");
}

function bindSettings() {
  apiUrlInput.value = settings.api_url || "";
  apiKeyInput.value = settings.api_key || "";
  modelInput.value = settings.model || "";
  temperatureInput.value = settings.temperature;
  temperatureValue.textContent = settings.temperature.toFixed(2);
  maxTokensInput.value = settings.max_tokens;
  topPInput.value = settings.top_p;
  topPValue.textContent = settings.top_p.toFixed(2);
  extractUrlInput.value = settings.extract_api_url || "";
  
  // Set language selector
  languageSelect.value = settings.language || "en";

  // Set system prompt text area value
  const defaultSys = config.system_messages ? (config.system_messages[settings.language || "en"] || config.system_message) : config.system_message;
  systemPromptInput.value = settings.system_prompt !== undefined ? settings.system_prompt : defaultSys;

  apiUrlInput.addEventListener("input", () => {
    settings.api_url = apiUrlInput.value.trim();
    saveSettings();
  });
  apiKeyInput.addEventListener("input", () => {
    settings.api_key = apiKeyInput.value.trim();
    saveSettings();
  });
  modelInput.addEventListener("input", () => {
    settings.model = modelInput.value.trim();
    saveSettings();
  });
  temperatureInput.addEventListener("input", () => {
    settings.temperature = Number(temperatureInput.value);
    temperatureValue.textContent = settings.temperature.toFixed(2);
    saveSettings();
  });
  maxTokensInput.addEventListener("input", () => {
    settings.max_tokens = Number(maxTokensInput.value);
    saveSettings();
  });
  topPInput.addEventListener("input", () => {
    settings.top_p = Number(topPInput.value);
    topPValue.textContent = settings.top_p.toFixed(2);
    saveSettings();
  });
  extractUrlInput.addEventListener("input", () => {
    settings.extract_api_url = extractUrlInput.value.trim();
    saveSettings();
  });

  languageSelect.addEventListener("change", () => {
    const oldLang = settings.language || "en";
    const newLang = languageSelect.value;
    settings.language = newLang;

    // Toggle system message if not manually modified
    const oldDefault = config.system_messages ? (config.system_messages[oldLang] || config.system_message) : config.system_message;
    if (!settings.system_prompt || settings.system_prompt.trim() === oldDefault.trim()) {
      const newDefault = config.system_messages ? (config.system_messages[newLang] || config.system_message) : config.system_message;
      settings.system_prompt = newDefault;
      systemPromptInput.value = newDefault;
    }
    saveSettings();
  });

  systemPromptInput.addEventListener("input", () => {
    settings.system_prompt = systemPromptInput.value;
    saveSettings();
  });

  resetSettingsBtn.addEventListener("click", async () => {
    const ok = await askConfirm("Reset Settings", "Are you sure you want to reset all settings to defaults?");
    if (!ok) return;

    settings = {
      api_url: config.api_url || "",
      api_key: "",
      model: config.model || "",
      temperature: config.params.temperature,
      max_tokens: config.params.max_tokens,
      top_p: config.params.top_p,
      extract_api_url: config.extract_api_url || "",
      language: "en",
      system_prompt: config.system_messages ? config.system_messages["en"] : config.system_message
    };
    saveSettings();
    bindSettings();
    showStatus("Settings reset to defaults.", "success");
  });
}

async function init() {
  try {
    const response = await fetch("/api/config");
    if (response.ok) {
      config = await response.json();
    }
  } catch (err) {
    console.warn("Could not load server config, using hardcoded fallbacks", err);
  }

  settings =
    loadSettings() || {
      api_url: config.api_url || "",
      api_key: "",
      model: config.model || "",
      temperature: config.params.temperature,
      max_tokens: config.params.max_tokens,
      top_p: config.params.top_p,
      extract_api_url: config.extract_api_url || "",
      language: "en",
      system_prompt: config.system_messages ? config.system_messages["en"] : config.system_message
    };

  const storedChats = loadChats();
  if (storedChats) {
    chats = storedChats;
    currentChat = localStorage.getItem(STORAGE_CHAT_CURRENT) || "Default";
  } else {
    const defaultSys = settings.system_prompt || (config.system_messages ? config.system_messages["en"] : config.system_message);
    chats = {
      Default: [{ role: "system", content: defaultSys }],
    };
    currentChat = "Default";
  }

  bindSettings();
  render();
}

sendBtn.addEventListener("click", sendMessage);
messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});
newChatBtn.addEventListener("click", () => createChat());
clearChatBtn.addEventListener("click", clearChat);
deleteChatBtn.addEventListener("click", deleteChat);
settingsBtn.addEventListener("click", openSettings);
closeSettingsBtn.addEventListener("click", closeSettings);
drawerBackdrop.addEventListener("click", closeSettings);
addFilesBtn.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (event) => {
  handleFiles(event.target.files);
  fileInput.value = "";
});

init();

