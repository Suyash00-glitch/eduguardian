import { useState, useEffect, useRef } from 'react';
import './App.css';
import { ChatWindow } from './components/ChatWindow';
import { InputBar } from './components/InputBar';
import { StudyPlanCard } from './components/StudyPlanCard';
import { useChat } from './hooks/useChat';

function App() {
  const {
    messages,
    studyPlan,
    isLoading,
    activeAgentStatus,
    error,
    conversationId,
    conversations,
    send,
    retry,
    newChat,
    loadConversation,
    loadConversations,
    removeConversation,
    renameConversation,
    toggleTask,
    clearError,
  } = useChat();

  const [showPlan, setShowPlan] = useState(false);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);
  const [editingConvId, setEditingConvId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  // Light / Dark Theme State & Persistence
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') return saved;
    if (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Show the plan card automatically only when a brand new study plan arrives
  const lastPlanRef = useRef<any>(null);
  useEffect(() => {
    if (studyPlan && studyPlan !== lastPlanRef.current) {
      lastPlanRef.current = studyPlan;
      setShowPlan(true);
    }
  }, [studyPlan]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const activeConv = conversations.find((c) => c.conversation_id === conversationId);

  const startEditing = (convId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingConvId(convId);
    setEditingTitle(currentTitle);
  };

  const handleSaveTitle = async (convId: string, e?: React.FormEvent | React.MouseEvent | React.KeyboardEvent) => {
    if (e) e.stopPropagation();
    const trimmed = editingTitle.trim();
    if (trimmed) {
      await renameConversation(convId, trimmed);
    }
    setEditingConvId(null);
    setEditingTitle('');
  };

  const handleCancelEdit = (e?: React.MouseEvent | React.KeyboardEvent) => {
    if (e) e.stopPropagation();
    setEditingConvId(null);
    setEditingTitle('');
  };

  return (
    <div className="app">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="app-header" role="banner">
        <div className="header-brand">
          <div className="header-logo" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <div className="header-title-row">
              <h1 className="header-title">EduGuardian AI</h1>
              {activeConv && (
                <span
                  className="active-conv-chip"
                  title="Current conversation title"
                  onClick={() => setShowHistoryDrawer(true)}
                >
                  💬 {activeConv.title || 'Study Session'}
                </span>
              )}
            </div>
            <p className="header-subtitle">Your personal academic coach</p>
          </div>
        </div>

        <div className="header-actions">
          {/* Theme Selector Toggle */}
          <button
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} theme`}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} theme`}
            data-testid="theme-toggle-btn"
          >
            <span className="btn-icon">{theme === 'dark' ? '☀️' : '🌙'}</span>
            <span className="btn-label">{theme === 'dark' ? 'Light' : 'Dark'}</span>
          </button>

          <button
            className="header-btn"
            onClick={() => {
              loadConversations();
              setShowHistoryDrawer(!showHistoryDrawer);
            }}
            aria-label="Toggle conversation history"
            title="Conversation History"
            data-testid="history-drawer-btn"
          >
            <span className="btn-icon">📂</span>
            <span className="btn-label">History</span>
          </button>

          <button
            className="header-btn header-btn-primary"
            onClick={newChat}
            aria-label="Start new conversation"
            data-testid="new-chat-btn"
          >
            <span className="btn-icon">+</span>
            <span className="btn-label">New Chat</span>
          </button>

          <div
            className={`header-status status-${error ? 'offline' : isLoading ? 'connecting' : 'online'}`}
            aria-label={`Service status: ${error ? 'offline' : isLoading ? 'connecting' : 'online'}`}
            data-testid="connection-status"
          >
            <span className="status-dot" />
            <span className="status-label">
              {error ? 'Offline' : isLoading ? 'Thinking…' : 'Online'}
            </span>
          </div>
        </div>
      </header>

      {/* ── History Drawer ──────────────────────────────────────── */}
      {showHistoryDrawer && (
        <div className="history-drawer-overlay" onClick={() => setShowHistoryDrawer(false)}>
          <aside
            className="history-drawer"
            onClick={(e) => e.stopPropagation()}
            aria-label="Past conversations"
            data-testid="history-drawer"
          >
            <div className="drawer-header">
              <h2 className="drawer-title">Conversations</h2>
              <button
                className="drawer-close"
                onClick={() => setShowHistoryDrawer(false)}
                aria-label="Close history"
              >
                ✕
              </button>
            </div>

            <button
              className="drawer-new-btn"
              onClick={() => {
                newChat();
                setShowHistoryDrawer(false);
              }}
            >
              + Start New Conversation
            </button>

            <div className="drawer-list">
              {conversations.length === 0 ? (
                <p className="drawer-empty">No previous conversations yet.</p>
              ) : (
                conversations.map((conv) => {
                  const isEditing = editingConvId === conv.conversation_id;
                  const displayTitle = conv.title || 'Study Session';

                  return (
                    <div
                      key={conv.conversation_id}
                      className={`drawer-item ${conv.conversation_id === conversationId ? 'active' : ''} ${isEditing ? 'editing' : ''}`}
                      onClick={() => {
                        if (!isEditing) {
                          loadConversation(conv.conversation_id);
                          setShowHistoryDrawer(false);
                        }
                      }}
                    >
                      {isEditing ? (
                        <div className="drawer-item-edit-form" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="text"
                            className="drawer-item-input"
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveTitle(conv.conversation_id, e);
                              if (e.key === 'Escape') handleCancelEdit(e);
                            }}
                            autoFocus
                            maxLength={80}
                            placeholder="Name this conversation..."
                          />
                          <div className="drawer-item-edit-btns">
                            <button
                              type="button"
                              className="drawer-edit-btn save"
                              onClick={(e) => handleSaveTitle(conv.conversation_id, e)}
                              title="Save title (Enter)"
                              aria-label="Save title"
                            >
                              ✓
                            </button>
                            <button
                              type="button"
                              className="drawer-edit-btn cancel"
                              onClick={(e) => handleCancelEdit(e)}
                              title="Cancel (Esc)"
                              aria-label="Cancel edit"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div className="drawer-item-content">
                            <span className="drawer-item-title" title={displayTitle}>
                              {displayTitle}
                            </span>
                            <span className="drawer-item-date">
                              {conv.created_at ? new Date(conv.created_at).toLocaleDateString() : ''}
                            </span>
                          </div>
                          <div className="drawer-item-actions" onClick={(e) => e.stopPropagation()}>
                            <button
                              className="drawer-item-action-btn edit"
                              onClick={(e) => startEditing(conv.conversation_id, displayTitle, e)}
                              aria-label="Rename conversation"
                              title="Rename conversation"
                            >
                              ✏️
                            </button>
                            <button
                              className="drawer-item-action-btn del"
                              onClick={(e) => {
                                e.stopPropagation();
                                removeConversation(conv.conversation_id);
                              }}
                              aria-label="Delete conversation"
                              title="Delete conversation"
                            >
                              🗑️
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </aside>
        </div>
      )}

      {/* ── Error Banner ────────────────────────────────────────── */}
      {error && (
        <div className="error-banner" role="alert" data-testid="error-banner">
          <span>⚠️ {error.includes('Traceback') || error.includes('500') || error.includes('Error') ? 'Something went wrong while connecting to EduGuardian. Please try again. 🔄' : error}</span>
          <div className="error-actions">
            <button className="error-retry-btn" onClick={retry}>Retry</button>
            <button onClick={clearError} aria-label="Dismiss error">✕</button>
          </div>
        </div>
      )}

      {/* ── Main Chat Area ──────────────────────────────────────── */}
      <main className="app-body" id="chat-main">
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          activeAgentStatus={activeAgentStatus}
          studyPlan={studyPlan}
          onOpenStudyPlan={() => setShowPlan(true)}
          onSelectPrompt={(prompt) => send(prompt)}
        />
      </main>

      {/* ── Input Bar ───────────────────────────────────────────── */}
      <InputBar
        onSend={send}
        isLoading={isLoading}
      />

      {/* ── Study Plan Modal ────────────────────────────────────── */}
      {showPlan && studyPlan && (
        <StudyPlanCard
          plan={studyPlan}
          onClose={() => setShowPlan(false)}
          onToggleTask={toggleTask}
        />
      )}
    </div>
  );
}

export default App;
