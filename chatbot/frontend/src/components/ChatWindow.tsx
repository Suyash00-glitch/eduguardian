import React, { useEffect, useRef } from 'react';
import type { Message, StudyPlan, AgentStatusEvent } from '../types';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import './ChatWindow.css';

interface Props {
  messages: Message[];
  isLoading: boolean;
  activeAgentStatus?: AgentStatusEvent | null;
  studyPlan: StudyPlan | null;
  onOpenStudyPlan: () => void;
  onSelectPrompt?: (prompt: string) => void;
}

const STARTER_PROMPTS = [
  { icon: '📚', label: 'Teach me something', prompt: 'Teach me something' },
  { icon: '📋', label: 'Make me a study plan', prompt: 'Make me a study plan' },
  { icon: '📊', label: 'How am I doing?', prompt: 'How am I doing?' },
  { icon: '💪', label: 'Help me stay motivated', prompt: 'Help me stay motivated' },
  { icon: '🧠', label: 'Quiz me', prompt: 'Quiz me' },
];

export const ChatWindow: React.FC<Props> = ({
  messages,
  isLoading,
  activeAgentStatus,
  studyPlan,
  onOpenStudyPlan,
  onSelectPrompt,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, activeAgentStatus]);

  const isEmpty = messages.length === 0 && !isLoading;

  return (
    <div className="chat-window" role="log" aria-live="polite" aria-label="Chat messages">
      {isEmpty ? (
        <div className="chat-empty" data-testid="chat-empty-state">
          <div className="chat-empty-icon" aria-hidden="true">👋</div>
          <h2 className="chat-empty-title">Hi! I'm EduGuardian</h2>
          <p className="chat-empty-subtitle">
            Your personal academic coach. Ready to help you master coursework,
            structure study schedules, and reach your full potential.
          </p>
          <div className="chat-empty-chips" role="group" aria-label="Suggested starter questions">
            {STARTER_PROMPTS.map((item, i) => (
              <button
                key={i}
                className="empty-chip"
                onClick={() => onSelectPrompt?.(item.prompt)}
                aria-label={`Ask: ${item.label}`}
              >
                <span className="empty-chip-icon">{item.icon}</span>
                <span className="empty-chip-label">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="chat-messages-container" data-testid="chat-messages-list">
          {messages
            .filter((msg) => msg.content && msg.content.trim().length > 0)
            .map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          {isLoading && (!messages.length || messages[messages.length - 1].role === 'user' || !messages[messages.length - 1].content || messages[messages.length - 1].content.trim().length === 0) && (
            <TypingIndicator status={activeAgentStatus} />
          )}
        </div>
      )}

      {/* Study Plan Badge (appears when a plan is available) */}
      {studyPlan && !isEmpty && (
        <div className="plan-badge-wrapper">
          <button
            id="study-plan-badge"
            className="plan-badge"
            onClick={onOpenStudyPlan}
            aria-label="View your study plan"
            data-testid="view-study-plan-btn"
          >
            <span className="plan-badge-icon">📋</span>
            <div className="plan-badge-text-group">
              <span className="plan-badge-text">View Active Study Plan</span>
              <span className="plan-badge-subtext">{studyPlan.title || 'Personalized Schedule'} • {studyPlan.tasks?.length || 0} tasks</span>
            </div>
            <span className="plan-badge-arrow">→</span>
          </button>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};

