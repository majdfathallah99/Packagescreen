/** Standalone page script; no global backend registration **/
(function () {
    function renderMessage(role, content) {
        const messagesEl = document.getElementById("gpt5_chat_messages");
        const b = document.createElement("div");
        b.style.margin = "6px 0";
        b.style.padding = "8px 10px";
        b.style.borderRadius = "10px";
        b.style.background = role === "user" ? "#e9f5ff" : "#f6f6f6";
        b.textContent = content;
        messagesEl.appendChild(b);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function mount() {
        const inputEl = document.getElementById("gpt5_chat_input");
        const sendBtn = document.getElementById("gpt5_send_btn");
        if (!inputEl || !sendBtn) return;
        const history = [];
        renderMessage("assistant", "مرحبًا! أنا مساعد Odoo الذكي. / Hi! I’m your Odoo assistant.");

        async function send() {
            const text = (inputEl.value || "").trim();
            if (!text) return;
            inputEl.value = "";
            renderMessage("user", text);
            history.push({ role: "user", content: text });

            let result;
            try {
                const resp = await fetch("/ai_assistant/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ prompt: text, history }),
                });
                result = await resp.json();
            } catch (e) {
                result = { ok: false, error: e?.message || String(e) };
            }

            if (result && result.ok) {
                renderMessage("assistant", result.reply || "(no reply)");
                history.push({ role: "assistant", content: result.reply || "" });
            } else {
                renderMessage("assistant", "⚠ " + (result?.error || "Error"));
            }
        }

        sendBtn.addEventListener("click", send);
        inputEl.addEventListener("keydown", (e) => {
            if (e.key === "Enter") send();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", mount);
    } else {
        mount();
    }
})();
