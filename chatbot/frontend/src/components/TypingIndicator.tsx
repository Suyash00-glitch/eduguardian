import React from 'react';
import type { AgentStatusEvent } from '../types';
import './TypingIndicator.css';

interface TypingIndicatorProps {
  status?: AgentStatusEvent | null;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ status }) => {
  const displayName = status?.display_name || 'EduGuardian';
  const actionMessage = status?.message || 'EduGuardian is preparing your response...';
  const icon = status?.icon || '✨';

  return (
    <div
      className="typing-wrapper"
      aria-label={`${displayName} is working...`}
      role="status"
      data-testid="agent-typing-indicator"
    >
      <div className="typing-avatar" aria-hidden="true">
        <span className="typing-agent-emoji">{icon}</span>
      </div>

      <div className="typing-bubble">
        <div className="typing-agent-header">
          <span className="typing-agent-name">{displayName}</span>
          <span className="typing-agent-badge">Active</span>
        </div>

        <div className="typing-agent-body">
          <span className="typing-action-text">{actionMessage}</span>
          <div className="typing-dots" aria-hidden="true">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        </div>
      </div>
    </div>
  );
};
