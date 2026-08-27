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

export interface QuizState {
  active: boolean;
  topic: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  step: 'awaiting_topic' | 'in_progress' | 'completed';
  current_question_number: number;
  total_questions: number;
  current_question_type: 'multiple_choice' | 'short_answer';
  current_question_text?: string | null;
  current_options?: string[] | null;
  last_student_answer?: string | null;
  last_evaluation?: 'correct' | 'partially_correct' | 'incorrect' | 'unclear' | null;
  score: number;
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
  study_plan: StudyPlan | null;
  teaching_state?: any;
  quiz_state?: QuizState | null;
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

export interface AgentStatusEvent {
  type: 'agent_status';
  agent: string;
  display_name: string;
  status: 'working' | 'complete';
  message?: string;
  icon?: string;
}

export interface ChatState {
  conversationId: string | null;
  messages: Message[];
  studyPlan: StudyPlan | null;
  isLoading: boolean;
  activeAgentStatus?: AgentStatusEvent | null;
  error: string | null;
  conversations: ConversationSummary[];
}

export interface SendMessagePayload {
  message: string;
  conversation_id?: string;
  user_id?: string;
}
