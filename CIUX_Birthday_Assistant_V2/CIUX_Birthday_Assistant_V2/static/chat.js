/**
 * chat.js - Frontend Controller for CIUX Birthday Assistant V2.
 * Communicates with Flask backend on Port 5002 via /chat endpoint.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const chatMessages = document.getElementById("chat-messages");
    const resetChatBtn = document.getElementById("reset-chat-btn");
    const toggleDebugBtn = document.getElementById("toggle-debug-btn");
    const closeDebugBtn = document.getElementById("close-debug-btn");
    const debugPanel = document.getElementById("debug-panel");
    const suggestedChips = document.querySelectorAll(".suggested-prompts .chip");

    // Debug Panel DOM Elements
    const debugIntent = document.getElementById("debug-intent");
    const entityPersonName = document.getElementById("entity-person-name");
    const entityPersonId = document.getElementById("entity-person-id");
    const entityMonth = document.getElementById("entity-month");
    const entityRelationship = document.getElementById("entity-relationship");
    const entityRelativeDate = document.getElementById("entity-relative-date");
    const debugRawJson = document.getElementById("debug-raw-json");

    let isRequestPending = false;

    // Initial greeting template
    const initialWelcomeHTML = `
        <div class="message-wrapper assistant">
            <div class="avatar assistant-avatar">🎂</div>
            <div class="message-bubble assistant-bubble">
                <div class="message-text">
                    Hello! I am your <strong>CIUX Birthday Assistant V2</strong>. Ask me anything about birthdays from the dataset:
                    <ul>
                        <li>Show birthdays by month or relationship</li>
                        <li>Check when someone was born or where they live</li>
                        <li>View upcoming or tomorrow's birthdays</li>
                        <li>Count birthdays across categories</li>
                    </ul>
                    Click any suggested prompt below or type your own question!
                </div>
                <span class="message-time">${getCurrentTime()}</span>
            </div>
        </div>
    `;

    /**
     * Get formatted local time (e.g. "5:15 PM")
     */
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    /**
     * Escape raw text to prevent XSS attacks
     */
    function escapeHTML(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    /**
     * Format assistant markdown text (bold, lists, emojis, linebreaks)
     */
    function formatAssistantResponse(rawText) {
        if (!rawText) return "";

        // Escape dangerous HTML first
        let safe = escapeHTML(rawText);

        // Convert markdown bold **text** to <strong>text</strong>
        safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

        // Convert markdown italics *text* to <em>text</em>
        safe = safe.replace(/\*(.*?)\*/g, "<em>$1</em>");

        // Process line by line for bullet points
        const lines = safe.split("\n");
        let htmlOut = "";
        let inList = false;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();

            if (line.startsWith("- ") || line.startsWith("* ")) {
                if (!inList) {
                    htmlOut += "<ul>";
                    inList = true;
                }
                htmlOut += `<li>${line.substring(2)}</li>`;
            } else {
                if (inList) {
                    htmlOut += "</ul>";
                    inList = false;
                }
                if (line) {
                    htmlOut += `<p>${line}</p>`;
                }
            }
        }

        if (inList) {
            htmlOut += "</ul>";
        }

        return htmlOut;
    }

    /**
     * Append a message bubble to the chat container
     */
    function appendMessage(text, sender = "user") {
        const wrapper = document.createElement("div");
        wrapper.className = `message-wrapper ${sender}`;

        const avatar = document.createElement("div");
        avatar.className = `avatar ${sender}-avatar`;
        avatar.textContent = sender === "user" ? "You" : "🎂";

        const bubble = document.createElement("div");
        bubble.className = `message-bubble ${sender}-bubble`;

        const content = document.createElement("div");
        content.className = "message-text";

        if (sender === "user") {
            content.textContent = text;
        } else {
            content.innerHTML = formatAssistantResponse(text);
        }

        const timeSpan = document.createElement("span");
        timeSpan.className = "message-time";
        timeSpan.textContent = getCurrentTime();

        bubble.appendChild(content);
        bubble.appendChild(timeSpan);

        wrapper.appendChild(avatar);
        wrapper.appendChild(bubble);

        chatMessages.appendChild(wrapper);
        scrollToBottom();

        return wrapper;
    }

    /**
     * Show loading/typing indicator bubble
     */
    function showTypingIndicator() {
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper assistant";
        wrapper.id = "typing-indicator-wrapper";

        wrapper.innerHTML = `
            <div class="avatar assistant-avatar">🎂</div>
            <div class="message-bubble assistant-bubble">
                <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
        `;

        chatMessages.appendChild(wrapper);
        scrollToBottom();
    }

    /**
     * Remove loading/typing indicator bubble
     */
    function removeTypingIndicator() {
        const indicator = document.getElementById("typing-indicator-wrapper");
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Scroll the message log to bottom
     */
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /**
     * Update NLU Debug Panel
     */
    function updateDebugPanel(debugData) {
        if (!debugData) return;

        debugIntent.textContent = debugData.intent || "unknown";

        const entities = debugData.entities || {};
        entityPersonName.textContent = entities.person_name || "null";
        entityPersonId.textContent = entities.person_id || "null";
        entityMonth.textContent = entities.month || "null";
        entityRelationship.textContent = entities.relationship || "null";
        entityRelativeDate.textContent = entities.relative_date || "null";

        debugRawJson.textContent = JSON.stringify(debugData, null, 2);
    }

    /**
     * Send message to backend
     */
    async function sendMessage(messageText) {
        const cleanMsg = (messageText || "").trim();
        if (!cleanMsg || isRequestPending) return;

        // Display user message in UI
        appendMessage(cleanMsg, "user");
        chatInput.value = "";
        isRequestPending = true;
        sendBtn.disabled = true;
        showTypingIndicator();

        try {
            // Send POST to Flask /chat route (Port 5002)
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: cleanMsg }),
            });

            const data = await response.json();
            removeTypingIndicator();

            if (!response.ok) {
                const errorMsg = data.answer || "An error occurred while communicating with the assistant.";
                appendMessage(`⚠️ ${errorMsg}`, "assistant");
                if (data.debug) updateDebugPanel(data.debug);
            } else {
                appendMessage(data.answer, "assistant");
                if (data.debug) updateDebugPanel(data.debug);
            }
        } catch (err) {
            removeTypingIndicator();
            appendMessage(
                "⚠️ Network connection failed. Please ensure the Flask server is running on http://127.0.0.1:5002.",
                "assistant"
            );
            console.error("Fetch error:", err);
        } finally {
            isRequestPending = false;
            sendBtn.disabled = false;
            chatInput.focus();
        }
    }

    // Form submission (click Send or press Enter)
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        sendMessage(chatInput.value);
    });

    // Enter key handling on input field
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // Suggested prompt click handlers
    suggestedChips.forEach((chip) => {
        chip.addEventListener("click", () => {
            const prompt = chip.getAttribute("data-prompt");
            if (prompt) {
                sendMessage(prompt);
            }
        });
    });

    // Reset Chat conversation
    resetChatBtn.addEventListener("click", () => {
        if (confirm("Reset conversation back to starting state?")) {
            chatMessages.innerHTML = initialWelcomeHTML;
            debugIntent.textContent = "None yet";
            entityPersonName.textContent = "null";
            entityPersonId.textContent = "null";
            entityMonth.textContent = "null";
            entityRelationship.textContent = "null";
            entityRelativeDate.textContent = "null";
            debugRawJson.textContent = '{ "status": "Conversation reset" }';
            chatInput.value = "";
            chatInput.focus();
        }
    });

    // Toggle Debug Panel
    toggleDebugBtn.addEventListener("click", () => {
        debugPanel.classList.toggle("hidden");
    });

    closeDebugBtn.addEventListener("click", () => {
        debugPanel.classList.add("hidden");
    });

    // Auto-focus input on page load
    chatInput.focus();
});
