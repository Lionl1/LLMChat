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

const STORAGE_CHAT_KEY = "llmchat.chats";
const STORAGE_CHAT_CURRENT = "llmchat.current";
const STORAGE_SETTINGS = "llmchat.settings";

let config = null;
let settings = null;
let chats = {};
let currentChat = "Default";
let isSending = false;

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
    chat.unshift({ role: "system", content: config.system_message || "" });
  }
}

function createChat(name) {
  const chatName = name || `Chat ${Object.keys(chats).length + 1}`;
  if (chats[chatName]) return;
  chats[chatName] = [{ role: "system", content: config.system_message || "" }];
  currentChat = chatName;
  saveChats();
  render();
}

function deleteChat() {
  if (currentChat === "Default") return;
  delete chats[currentChat];
  currentChat = "Default";
  if (!chats[currentChat]) {
    chats[currentChat] = [{ role: "system", content: config.system_message || "" }];
  }
  saveChats();
  render();
}

function clearChat() {
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
      currentChat = name;
      saveChats();
      render();
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
    textNode.textContent = msg.content;
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
  if (!text || isSending) return;
  messageInput.value = "";
  addMessage("user", text);
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
    addMessage("assistant", `Error: ${err.message}`);
  } finally {
    isSending = false;
    sendBtn.disabled = false;
  }
}

async function handleFiles(files) {
  if (!files || files.length === 0) return;
  addMessage("assistant", "Extracting files...");

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
      addMessage("assistant", "No text extracted.");
      return;
    }
    addMessage("user", `Extracted content:\n\n${payload.text}`);
    showStatus("Files processed successfully.", "success");
  } catch (err) {
    showStatus(err.message, "error");
    addMessage("assistant", `Extraction error: ${err.message}`);
  }
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
}

async function init() {
  const response = await fetch("/api/config");
  config = await response.json();

  settings =
    loadSettings() || {
      api_url: config.api_url || "",
      api_key: "",
      model: config.model || "",
      temperature: config.params.temperature,
      max_tokens: config.params.max_tokens,
      top_p: config.params.top_p,
      extract_api_url: config.extract_api_url || "",
    };

  const storedChats = loadChats();
  if (storedChats) {
    chats = storedChats;
    currentChat = localStorage.getItem(STORAGE_CHAT_CURRENT) || "Default";
  } else {
    chats = {
      Default: [{ role: "system", content: config.system_message || "" }],
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
