import React, { useEffect, useRef } from 'react';
import type { Message, StudyPlan } from '../types';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import './ChatWindow.css';

interface Props {
  messages: Message[];
  isLoading: boolean;
  studyPlan: StudyPlan | null;
  onOpenStudyPlan: () => void;
  onSelectPrompt?: (prompt: string) => void;
}

const STARTER_PROMPTS = [
  '📋 Make me a study plan for this week',
  '📚 How can I catch up on my courses?',
  '🎯 Help me break down exam preparation',
  '⏰ I feel overwhelmed with assignments',
];

export const ChatWindow: React.FC<Props> = ({
  messages,
  isLoading,
  studyPlan,
  onOpenStudyPlan,
  onSelectPrompt,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const isEmpty = messages.length === 0 && !isLoading;

  return (
    <div className="chat-window" role="log" aria-live="polite" aria-label="Chat messages">
      {isEmpty ? (
        <div className="chat-empty" data-testid="chat-empty-state">
          <div className="chat-empty-icon">✨</div>
          <h2 className="chat-empty-title">Hi! I'm EduGuardian</h2>
          <p className="chat-empty-subtitle">
            Your personal AI academic coach. I'm here to help you study smarter,
            organize your schedule, and reach your full potential.
          </p>
          <div className="chat-empty-chips">
            {STARTER_PROMPTS.map((prompt, i) => (
              <button
                key={i}
                className="empty-chip"
                onClick={() => onSelectPrompt?.(prompt)}
                aria-label={`Ask: ${prompt}`}
              >
                {prompt}
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
            <TypingIndicator />
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
