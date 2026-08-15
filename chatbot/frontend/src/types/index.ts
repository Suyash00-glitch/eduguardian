// Shared TypeScript interfaces for the EduGuardian Chatbot frontend

export type MessageRole = 'user' | 'assistant';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface StudyTask {
  task_id?: string;
  title: string;
  activity?: string;
  day?: string;
  time_slot?: string;
  subject: string;
  description?: string;
  duration_minutes: number;
  priority: 'high' | 'medium' | 'low';
  completed?: boolean;
}

export interface StudyPlan {
  title: string;
  week_start: string;
  goals: string[];
  tasks: StudyTask[];
  resources?: string[];
  notes?: string;
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
  study_plan: StudyPlan | null;
  agents_used?: string[];
}

export interface ConversationHistory {
  conversation_id: string;
  messages: Message[];
  created_at: string;
}

export interface ConversationSummary {
  conversation_id: string;
  student_id: string;
  title?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ChatState {
  conversationId: string | null;
  messages: Message[];
  studyPlan: StudyPlan | null;
  isLoading: boolean;
  error: string | null;
  conversations: ConversationSummary[];
}

export interface SendMessagePayload {
  message: string;
  conversation_id?: string;
}
