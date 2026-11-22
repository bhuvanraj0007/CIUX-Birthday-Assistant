/**
 * chat.js - Conversational Interface, Speech Recognition (Voice Input),
 * and Speech Synthesis (Voice Output) for CIUX Birthday Assistant V5.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const chatMessages = document.getElementById("chatMessages");
    const chatInput = document.getElementById("chatInput");
    const chatForm = document.getElementById("chatForm");
    const sendBtn = document.getElementById("sendBtn");
    const micBtn = document.getElementById("micBtn");
    const resetBtn = document.getElementById("resetBtn");
    const voiceToggle = document.getElementById("voiceToggle");
    const debugToggle = document.getElementById("debugToggle");
    const debugPanel = document.getElementById("debugPanel");
    const debugContent = document.getElementById("debugContent");
    const closeDebugBtn = document.getElementById("closeDebugBtn");
    const typingIndicator = document.getElementById("typingIndicator");
    const suggestedChips = document.getElementById("suggestedChips");
    const statusPill = document.getElementById("statusPill");
    const statusText = document.getElementById("statusText");
    const speechFeedback = document.getElementById("speechFeedback");

    let isProcessing = false;
    let isListening = false;
    let speechRecognition = null;
    let selectedVoice = null;

    // -------------------------------------------------------------------------
    // 1. Status Indicator Helpers
    // -------------------------------------------------------------------------
    function setStatus(status, label) {
        statusPill.className = "status-pill";
        if (status === "listening") {
            statusPill.classList.add("status-listening");
            statusText.textContent = label || "Listening...";
        } else if (status === "thinking") {
            statusPill.classList.add("status-thinking");
            statusText.textContent = label || "Thinking...";
        } else {
            statusPill.classList.add("status-ready");
            statusText.textContent = label || "Ready";
        }
    }

    // -------------------------------------------------------------------------
    // 2. Speech Synthesis (Voice Output)
    // -------------------------------------------------------------------------
    function initSpeechSynthesis() {
        if (!("speechSynthesis" in window)) {
            console.warn("Speech Synthesis not supported by this browser.");
            voiceToggle.disabled = true;
            return;
        }

        function populateVoices() {
            const voices = window.speechSynthesis.getVoices();
            // Prioritize English (India) en-IN, then fallback to en-US or en-GB
            selectedVoice = voices.find(v => v.lang === "en-IN") ||
                            voices.find(v => v.lang.startsWith("en-") && v.name.includes("India")) ||
                            voices.find(v => v.lang === "en-US") ||
                            voices.find(v => v.lang.startsWith("en")) ||
                            voices[0];
        }

        populateVoices();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = populateVoices;
        }
    }

    function cleanTextForSpeech(text) {
        if (!text) return "";
        let clean = text;
        // Strip markdown bold and italic
        clean = clean.replace(/\*\*(.*?)\*\*/g, "$1");
        clean = clean.replace(/\*(.*?)\*/g, "$1");
        // Strip code snippets
        clean = clean.replace(/`([^`]+)`/g, "$1");
        // Strip emojis and non-standard symbols
        clean = clean.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}🎉🎂👋📍🔢📅•]/gu, "");
        // Clean multiple newlines and spaces
        clean = clean.replace(/\n+/g, ". ").replace(/\s+/g, " ").trim();
        return clean;
    }

    function speakResponse(text) {
        if (!voiceToggle.checked || !("speechSynthesis" in window)) {
            return;
        }

        window.speechSynthesis.cancel(); // Stop any pending or ongoing speech
        const speechText = cleanTextForSpeech(text);
        if (!speechText) return;

        const utterance = new SpeechSynthesisUtterance(speechText);
        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.lang = "en-IN";

        window.speechSynthesis.speak(utterance);
    }

    function stopSpeaking() {
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
        }
    }

    // -------------------------------------------------------------------------
    // 3. Speech Recognition (Voice Input - en-IN)
    // -------------------------------------------------------------------------
    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Speech Recognition API not supported in this browser.");
            micBtn.title = "Voice recognition not supported in this browser (Chrome / Edge recommended)";
            micBtn.style.opacity = "0.5";
            return;
        }

        speechRecognition = new SpeechRecognition();
        speechRecognition.lang = "en-IN";
        speechRecognition.continuous = false;
        speechRecognition.interimResults = false;
        speechRecognition.maxAlternatives = 1;

        speechRecognition.onstart = () => {
            isListening = true;
            micBtn.classList.add("listening");
            setStatus("listening", "Listening...");
            speechFeedback.textContent = "Listening... Speak now into your microphone";
        };

        speechRecognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript.trim();
            if (transcript) {
                chatInput.value = transcript;
                speechFeedback.textContent = `Recognized: "${transcript}"`;
                // Automatically send recognized speech after a brief confirmation moment
                setTimeout(() => {
                    speechFeedback.textContent = "";
                    sendMessage(transcript);
                }, 400);
            }
        };

        speechRecognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            isListening = false;
            micBtn.classList.remove("listening");
            setStatus("ready");

            let errMessage = "Speech error. Please try again.";
            if (event.error === "not-allowed" || event.error === "service-not-allowed") {
                errMessage = "Microphone access was denied. Please allow microphone permissions.";
            } else if (event.error === "no-speech") {
                errMessage = "No speech detected. Please speak closer to your microphone.";
            } else if (event.error === "network") {
                errMessage = "Network error during speech recognition.";
            }
            speechFeedback.textContent = errMessage;
            setTimeout(() => { speechFeedback.textContent = ""; }, 4000);
        };

        speechRecognition.onend = () => {
            isListening = false;
            micBtn.classList.remove("listening");
            if (!isProcessing) {
                setStatus("ready");
            }
        };
    }

    function toggleSpeechRecognition() {
        if (!speechRecognition) {
            alert("Speech recognition is not supported in this browser.\nPlease use Google Chrome, Microsoft Edge, or a Web Speech API compatible browser.");
            return;
        }

        if (isListening) {
            speechRecognition.stop();
        } else {
            speechFeedback.textContent = "Initializing microphone...";
            try {
                speechRecognition.start();
            } catch (err) {
                console.error("Failed to start speech recognition:", err);
                speechRecognition.stop();
            }
        }
    }

    // -------------------------------------------------------------------------
    // 4. UI Message Rendering
    // -------------------------------------------------------------------------
    function formatMessageText(text) {
        if (!text) return "";

        // Escape dangerous HTML entities
        let formatted = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Format bold text: **text**
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

        // Format inline code: `code`
        formatted = formatted.replace(/`([^`]+)`/g, "<code>$1</code>");

        // Format bullet lists
        const lines = formatted.split("\n");
        let htmlLines = [];
        let inList = false;

        for (let line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("•") || trimmed.startsWith("-")) {
                if (!inList) {
                    htmlLines.push("<ul>");
                    inList = true;
                }
                const itemContent = trimmed.substring(1).trim();
                htmlLines.push(`<li>${itemContent}</li>`);
            } else {
                if (inList) {
                    htmlLines.push("</ul>");
                    inList = false;
                }
                if (trimmed) {
                    htmlLines.push(`<p>${trimmed}</p>`);
                }
            }
        }
        if (inList) {
            htmlLines.push("</ul>");
        }

        return htmlLines.join("");
    }

    function appendMessage(sender, text) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}-message`;

        const avatarDiv = document.createElement("div");
        avatarDiv.className = "message-avatar";

        if (sender === "assistant") {
            avatarDiv.innerHTML = `
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
                    <line x1="9" y1="9" x2="9.01" y2="9"></line>
                    <line x1="15" y1="9" x2="15.01" y2="9"></line>
                </svg>
            `;
        } else {
            avatarDiv.innerHTML = `
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>
            `;
        }

        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";

        const bubbleDiv = document.createElement("div");
        bubbleDiv.className = "message-bubble";
        bubbleDiv.innerHTML = formatMessageText(text);

        const timeSpan = document.createElement("span");
        timeSpan.className = "message-time";
        const now = new Date();
        timeSpan.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

        contentDiv.appendChild(bubbleDiv);
        contentDiv.appendChild(timeSpan);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // -------------------------------------------------------------------------
    // 5. Send Message Pipeline
    // -------------------------------------------------------------------------
    async function sendMessage(overrideText) {
        const text = overrideText !== undefined ? overrideText : chatInput.value.trim();
        if (!text || isProcessing) return;

        // Reset text input & UI states
        chatInput.value = "";
        isProcessing = true;
        sendBtn.disabled = true;
        setStatus("thinking", "Thinking...");
        typingIndicator.classList.remove("hidden");
        scrollToBottom();

        appendMessage("user", text);

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            const answer = data.answer || "No response received.";

            appendMessage("assistant", answer);

            // Update debug panel content
            if (data.debug) {
                debugContent.textContent = JSON.stringify(data.debug, null, 2);
            }

            // Speak response if voice response toggle is active
            speakResponse(answer);

        } catch (error) {
            console.error("Error communicating with backend:", error);
            const errText = "Unable to connect to the assistant backend. Please verify the Flask server is running.";
            appendMessage("assistant", errText);
            debugContent.textContent = JSON.stringify({ error: error.message }, null, 2);
        } finally {
            isProcessing = false;
            sendBtn.disabled = false;
            typingIndicator.classList.add("hidden");
            setStatus("ready");
            chatInput.focus();
        }
    }

    // -------------------------------------------------------------------------
    // 6. Reset Conversation Pipeline
    // -------------------------------------------------------------------------
    async function resetConversation() {
        if (isProcessing) return;

        stopSpeaking();
        if (isListening && speechRecognition) {
            speechRecognition.stop();
        }

        try {
            const response = await fetch("/reset", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            const data = await response.json();

            // Clear chat message window and render clean welcome notice
            chatMessages.innerHTML = "";
            appendMessage("assistant", "Conversation context has been reset. All previous memory has been cleared. What would you like to ask next?");
            debugContent.textContent = JSON.stringify({ status: "context_cleared", message: data.message }, null, 2);

        } catch (err) {
            console.error("Error resetting conversation:", err);
            appendMessage("assistant", "Failed to reset context on server. Please try again.");
        }
    }

    // -------------------------------------------------------------------------
    // 7. Event Listeners & Binding
    // -------------------------------------------------------------------------

    // Send Form & Enter key
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        sendMessage();
    });

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Microphone button
    micBtn.addEventListener("click", () => {
        toggleSpeechRecognition();
    });

    // Reset button
    resetBtn.addEventListener("click", () => {
        resetConversation();
    });

    // Suggested Chips
    suggestedChips.addEventListener("click", (e) => {
        const chip = e.target.closest(".chip-btn");
        if (chip) {
            const query = chip.dataset.query;
            if (query) {
                sendMessage(query);
            }
        }
    });

    // Debug Panel Toggle
    debugToggle.addEventListener("change", () => {
        if (debugToggle.checked) {
            debugPanel.classList.remove("hidden");
        } else {
            debugPanel.classList.add("hidden");
        }
    });

    closeDebugBtn.addEventListener("click", () => {
        debugToggle.checked = false;
        debugPanel.classList.add("hidden");
    });

    // Stop TTS when voice toggle is switched off
    voiceToggle.addEventListener("change", () => {
        if (!voiceToggle.checked) {
            stopSpeaking();
        }
    });

    // Initialize Web APIs
    initSpeechSynthesis();
    initSpeechRecognition();
    chatInput.focus();
});
