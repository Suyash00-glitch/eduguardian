import React from 'react';
import './TypingIndicator.css';

export const TypingIndicator: React.FC = () => (
  <div className="typing-wrapper" aria-label="EduGuardian is thinking..." role="status">
    <div className="typing-avatar">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    </div>
    <div className="typing-bubble">
      <span className="typing-dot" />
      <span className="typing-dot" />
      <span className="typing-dot" />
    </div>
  </div>
);
