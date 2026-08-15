// API client — handles all HTTP calls to the FastAPI backend.
// Auth: attaches the JWT token from localStorage to every request (if present).

import type { ChatResponse, ConversationHistory, ConversationSummary, SendMessagePayload } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

function getToken(): string | null {
  return localStorage.getItem('edu_token');
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message = body?.error?.message || body?.detail || `HTTP ${res.status}: An error occurred.`;
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

/**
 * Send a message to the chatbot.
 * Returns the assistant's response + optional study plan.
 */
export async function sendMessage(payload: SendMessagePayload): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse<ChatResponse>(res);
}

export interface StreamHandlers {
  onChunk: (text: string) => void;
  onMeta?: (meta: { conversation_id: string; message_id: string; study_plan: any; agents_used: string[] }) => void;
  onError?: (err: Error) => void;
  onDone?: () => void;
}

/**
 * Send a message and stream the assistant response tokens via SSE.
 */
export async function sendMessageStream(
  payload: SendMessagePayload,
  handlers: StreamHandlers,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message = body?.error?.message || body?.detail || `HTTP ${res.status}: An error occurred.`;
    throw new Error(message);
  }

  if (!res.body) {
    throw new Error('ReadableStream not supported.');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith('data:')) continue;

      const dataStr = trimmed.slice(5).trim();
      if (!dataStr) continue;

      try {
        const parsed = JSON.parse(dataStr);
        if (parsed.type === 'chunk' && typeof parsed.text === 'string') {
          handlers.onChunk(parsed.text);
        } else if (parsed.type === 'meta') {
          handlers.onMeta?.(parsed);
        } else if (parsed.type === 'error') {
          throw new Error(parsed.message || 'Streaming failed.');
        } else if (parsed.type === 'done') {
          handlers.onDone?.();
        }
      } catch (err) {
        if (err instanceof Error && !err.message.includes('JSON')) {
          handlers.onError?.(err);
        }
      }
    }
  }

  handlers.onDone?.();
}


/**
 * Fetch conversation history by conversation_id.
 */
export async function fetchHistory(conversationId: string): Promise<ConversationHistory> {
  const res = await fetch(`${BASE_URL}/chat/${conversationId}/messages`, {
    method: 'GET',
    headers: authHeaders(),
  });
  return handleResponse<ConversationHistory>(res);
}

/**
 * Fetch list of all conversations for the student.
 */
export async function fetchConversations(): Promise<ConversationSummary[]> {
  const res = await fetch(`${BASE_URL}/chat/conversations`, {
    method: 'GET',
    headers: authHeaders(),
  });
  return handleResponse<ConversationSummary[]>(res);
}

/**
 * Delete a conversation thread.
 */
export async function deleteConversation(conversationId: string): Promise<{ status: string }> {
  const res = await fetch(`${BASE_URL}/chat/${conversationId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  return handleResponse<{ status: string }>(res);
}

/**
 * Rename a conversation thread title.
 */
export async function renameConversation(
  conversationId: string,
  title: string,
): Promise<{ status: string; conversation_id: string; title: string }> {
  const res = await fetch(`${BASE_URL}/chat/${conversationId}/title`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: JSON.stringify({ title }),
  });
  return handleResponse<{ status: string; conversation_id: string; title: string }>(res);
}


/**
 * Health check — useful for verifying backend connectivity.
 */
export async function checkHealth(): Promise<{ status: string }> {
  const rootUrl = BASE_URL.replace(/\/api(\/v1)?$/, '');
  const res = await fetch(`${rootUrl}/health`);
  return handleResponse<{ status: string }>(res);
}
