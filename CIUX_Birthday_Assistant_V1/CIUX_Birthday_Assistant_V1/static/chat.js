const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");


function addMessage(message, sender, debug = null) {

    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = message;

    messageDiv.appendChild(bubble);

    // Display V2 NLU debugging information
    if (debug) {

        const debugDiv = document.createElement("div");
        debugDiv.className = "debug";

        debugDiv.textContent =
            "V2 NLU DEBUG:\n" +
            JSON.stringify(debug, null, 2);

        messageDiv.appendChild(debugDiv);
    }

    chatBox.appendChild(messageDiv);

    chatBox.scrollTop = chatBox.scrollHeight;
}


async function sendMessage() {

    const message = messageInput.value.trim();

    if (message === "") {
        return;
    }

    addMessage(message, "user");

    messageInput.value = "";

    sendButton.disabled = true;
    sendButton.textContent = "Sending...";

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })

        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        addMessage(
            data.answer || "No response received.",
            "assistant",
            data.debug
        );

    }

    catch (error) {

        console.error("Chat error:", error);

        addMessage(
            "Sorry! Something went wrong. Please check the Flask server.",
            "assistant"
        );

    }

    finally {

        sendButton.disabled = false;
        sendButton.textContent = "Send ➤";

        messageInput.focus();

    }

}


// Click suggestion buttons
function askQuestion(question) {

    messageInput.value = question;

    sendMessage();

}


// Press Enter to send
messageInput.addEventListener("keydown", function(event) {

    if (event.key === "Enter") {

        sendMessage();

    }

});