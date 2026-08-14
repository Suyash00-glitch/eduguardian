import React from "react";

import {
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  AlertCircle,
  CalendarDays,
  TrendingUp,
  BookOpen,
  Activity,
  Target,
  Sparkles,
  ChevronRight,
} from "lucide-react";

const stats = [
  {
    label: "Attendance",
    value: "84.6%",
    change: "+3.2%",
    icon: CalendarDays,
  },
  {
    label: "Assignments",
    value: "91%",
    change: "+8%",
    icon: CheckCircle2,
  },
  {
    label: "Quiz Average",
    value: "78%",
    change: "+4.5%",
    icon: BookOpen,
  },
  {
    label: "LMS Engagement",
    value: "74%",
    change: "+11%",
    icon: Activity,
  },
];

const attentionItems = [
  {
    type: "assignment",
    title: "Normalization Assignment",
    subtitle: "Database Management Systems",
    detail: "Due tomorrow",
    icon: Clock3,
  },
  {
    type: "attendance",
    title: "Operating Systems attendance",
    subtitle: "Your attendance is below your target",
    detail: "77.5%",
    icon: AlertCircle,
  },
  {
    type: "quiz",
    title: "Computer Networks Quiz",
    subtitle: "Revision recommended",
    detail: "Friday",
    icon: BookOpen,
  },
];

const tasks = [
  {
    title: "Complete DBMS Assignment",
    subject: "Database Management Systems",
    due: "Tomorrow",
    progress: 0,
  },
  {
    title: "Revise OS scheduling",
    subject: "Operating Systems",
    due: "Thursday",
    progress: 50,
  },
  {
    title: "Complete CN Quiz",
    subject: "Computer Networks",
    due: "Friday",
    progress: 0,
  },
];

