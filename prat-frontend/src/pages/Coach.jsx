import React, { useState } from "react";
import { Bot, Send, Sparkles, Trash2, User } from "lucide-react";

import { coachService } from "../services/coachService";

const suggestions = [
  "Help me make a study plan",
  "How can I improve my attendance?",
  "What should I do about my assignments?",
];

function Coach() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "assistant",
      text: "Hi Pratham! I'm your EduGuardian Coach. I can help you plan your studies, manage assignments, improve your academic habits, and work through your recovery goals.",
    },
  ]);

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const sendMessage = async (text = input) => {
    const message = text.trim();

    if (!message || sending) return;

    setInput("");

    setMessages((current) => [
      ...current,
      {
        id: Date.now(),
        role: "student",
        text: message,
      },
    ]);

    setSending(true);

    try {
      const reply = await coachService.sendMessage(message);

      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          text: reply,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: Date.now(),
        role: "assistant",
        text: "Chat cleared. What would you like help with?",
      },
    ]);
  };

  return (
    <div className="coach-page">
      {/* HEADER */}

      <div className="coach-header">
        <div>
          <span className="dashboard-eyebrow">RECOVERY COACH</span>

          <h2>AI Coach</h2>

          <p>Get personalized guidance for your academic journey.</p>
        </div>

        <button className="coach-clear" onClick={clearChat}>
          <Trash2 size={13} />
          Clear
        </button>
      </div>

      {/* CHAT */}

      <section className="coach-container">
        <div className="coach-chat">
          {messages.map((message) => {
            const assistant = message.role === "assistant";

            return (
              <div
                className={`coach-message ${
                  assistant ? "assistant" : "student"
                }`}
                key={message.id}
              >
                <div className="coach-avatar">
                  {assistant ? <Bot size={15} /> : <User size={15} />}
                </div>

                <div className="coach-bubble">{message.text}</div>
              </div>
            );
          })}

          {sending && (
            <div className="coach-message assistant">
              <div className="coach-avatar">
                <Bot size={15} />
              </div>

              <div className="coach-bubble coach-typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          )}
        </div>

        {/* SUGGESTIONS */}

        <div className="coach-suggestions">
          <span>Try asking</span>

          <div>
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => sendMessage(suggestion)}
                disabled={sending}
              >
                <Sparkles size={11} />
                {suggestion}
              </button>
            ))}
          </div>
        </div>

        {/* INPUT */}

        <div className="coach-input-area">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask your AI Coach..."
            rows={1}
            disabled={sending}
          />

          <button
            className="coach-send"
            onClick={() => sendMessage()}
            disabled={!input.trim() || sending}
          >
            <Send size={15} />
          </button>
        </div>

        <div className="coach-disclaimer">
          EduGuardian Coach provides guidance and support. Important academic
          decisions remain with you and your faculty/mentor.
        </div>
      </section>
    </div>
  );
}

export default Coach;
