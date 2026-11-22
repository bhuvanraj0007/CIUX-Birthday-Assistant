/**
 * CIUX Birthday Assistant V3 - Frontend Chat Controller
 * Manages chat interactions, asynchronous Flask communication, loading states,
 * UI updates, debug information rendering, and conversation resets.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Core DOM Elements
  const chatMessages = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const btnSend = document.getElementById("btn-send");
  const btnReset = document.getElementById("btn-reset");
  const loadingIndicator = document.getElementById("loading-indicator");
  const suggestedQuestions = document.getElementById("suggested-questions");

  // Debug Panel Elements
  const debugPanel = document.getElementById("debug-panel");
  const btnToggleDebug = document.getElementById("btn-toggle-debug");
  const btnCloseDebug = document.getElementById("btn-close-debug");
  const debugIntent = document.getElementById("debug-intent");
  const debugEntities = document.getElementById("debug-entities");
  const debugState = document.getElementById("debug-state");

  let isSending = false;

  // ------------------------------------------------------------------------
  // Safe Markdown-to-HTML Formatter
  // ------------------------------------------------------------------------
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function formatMarkdown(markdown) {
    if (!markdown) return "";
    let safe = escapeHtml(markdown);

    // Headers: ### Header
    safe = safe.replace(/^### (.*$)/gim, "<h3>$1</h3>");

    // Bold: **text**
    safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Italic: *text*
    safe = safe.replace(/\*(.*?)\*/g, "<em>$1</em>");

    // Inline Code: `code`
    safe = safe.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Bullet points: - item or * item
    safe = safe.replace(/^\s*[-*]\s+(.*$)/gim, "<li>$1</li>");

    // Numbered lists: 1. item
    safe = safe.replace(/^\s*\d+\.\s+(.*$)/gim, "<li>$1</li>");

    // Wrap consecutive list items in <ul>
    safe = safe.replace(/(<li>[\s\S]*?<\/li>)/gm, "<ul>$1</ul>");
    safe = safe.replace(/<\/ul>\s*<ul>/g, "");

    // Split paragraphs
    const paragraphs = safe.split(/\n{2,}/).map(p => {
      p = p.trim();
      if (!p) return "";
      if (p.startsWith("<h3>") || p.startsWith("<ul>")) return p;
      return `<p>${p.replace(/\n/g, "<br>")}</p>`;
    });

    return paragraphs.join("");
  }

  // ------------------------------------------------------------------------
  // UI Helpers
  // ------------------------------------------------------------------------
  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendMessage(sender, text) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}-message animate-fade-in`;

    const avatarSvg = sender === "user"
      ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`
      : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="M20 12h2"></path><path d="m19.07 4.93-1.41 1.41"></path><path d="M15.34 18a3.5 3.5 0 0 0 2.66-3.5 4 4 0 0 0-4-4 4 4 0 0 0-4 4 3.5 3.5 0 0 0 2.66 3.5"></path><path d="M8 18v2a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2"></path></svg>`;

    const senderLabel = sender === "user" ? "You" : "Birthday Assistant V3";
    const bodyContent = formatMarkdown(text);

    messageDiv.innerHTML = `
      <div class="message-avatar">
        ${avatarSvg}
      </div>
      <div class="message-bubble">
        <div class="message-header">
          <span class="sender-name">${senderLabel}</span>
        </div>
        <div class="message-body">
          ${bodyContent}
        </div>
      </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
  }

  function setLoading(loading) {
    isSending = loading;
    loadingIndicator.style.display = loading ? "block" : "none";
    btnSend.disabled = loading;
    userInput.disabled = loading;
    if (loading) {
      scrollToBottom();
    } else {
      userInput.focus();
    }
  }

  function updateDebugPanel(debugData, stateData) {
    if (debugIntent && debugData) {
      debugIntent.textContent = debugData.intent || "unknown";
    }

    if (debugEntities && debugData) {
      debugEntities.textContent = JSON.stringify(debugData.entities || {}, null, 2);
    }

    if (debugState && stateData) {
      debugState.textContent = JSON.stringify(stateData || {}, null, 2);
    }
  }

  // ------------------------------------------------------------------------
  // Chat Messaging (POST /chat)
  // ------------------------------------------------------------------------
  async function sendMessage(messageText) {
    const text = (messageText || userInput.value).trim();
    if (!text || isSending) return;

    // Display user message in chat
    appendMessage("user", text);
    userInput.value = "";
    setLoading(true);

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: text }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Server responded with status ${response.status}`);
      }

      // Display assistant response
      appendMessage("assistant", data.answer || "No response received.");

      // Update Debug Panel with intent, entities, and conversation state
      updateDebugPanel(data.debug, data.state);
    } catch (err) {
      console.error("Communication error:", err);
      appendMessage(
        "assistant",
        `⚠️ **Error:** Unable to process request. ${err.message || "Please check network or backend logs."}`
      );
    } finally {
      setLoading(false);
    }
  }

  // ------------------------------------------------------------------------
  // Reset Conversation (POST /reset)
  // ------------------------------------------------------------------------
  async function resetConversation() {
    if (isSending) return;

    if (!confirm("Are you sure you want to reset the conversation memory?")) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      const data = await response.json();
      if (response.ok) {
        appendMessage("assistant", "🔄 *Conversation context and session memory have been reset.*");
        updateDebugPanel(
          { intent: "reset", entities: {} },
          { status: "reset", previous_results_count: 0 }
        );
      } else {
        alert(data.error || "Failed to reset session.");
      }
    } catch (err) {
      console.error("Reset error:", err);
      alert("Failed to reach server to reset conversation.");
    } finally {
      setLoading(false);
    }
  }

  // ------------------------------------------------------------------------
  // Event Listeners
  // ------------------------------------------------------------------------
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage();
  });

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  btnReset.addEventListener("click", () => {
    resetConversation();
  });

  // Suggested Questions Click Handler
  if (suggestedQuestions) {
    suggestedQuestions.addEventListener("click", (e) => {
      const chip = e.target.closest(".question-chip");
      if (chip && chip.dataset.question) {
        sendMessage(chip.dataset.question);
      }
    });
  }

  // Debug Panel Toggles
  if (btnToggleDebug && debugPanel) {
    btnToggleDebug.addEventListener("click", () => {
      debugPanel.classList.toggle("collapsed");
    });
  }

  if (btnCloseDebug && debugPanel) {
    btnCloseDebug.addEventListener("click", () => {
      debugPanel.classList.add("collapsed");
    });
  }

  // Initial focus
  userInput.focus();
});
