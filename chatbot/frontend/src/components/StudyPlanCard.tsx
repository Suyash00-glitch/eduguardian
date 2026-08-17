import React, { useEffect } from 'react';
import type { StudyPlan } from '../types';
import './StudyPlanCard.css';

const PRIORITY_COLORS: Record<string, string> = {
  high: 'priority-high',
  medium: 'priority-medium',
  low: 'priority-low',
};

interface Props {
  plan: StudyPlan;
  onClose: () => void;
  onToggleTask?: (taskKey: string) => void;
}

export const StudyPlanCard: React.FC<Props> = ({ plan, onClose, onToggleTask }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const tasksByDay = (plan.tasks || []).reduce<Record<string, typeof plan.tasks>>((acc, task) => {
    const day = task.day || 'General';
    if (!acc[day]) acc[day] = [];
    acc[day].push(task);
    return acc;
  }, {});

  const totalMinutes = (plan.tasks || []).reduce((sum, t) => sum + (t.duration_minutes || 0), 0);
  const completedCount = (plan.tasks || []).filter(t => t.completed).length;
  const totalTasks = (plan.tasks || []).length;

  return (
    <div
      className="plan-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Your Study Plan"
      data-testid="study-plan-card"
      onClick={onClose}
    >
      <div className="plan-card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="plan-header">
          <div className="plan-header-left">
            <div className="plan-icon">📚</div>
            <div>
              <h2 className="plan-title">{plan.title || 'Personalized Study Plan'}</h2>
              <div className="plan-meta-row">
                <span className="plan-week">Week of {plan.week_start ? new Date(plan.week_start).toLocaleDateString() : 'This Week'}</span>
                <span className="plan-meta-divider">•</span>
                <span className="plan-duration-total">⏱ {totalMinutes} mins total</span>
                {totalTasks > 0 && (
                  <>
                    <span className="plan-meta-divider">•</span>
                    <span className="plan-progress-pill">{completedCount}/{totalTasks} Completed</span>
                  </>
                )}
              </div>
            </div>
          </div>
          <button className="plan-close" onClick={onClose} aria-label="Close study plan">✕</button>
        </div>

        {/* Goals */}
        {plan.goals && plan.goals.length > 0 && (
          <div className="plan-section">
            <h3 className="plan-section-title">🎯 Weekly Goals</h3>
            <ul className="plan-goals">
              {plan.goals.map((goal, i) => (
                <li key={i} className="plan-goal">{goal}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Schedule */}
        <div className="plan-section">
          <h3 className="plan-section-title">📅 Your Schedule</h3>
          <div className="plan-days">
            {Object.entries(tasksByDay).map(([day, tasks]) => (
              <div key={day} className="plan-day">
                <h4 className="plan-day-name">{day}</h4>
                {tasks.map((task, i) => {
                  const taskKey = task.task_id || task.title || task.activity || `${day}-${i}`;
                  const taskTitle = task.title || task.activity || 'Study Session';
                  const isDone = !!task.completed;

                  const taskSubject = task.subject && task.subject.trim() !== '' && task.subject.toLowerCase() !== 'none' && task.subject.toLowerCase() !== 'null' ? task.subject : 'General Study';

                  return (
                    <div
                      key={taskKey}
                      className={`plan-task ${isDone ? 'task-completed' : ''}`}
                      onClick={() => onToggleTask?.(taskKey)}
                      tabIndex={0}
                    >
                      <div className="plan-task-checkbox" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isDone}
                          onChange={() => onToggleTask?.(taskKey)}
                          aria-label={`Mark ${taskTitle} as complete`}
                        />
                      </div>
                      <div className="plan-task-body">
                        <div className="plan-task-header">
                          <span className="plan-task-time">{task.time_slot || `${task.duration_minutes} min`}</span>
                          <span className={`plan-task-priority ${PRIORITY_COLORS[task.priority] || 'priority-medium'}`}>
                            {task.priority || 'medium'}
                          </span>
                        </div>
                        <p className="plan-task-subject">{taskSubject}</p>
                        <p className={`plan-task-activity ${isDone ? 'strikethrough' : ''}`}>{taskTitle}</p>
                        {task.description && <p className="plan-task-description">{task.description}</p>}
                        <p className="plan-task-duration">⏱ {task.duration_minutes} min</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Resources */}
        {plan.resources && plan.resources.length > 0 && (
          <div className="plan-section">
            <h3 className="plan-section-title">🔗 Recommended Resources</h3>
            <ul className="plan-resources">
              {plan.resources.map((r, i) => (
                <li key={i} className="plan-resource">{r}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Notes */}
        {plan.notes && (
          <div className="plan-section plan-notes-section">
            <h3 className="plan-section-title">💡 Coach's Note</h3>
            <p className="plan-notes">{plan.notes}</p>
          </div>
        )}
      </div>
    </div>
  );
};