function Dashboard() {
  return (
    <div className="dashboard">
      <section className="dashboard-welcome">
        <div>
          <div className="welcome-label">
            <Sparkles size={14} />
            STUDENT SUCCESS
          </div>

          <h2>Good evening, Pratham.</h2>

          <p>
            You're making steady progress. Here's what you can focus on today.
          </p>
        </div>

        <div className="dashboard-date">
          <CalendarDays size={15} />
          <span>Thursday, August 14</span>
        </div>
      </section>

      <section className="dashboard-section">
        <div className="section-heading">
          <div>
            <h3>Academic overview</h3>
            <p>Your latest academic activity</p>
          </div>

          <button className="text-button">
            View progress
            <ChevronRight size={15} />
          </button>
        </div>

        <div className="stats-grid">
          {stats.map((stat) => {
            const Icon = stat.icon;

            return (
              <div className="stat-card" key={stat.label}>
                <div className="stat-card-top">
                  <div className="stat-icon">
                    <Icon size={18} />
                  </div>

                  <div className="stat-change positive">
                    <ArrowUpRight size={13} />
                    {stat.change}
                  </div>
                </div>

                <div className="stat-value">{stat.value}</div>

                <div className="stat-label">{stat.label}</div>

                <div className="mini-bar">
                  <span
                    style={{
                      width:
                        stat.label === "Attendance"
                          ? "84.6%"
                          : stat.label === "Assignments"
                            ? "91%"
                            : stat.label === "Quiz Average"
                              ? "78%"
                              : "74%",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="dashboard-main-grid">
        <div className="dashboard-card recovery-card">
          <div className="card-heading">
            <div>
              <h3>Recovery probability</h3>
              <p>Your current recovery potential</p>
            </div>

            <div className="card-icon green">
              <TrendingUp size={18} />
            </div>
          </div>

          <div className="recovery-content">
            <div className="recovery-score">
              <div className="score-ring">
                <svg viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="50" className="ring-background" />

                  <circle cx="60" cy="60" r="50" className="ring-progress" />
                </svg>

                <div className="score-value">
                  <strong>86</strong>
                  <span>%</span>
                </div>
              </div>

              <div className="score-info">
                <strong>Strong recovery potential</strong>

                <span>+12% from the previous assessment</span>
              </div>
            </div>

            <div className="recovery-message">
              <div className="message-icon">
                <Sparkles size={15} />
              </div>

              <p>
                Your recent activity is improving. Staying consistent with your
                recovery plan could help maintain this positive trend.
              </p>
            </div>
          </div>

          <button className="card-action">
            View recovery insights
            <ChevronRight size={15} />
          </button>
        </div>

        <div className="dashboard-card weekly-card">
          <div className="card-heading">
            <div>
              <h3>This week's progress</h3>
              <p>Your recovery plan activity</p>
            </div>

            <div className="card-icon">
              <Target size={18} />
            </div>
          </div>

          <div className="weekly-progress">
            <div className="weekly-number">
              <strong>3</strong>
              <span>/ 5 goals completed</span>
            </div>

            <div className="large-progress">
              <span style={{ width: "60%" }} />
            </div>

            <div className="progress-meta">
              <span>60% complete</span>
              <span>2 remaining</span>
            </div>
          </div>

          <div className="weekly-tasks">
            <div className="small-task completed">
              <CheckCircle2 size={15} />
              <span>Attend scheduled lectures</span>
            </div>

            <div className="small-task completed">
              <CheckCircle2 size={15} />
              <span>Complete OS revision</span>
            </div>

            <div className="small-task completed">
              <CheckCircle2 size={15} />
              <span>Review quiz mistakes</span>
            </div>

            <div className="small-task">
              <span className="task-circle" />
              <span>Complete DBMS assignment</span>
            </div>
          </div>

          <button className="card-action">
            Open recovery plan
            <ChevronRight size={15} />
          </button>
        </div>
      </section>

      <section className="dashboard-lower-grid">
        <div className="dashboard-card">
          <div className="card-heading">
            <div>
              <h3>What needs attention?</h3>
              <p>A few things worth focusing on</p>
            </div>
          </div>

          <div className="attention-list">
            {attentionItems.map((item) => {
              const Icon = item.icon;

              return (
                <div className="attention-item" key={item.title}>
                  <div className={`attention-icon ${item.type}`}>
                    <Icon size={17} />
                  </div>

                  <div className="attention-content">
                    <strong>{item.title}</strong>
                    <span>{item.subtitle}</span>
                  </div>

                  <div className="attention-detail">{item.detail}</div>

                  <ChevronRight size={15} className="attention-arrow" />
                </div>
              );
            })}
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-heading">
            <div>
              <h3>Recent activity</h3>
              <p>Your latest academic activity</p>
            </div>

            <Activity size={18} className="heading-muted" />
          </div>

          <div className="activity-list">
            <div className="activity-item">
              <div className="activity-dot success" />

              <div>
                <strong>Assignment submitted</strong>
                <span>Operating Systems · 2 hours ago</span>
              </div>

              <span className="activity-score">18/20</span>
            </div>

            <div className="activity-item">
              <div className="activity-dot green" />

              <div>
                <strong>LMS engagement increased</strong>
                <span>+18% this week · Yesterday</span>
              </div>
            </div>

            <div className="activity-item">
              <div className="activity-dot blue" />

              <div>
                <strong>Quiz completed</strong>
                <span>Computer Networks · Yesterday</span>
              </div>

              <span className="activity-score">16/20</span>
            </div>

            <div className="activity-item">
              <div className="activity-dot purple" />

              <div>
                <strong>Recovery plan updated</strong>
                <span>3 new tasks · 2 days ago</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="dashboard-card tasks-card">
        <div className="card-heading">
          <div>
            <h3>Next steps</h3>
            <p>Recommended actions from your recovery plan</p>
          </div>

          <button className="text-button">
            View all
            <ChevronRight size={15} />
          </button>
        </div>

        <div className="tasks-table">
          {tasks.map((task) => (
            <div className="dashboard-task" key={task.title}>
              <div className="task-check">
                {task.progress === 100 && <CheckCircle2 size={17} />}
              </div>

              <div className="task-info">
                <strong>{task.title}</strong>
                <span>{task.subject}</span>
              </div>

              <div className="task-progress">
                <div className="task-progress-bar">
                  <span
                    style={{
                      width: `${task.progress}%`,
                    }}
                  />
                </div>

                <span>{task.progress}%</span>
              </div>

              <div className="task-due">{task.due}</div>

              <ChevronRight size={15} className="task-arrow" />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
