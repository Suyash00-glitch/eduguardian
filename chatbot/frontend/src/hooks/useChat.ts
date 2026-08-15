import { useState, useCallback, useRef, useEffect } from 'react';
import type { Message, ChatState } from '../types';
import {
  sendMessage,
  sendMessageStream,
  fetchHistory,
  fetchConversations,
  deleteConversation,
  renameConversation as apiRenameConversation,
} from '../api/chatApi';

/**
 * useChat — State Management for the EduGuardian Student Chatbot.
 *
 * Coordinates:
 * - Multi-turn message list (user & assistant messages)
 * - Progressive SSE token streaming
 * - Active study plan with interactive task checkoff
 * - Conversation thread selection and history loading
 * - Safe error handling and retry mechanism
 */
export function useChat() {
  const [state, setState] = useState<ChatState>({
    conversationId: null,
    messages: [],
    studyPlan: null,
    isLoading: false,
    error: null,
    conversations: [],
  });

  const conversationIdRef = useRef<string | null>(null);
  const lastUserMessageRef = useRef<string | null>(null);

  // Sync ref with state
  useEffect(() => {
    conversationIdRef.current = state.conversationId;
  }, [state.conversationId]);

  // Load past conversation threads
  const loadConversations = useCallback(async () => {
    try {
      const convs = await fetchConversations();
      setState(prev => ({ ...prev, conversations: convs }));
    } catch {
      // Fallback silently if offline or unauthenticated
    }
  }, []);

  // Send message turn with progressive SSE streaming
  const send = useCallback(async (content: string) => {
    const text = content.trim();
    if (!text || state.isLoading) return;

    lastUserMessageRef.current = text;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    const assistantMsgId = crypto.randomUUID();
    const initialAssistantMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage, initialAssistantMsg],
      isLoading: true,
      error: null,
    }));

    try {
      await sendMessageStream(
        {
          message: text,
          conversation_id: conversationIdRef.current ?? undefined,
        },
        {
          onChunk: (chunk: string) => {
            setState(prev => {
              const updatedMessages = prev.messages.map(m => {
                if (m.id === assistantMsgId) {
                  return { ...m, content: m.content + chunk };
                }
                return m;
              });
              return { ...prev, messages: updatedMessages };
            });
          },
          onMeta: (meta) => {
            if (meta.conversation_id) {
              conversationIdRef.current = meta.conversation_id;
              setState(prev => ({
                ...prev,
                conversationId: meta.conversation_id,
                studyPlan: meta.study_plan ?? prev.studyPlan,
              }));
            }
          },
          onError: (err) => {
            setState(prev => ({
              ...prev,
              messages: prev.messages.filter(m => m.id !== assistantMsgId || m.content.length > 0),
              isLoading: false,
              error: err.message || 'Stream connection interrupted.',
            }));
          },
          onDone: () => {
            setState(prev => ({ ...prev, isLoading: false }));
            loadConversations();
          },
        },
      );
    } catch (err) {
      // Fallback to standard unary POST if streaming fails
      try {
        const response = await sendMessage({
          message: text,
          conversation_id: conversationIdRef.current ?? undefined,
        });
        conversationIdRef.current = response.conversation_id;
        setState(prev => ({
          ...prev,
          conversationId: response.conversation_id,
          messages: prev.messages.filter(m => m.id !== assistantMsgId).concat(response.message),
          studyPlan: response.study_plan ?? prev.studyPlan,
          isLoading: false,
        }));
        loadConversations();
      } catch (fallbackErr) {
        const message = fallbackErr instanceof Error ? fallbackErr.message : 'Something went wrong. Please try again.';
        setState(prev => ({
          ...prev,
          messages: prev.messages.filter(m => m.id !== assistantMsgId || m.content.length > 0),
          isLoading: false,
          error: message,
        }));
      }
    }
  }, [state.isLoading, loadConversations]);


  // Retry last failed turn
  const retry = useCallback(() => {
    if (lastUserMessageRef.current) {
      send(lastUserMessageRef.current);
    }
  }, [send]);

  // Start new conversation
  const newChat = useCallback(() => {
    conversationIdRef.current = null;
    lastUserMessageRef.current = null;
    setState(prev => ({
      ...prev,
      conversationId: null,
      messages: [],
      studyPlan: null,
      error: null,
    }));
  }, []);

  // Load existing conversation thread
  const loadConversation = useCallback(async (convId: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const history = await fetchHistory(convId);
      conversationIdRef.current = history.conversation_id;
      setState(prev => ({
        ...prev,
        conversationId: history.conversation_id,
        messages: history.messages,
        studyPlan: null,
        isLoading: false,
      }));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Could not load conversation history.';
      setState(prev => ({ ...prev, isLoading: false, error: msg }));
    }
  }, []);

  // Delete conversation
  const removeConversation = useCallback(async (convId: string) => {
    try {
      await deleteConversation(convId);
      if (state.conversationId === convId) {
        newChat();
      }
      loadConversations();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Could not delete conversation.';
      setState(prev => ({ ...prev, error: msg }));
    }
  }, [state.conversationId, newChat, loadConversations]);

  // Rename conversation title
  const renameConversation = useCallback(async (convId: string, newTitle: string) => {
    const trimmed = newTitle.trim();
    if (!trimmed) return;
    try {
      await apiRenameConversation(convId, trimmed);
      setState(prev => ({
        ...prev,
        conversations: prev.conversations.map(c =>
          c.conversation_id === convId ? { ...c, title: trimmed } : c
        ),
      }));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Could not rename conversation.';
      setState(prev => ({ ...prev, error: msg }));
    }
  }, []);

  // Check off study task in UI
  const toggleTask = useCallback((taskIdOrTitle: string) => {
    setState(prev => {
      if (!prev.studyPlan) return prev;
      const updatedTasks = prev.studyPlan.tasks.map(t => {
        const id = t.task_id || t.title || t.activity;
        if (id === taskIdOrTitle || t.title === taskIdOrTitle || t.activity === taskIdOrTitle) {
          return { ...t, completed: !t.completed };
        }
        return t;
      });
      return {
        ...prev,
        studyPlan: {
          ...prev.studyPlan,
          tasks: updatedTasks,
        },
      };
    });
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const clearStudyPlan = useCallback(() => {
    setState(prev => ({ ...prev, studyPlan: null }));
  }, []);

  return {
    messages: state.messages,
    studyPlan: state.studyPlan,
    isLoading: state.isLoading,
    error: state.error,
    conversationId: state.conversationId,
    conversations: state.conversations,
    send,
    retry,
    newChat,
    loadConversation,
    loadConversations,
    removeConversation,
    renameConversation,
    toggleTask,
    clearError,
    clearStudyPlan,
  };
}

