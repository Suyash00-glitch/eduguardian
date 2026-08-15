import React from 'react';
import type { Message } from '../types';
import './MessageBubble.css';

interface Props {
  message: Message;
}

/**
 * Lightweight safe markdown renderer for assistant responses.
 * Parses bold, italics, inline code, code blocks, lists, and headings.
 */
function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBlockContent: string[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="bubble-list">
          {listItems.map((item, idx) => (
            <li key={idx}>{parseInlineFormatting(item)}</li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block start/end
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${elements.length}`} className="bubble-code-block">
            <code>{codeBlockContent.join('\n')}</code>
          </pre>
        );
        codeBlockContent = [];
        inCodeBlock = false;
      } else {
        flushList();
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line);
      continue;
    }

    // Bullet list item
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ') || line.trim().startsWith('• ')) {
      listItems.push(line.trim().replace(/^[-*•]\s+/, ''));
      continue;
    }

    // Numbered list item
    if (/^\d+\.\s+/.test(line.trim())) {
      listItems.push(line.trim().replace(/^\d+\.\s+/, ''));
      continue;
    }

    flushList();

    // Headings
    if (line.startsWith('### ')) {
      elements.push(<h4 key={`h4-${elements.length}`} className="bubble-heading">{parseInlineFormatting(line.slice(4))}</h4>);
      continue;
    }
    if (line.startsWith('## ')) {
      elements.push(<h3 key={`h3-${elements.length}`} className="bubble-heading">{parseInlineFormatting(line.slice(3))}</h3>);
      continue;
    }
    if (line.startsWith('# ')) {
      elements.push(<h2 key={`h2-${elements.length}`} className="bubble-heading">{parseInlineFormatting(line.slice(2))}</h2>);
      continue;
    }

    // Normal paragraph
    if (line.trim().length > 0) {
      elements.push(<p key={`p-${elements.length}`} className="bubble-p">{parseInlineFormatting(line)}</p>);
    }
  }

  flushList();
  if (inCodeBlock && codeBlockContent.length > 0) {
    elements.push(
      <pre key={`code-end`} className="bubble-code-block">
        <code>{codeBlockContent.join('\n')}</code>
      </pre>
    );
  }

  return elements.length > 0 ? elements : <p className="bubble-p">{text}</p>;
}

function parseInlineFormatting(text: string): React.ReactNode {
  // Split by inline code first
  const parts = text.split(/(`[^`]+`)/g);
  return parts.map((part, index) => {
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return <code key={index} className="bubble-inline-code">{part.slice(1, -1)}</code>;
    }

    // Bold formatting (**text**)
    const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
    return boldParts.map((bPart, bIndex) => {
      if (bPart.startsWith('**') && bPart.endsWith('**') && bPart.length > 4) {
        return <strong key={`${index}-${bIndex}`}>{bPart.slice(2, -2)}</strong>;
      }
      // Italic formatting (*text*)
      const italicParts = bPart.split(/(\*[^*]+\*)/g);
      return italicParts.map((iPart, iIndex) => {
        if (iPart.startsWith('*') && iPart.endsWith('*') && iPart.length > 2) {
          return <em key={`${index}-${bIndex}-${iIndex}`}>{iPart.slice(1, -1)}</em>;
        }
        return iPart;
      });
    });
  });
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  if (!message.content || message.content.trim() === '') {
    return null;
  }

  const isUser = message.role === 'user';
  const time = message.created_at
    ? new Date(message.created_at).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  return (
    <div className={`bubble-wrapper ${isUser ? 'bubble-user' : 'bubble-assistant'}`} data-testid={`message-${message.role}`}>
      {!isUser && (
        <div className="bubble-avatar" aria-label="EduGuardian AI">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
      )}
      <div className="bubble-content">
        <div className={`bubble ${isUser ? 'bubble-user-text' : 'bubble-assistant-text'}`}>
          {isUser ? <p className="bubble-p">{message.content}</p> : renderMarkdown(message.content)}
        </div>
        {time && <span className="bubble-time">{time}</span>}
      </div>
      {isUser && (
        <div className="bubble-avatar bubble-avatar-user" aria-label="You">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
      )}
    </div>
  );
};
