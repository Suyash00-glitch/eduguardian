import React, { useState, useRef, useEffect } from 'react';
import './InputBar.css';

interface Props {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const QUICK_PROMPTS = [
  '📋 Make me a study plan',
  '📊 How am I doing?',
  '💪 Help me stay motivated',
  '📖 Help me catch up',
];

export const InputBar: React.FC<Props> = ({ onSend, isLoading, disabled }) => {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading || disabled) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  };

  useEffect(() => {
    if (!isLoading) textareaRef.current?.focus();
  }, [isLoading]);

  return (
    <div className="input-bar-wrapper">
      {/* Quick prompt chips */}
      <div className="quick-prompts" role="group" aria-label="Quick prompts">
        {QUICK_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            className="quick-chip"
            onClick={() => onSend(prompt.replace(/^[\p{Emoji}\s]+/u, '').trim())}
            disabled={isLoading || disabled}
            aria-label={prompt}
          >
            {prompt}
          </button>
        ))}
      </div>

      <div className="input-bar">
        <textarea
          ref={textareaRef}
          id="chat-input"
          className="input-textarea"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything — I'm here to help you succeed…"
          rows={1}
          disabled={isLoading || disabled}
          aria-label="Message input"
          aria-multiline="true"
        />
        <button
          id="send-button"
          className={`send-button ${value.trim() && !isLoading ? 'send-active' : ''}`}
          onClick={handleSend}
          disabled={!value.trim() || isLoading || disabled}
          aria-label="Send message"
        >
          {isLoading ? (
            <span className="send-spinner" aria-hidden="true" />
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </div>

      <p className="input-hint">Press Enter to send · Shift+Enter for new line</p>
    </div>
  );
};
