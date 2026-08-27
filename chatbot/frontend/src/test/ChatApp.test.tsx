import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';
import * as chatApi from '../api/chatApi';

vi.mock('../api/chatApi');

describe('EduGuardian Chatbot Frontend', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(chatApi.fetchConversations).mockResolvedValue([
      {
        conversation_id: 'conv-123',
        student_id: 'student_001',
        title: 'Midterm Prep',
        created_at: '2026-08-14T10:00:00Z',
      },
    ]);
  });

  it('1. Renders the main chat screen with header and empty state starter prompts', () => {
    render(<App />);

    expect(screen.getByText('EduGuardian AI')).toBeInTheDocument();
    expect(screen.getByText('Your personal academic coach')).toBeInTheDocument();
    expect(screen.getByTestId('chat-empty-state')).toBeInTheDocument();
    expect(screen.getByText('📋 Make me a study plan for this week')).toBeInTheDocument();
  });

  it('2. User can type a message and send via the Send button', async () => {
    const user = userEvent.setup();
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      conversation_id: 'conv-001',
      message: {
        id: 'msg-1',
        role: 'assistant',
        content: 'Hi! How can I help you succeed today?',
        created_at: new Date().toISOString(),
      },
      study_plan: null,
    });

    render(<App />);
    const textarea = screen.getByPlaceholderText(/Ask anything/i);
    const sendButton = screen.getByLabelText('Send message');

    await user.type(textarea, 'Hello EduGuardian');
    expect(textarea).toHaveValue('Hello EduGuardian');

    await user.click(sendButton);

    // Optimistic user bubble
    expect(screen.getByText('Hello EduGuardian')).toBeInTheDocument();

    // Assistant response arrives
    await waitFor(() => {
      expect(screen.getByText(/Hi! How can I help you succeed today?/i)).toBeInTheDocument();
    });
  });

  it('3. User can send a message using the Enter key', async () => {
    const user = userEvent.setup();
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      conversation_id: 'conv-002',
      message: {
        id: 'msg-2',
        role: 'assistant',
        content: 'I hear you! Let us break things down together.',
        created_at: new Date().toISOString(),
      },
      study_plan: null,
    });

    render(<App />);
    const textarea = screen.getByPlaceholderText(/Ask anything/i);

    await user.type(textarea, 'I am feeling overwhelmed{enter}');

    expect(screen.getByText('I am feeling overwhelmed')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Let us break things down together/i)).toBeInTheDocument();
    });
  });

  it('4. Renders structured StudyPlan card when plan artifact is returned', async () => {
    const user = userEvent.setup();
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      conversation_id: 'conv-003',
      message: {
        id: 'msg-3',
        role: 'assistant',
        content: 'Here is your personalized weekly schedule!',
        created_at: new Date().toISOString(),
      },
      study_plan: {
        title: 'Weekly Success Plan: Data Structures',
        week_start: '2026-08-15',
        goals: ['Master tree traversals', 'Complete Assignment 2'],
        tasks: [
          {
            task_id: 't-1',
            title: 'Tree Traversal Practice',
            day: 'Monday',
            time_slot: '10:00–11:30',
            subject: 'Data Structures',
            duration_minutes: 90,
            priority: 'high',
            completed: false,
          },
        ],
        resources: ['Textbook Chapter 4'],
        notes: 'Take breaks and stay steady.',
      },
    });

    render(<App />);
    const textarea = screen.getByPlaceholderText(/Ask anything/i);

    await user.type(textarea, 'Make me a study plan{enter}');

    await waitFor(() => {
      expect(screen.getByTestId('study-plan-card')).toBeInTheDocument();
      expect(screen.getByText('Weekly Success Plan: Data Structures')).toBeInTheDocument();
      expect(screen.getByText('Tree Traversal Practice')).toBeInTheDocument();
      expect(screen.getByText('Master tree traversals')).toBeInTheDocument();
      expect(screen.getByText('Textbook Chapter 4')).toBeInTheDocument();
    });
  });

  it('5. Allows checking off tasks inside the StudyPlan card', async () => {
    const user = userEvent.setup();
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      conversation_id: 'conv-004',
      message: {
        id: 'msg-4',
        role: 'assistant',
        content: 'Plan ready!',
        created_at: new Date().toISOString(),
      },
      study_plan: {
        title: 'Quick Plan',
        week_start: '2026-08-15',
        goals: ['Goal 1'],
        tasks: [
          {
            task_id: 't-chk',
            title: 'Binary Search Practice',
            day: 'Monday',
            time_slot: '10:00',
            subject: 'Algorithms',
            duration_minutes: 45,
            priority: 'medium',
            completed: false,
          },
        ],
      },
    });

    render(<App />);
    await user.type(screen.getByPlaceholderText(/Ask anything/i), 'Give me a plan{enter}');

    await waitFor(() => {
      expect(screen.getByText('Binary Search Practice')).toBeInTheDocument();
    });

    const checkbox = screen.getByRole('checkbox', { name: /Mark Binary Search Practice as complete/i });
    expect(checkbox).not.toBeChecked();

    await user.click(checkbox);
    expect(checkbox).toBeChecked();
  });

  it('6. Shows error banner with retry option on API failure', async () => {
    const user = userEvent.setup();
    vi.mocked(chatApi.sendMessage).mockRejectedValueOnce(new Error('Network connection timeout.'));

    render(<App />);
    const textarea = screen.getByPlaceholderText(/Ask anything/i);

    await user.type(textarea, 'Help me please{enter}');

    await waitFor(() => {
      expect(screen.getByTestId('error-banner')).toBeInTheDocument();
      expect(screen.getByText(/Network connection timeout/i)).toBeInTheDocument();
    });

    // Retry should trigger second call
    vi.mocked(chatApi.sendMessage).mockResolvedValueOnce({
      conversation_id: 'conv-005',
      message: {
        id: 'msg-5',
        role: 'assistant',
        content: 'I am here now!',
        created_at: new Date().toISOString(),
      },
      study_plan: null,
    });

    const retryBtn = screen.getByText('Retry');
    await user.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByText('I am here now!')).toBeInTheDocument();
    });
  });

  it('7. "New Chat" resets conversation and clears messages', async () => {
    const user = userEvent.setup();
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      conversation_id: 'conv-006',
      message: {
        id: 'msg-6',
        role: 'assistant',
        content: 'First session reply',
        created_at: new Date().toISOString(),
      },
      study_plan: null,
    });

    render(<App />);
    await user.type(screen.getByPlaceholderText(/Ask anything/i), 'Hello{enter}');
    await waitFor(() => expect(screen.getByText('First session reply')).toBeInTheDocument());

    const newChatBtn = screen.getByTestId('new-chat-btn');
    await user.click(newChatBtn);

    // Empty state should be back
    expect(screen.getByTestId('chat-empty-state')).toBeInTheDocument();
    expect(screen.queryByText('First session reply')).not.toBeInTheDocument();
  });

  it('8. History drawer opens and displays past conversations', async () => {
    const user = userEvent.setup();
    render(<App />);

    const historyBtn = screen.getByTestId('history-drawer-btn');
    await user.click(historyBtn);

    expect(screen.getByTestId('history-drawer')).toBeInTheDocument();
    expect(screen.getByText('Midterm Prep')).toBeInTheDocument();
  });

  it('9. Never displays internal agent names or risk labels to student', async () => {
    const user = userEvent.setup();
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      conversation_id: 'conv-007',
      message: {
        id: 'msg-7',
        role: 'assistant',
        content: 'You have solid fundamentals in Operating Systems! Keep up the great work.',
        created_at: new Date().toISOString(),
      },
      study_plan: null,
      agents_used: ['student_insight', 'recovery_coach'],
    });

    render(<App />);
    await user.type(screen.getByPlaceholderText(/Ask anything/i), 'How am I doing?{enter}');

    await waitFor(() => {
      expect(screen.getByText(/You have solid fundamentals/i)).toBeInTheDocument();
    });

    const bodyText = document.body.textContent || '';
    expect(bodyText).not.toMatch(/student[- ]insight/i);
    expect(bodyText).not.toMatch(/recovery[- ]coach/i);
    expect(bodyText).not.toMatch(/study[- ]planner/i);
    expect(bodyText).not.toMatch(/at[- ]risk/i);
    expect(bodyText).not.toMatch(/high[- ]risk/i);
    expect(bodyText).not.toMatch(/failing student/i);
  });
});
