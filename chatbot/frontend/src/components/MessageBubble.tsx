import React, { useState } from 'react';
import type { Message } from '../types';
import './MessageBubble.css';

interface Props {
  message: Message;
}

/**
  * Formats an ISO-8601 timestamp string into a local human-readable time.
  * Uses the browser's resolved locale and timezone (never hardcoded).
  */
export function formatMessageTime(isoString?: string | null): string {
  if (!isoString) return '';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return '';

  const now = new Date();
  const isToday =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();

  const timeStr = date.toLocaleTimeString([], {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });

  if (isToday) {
    return timeStr;
  }

  const dateStr = date.toLocaleDateString([], {
    month: 'short',
    day: 'numeric',
  });
  return `${dateStr} · ${timeStr}`;
}

/**
 * Lightweight safe markdown renderer for assistant responses.
 * Parses bold, italics, inline code, code blocks, lists, headings, and links.
 */
function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBlockContent: string[] = [];
  let listItems: string[] = [];
  let isNumberedList = false;

  const flushList = () => {
    if (listItems.length > 0) {
      if (isNumberedList) {
        elements.push(
          <ol key={`ol-${elements.length}`} className="bubble-list bubble-ol">
            {listItems.map((item, idx) => (
              <li key={idx}>{parseInlineFormatting(item)}</li>
            ))}
          </ol>
        );
      } else {
        elements.push(
          <ul key={`ul-${elements.length}`} className="bubble-list bubble-ul">
            {listItems.map((item, idx) => (
              <li key={idx}>{parseInlineFormatting(item)}</li>
            ))}
          </ul>
        );
      }
      listItems = [];
      isNumberedList = false;
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

    // Numbered list item
    if (/^\d+\.\s+/.test(line.trim())) {
      if (!isNumberedList && listItems.length > 0) flushList();
      isNumberedList = true;
      listItems.push(line.trim().replace(/^\d+\.\s+/, ''));
      continue;
    }

    // Bullet list item
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ') || line.trim().startsWith('• ')) {
      if (isNumberedList && listItems.length > 0) flushList();
      isNumberedList = false;
      listItems.push(line.trim().replace(/^[-*•]\s+/, ''));
      continue;
    }

    flushList();

    // Headings
    if (line.startsWith('### ')) {
      elements.push(<h4 key={`h4-${elements.length}`} className="bubble-heading h4">{parseInlineFormatting(line.slice(4))}</h4>);
      continue;
    }
    if (line.startsWith('## ')) {
      elements.push(<h3 key={`h3-${elements.length}`} className="bubble-heading h3">{parseInlineFormatting(line.slice(3))}</h3>);
      continue;
    }
    if (line.startsWith('# ')) {
      elements.push(<h2 key={`h2-${elements.length}`} className="bubble-heading h2">{parseInlineFormatting(line.slice(2))}</h2>);
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
  const codeParts = text.split(/(`[^`]+`)/g);
  return codeParts.map((part, index) => {
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return <code key={index} className="bubble-inline-code">{part.slice(1, -1)}</code>;
    }

    // Links [title](url)
    const linkParts = part.split(/(\[[^\]]+\]\([^)]+\))/g);
    return linkParts.map((lPart, lIndex) => {
      const linkMatch = lPart.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (linkMatch) {
        return (
          <a
            key={`${index}-${lIndex}`}
            href={linkMatch[2]}
            target="_blank"
            rel="noopener noreferrer"
            className="bubble-link"
          >
            {linkMatch[1]}
          </a>
        );
      }

      // Bold formatting (**text**)
      const boldParts = lPart.split(/(\*\*[^*]+\*\*)/g);
      return boldParts.map((bPart, bIndex) => {
        if (bPart.startsWith('**') && bPart.endsWith('**') && bPart.length > 4) {
          return <strong key={`${index}-${lIndex}-${bIndex}`}>{bPart.slice(2, -2)}</strong>;
        }
        // Italic formatting (*text*)
        const italicParts = bPart.split(/(\*[^*]+\*)/g);
        return italicParts.map((iPart, iIndex) => {
          if (iPart.startsWith('*') && iPart.endsWith('*') && iPart.length > 2) {
            return <em key={`${index}-${lIndex}-${bIndex}-${iIndex}`}>{iPart.slice(1, -1)}</em>;
          }
          return iPart;
        });
      });
    });
  });
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'helpful' | 'not-helpful' | null>(null);

  if (!message.content || message.content.trim() === '') {
    return null;
  }

  const isUser = message.role === 'user';
  const time = formatMessageTime(message.created_at);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.warn('Clipboard copy failed', err);
    }
  };

  const toggleFeedback = (type: 'helpful' | 'not-helpful') => {
    setFeedback(prev => (prev === type ? null : type));
  };

  return (
    <div
      className={`bubble-wrapper ${isUser ? 'bubble-user' : 'bubble-assistant'}`}
      data-testid={`message-${message.role}`}
    >
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

        <div className="bubble-meta-row">
          {time && <span className="bubble-time">{time}</span>}

          {!isUser && (
            <div className="bubble-actions" role="toolbar" aria-label="Message options">
              <button
                className={`bubble-action-btn ${copied ? 'action-active' : ''}`}
                onClick={handleCopy}
                aria-label={copied ? 'Message copied' : 'Copy message to clipboard'}
                title={copied ? 'Copied!' : 'Copy'}
              >
                {copied ? (
                  <>
                    <span className="action-icon">✓</span>
                    <span className="action-label">Copied</span>
                  </>
                ) : (
                  <>
                    <span className="action-icon">📋</span>
                    <span className="action-label">Copy</span>
                  </>
                )}
              </button>

              <button
                className={`bubble-action-btn ${feedback === 'helpful' ? 'action-active' : ''}`}
                onClick={() => toggleFeedback('helpful')}
                aria-label="Mark as helpful"
                title="Helpful"
              >
                <span className="action-icon">👍</span>
              </button>

              <button
                className={`bubble-action-btn ${feedback === 'not-helpful' ? 'action-active' : ''}`}
                onClick={() => toggleFeedback('not-helpful')}
                aria-label="Mark as not helpful"
                title="Not helpful"
              >
                <span className="action-icon">👎</span>
              </button>
            </div>
          )}
        </div>
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

