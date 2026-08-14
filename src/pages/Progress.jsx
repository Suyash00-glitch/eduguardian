import React from "react";
import {
  TrendingUp,
  TrendingDown,
  CalendarDays,
  CheckCircle2,
  BookOpen,
  Activity,
  Target,
} from "lucide-react";

const attendanceData = [
  { week: "W1", value: 78 },
  { week: "W2", value: 76 },
  { week: "W3", value: 75 },
  { week: "W4", value: 79 },
  { week: "W5", value: 81 },
  { week: "W6", value: 82 },
  { week: "W7", value: 84 },
  { week: "W8", value: 85 },
];

const quizData = [
  { week: "W1", value: 68 },
  { week: "W2", value: 72 },
  { week: "W3", value: 69 },
  { week: "W4", value: 74 },
  { week: "W5", value: 76 },
  { week: "W6", value: 73 },
  { week: "W7", value: 77 },
  { week: "W8", value: 78 },
];

const lmsData = [
  { week: "W1", value: 52 },
  { week: "W2", value: 48 },
  { week: "W3", value: 44 },
  { week: "W4", value: 51 },
  { week: "W5", value: 59 },
  { week: "W6", value: 64 },
  { week: "W7", value: 69 },
  { week: "W8", value: 74 },
];

const subjects = [
  {
    name: "Database Management Systems",
    code: "CS401",
    score: 86,
    attendance: 85.7,
    trend: "up",
  },
  {
    name: "Operating Systems",
    code: "CS402",
    score: 74,
    attendance: 77.5,
    trend: "up",
  },
  {
    name: "Computer Networks",
    code: "CS403",
    score: 81,
    attendance: 92.1,
    trend: "up",
  },
  {
    name: "Software Engineering",
    code: "CS404",
    score: 79,
    attendance: 88.4,
    trend: "down",
  },
];

function Progress() {
  return (
    <div className="progress-page">
      {/* Header */}
      <section className="progress-intro">
        <div>
          <div className="progress-label">
            <TrendingUp size={14} />
            ACADEMIC JOURNEY
          </div>

          <h2>Your progress at a glance.</h2>

          <p>Track how your academic activity is changing over time.</p>
        </div>

        <button className="period-button">
          <CalendarDays size={15} />
          Last 8 weeks
        </button>
      </section>

      {/* Summary */}
      <section className="progress-summary">
        <div className="progress-summary-card">
          <div className="progress-summary-icon">
            <Target size={18} />
          </div>

          <div>
            <span>Overall performance</span>
            <strong>82%</strong>
          </div>

          <div className="progress-change">
            <TrendingUp size={13} />
            +6.4%
          </div>
        </div>

        <div className="progress-summary-card">
          <div className="progress-summary-icon">
            <CalendarDays size={18} />
          </div>

          <div>
            <span>Attendance</span>
            <strong>84.6%</strong>
          </div>

          <div className="progress-change">
            <TrendingUp size={13} />
            +3.2%
          </div>
        </div>

        <div className="progress-summary-card">
          <div className="progress-summary-icon">
            <BookOpen size={18} />
          </div>

          <div>
            <span>Quiz average</span>
            <strong>78%</strong>
          </div>

          <div className="progress-change">
            <TrendingUp size={13} />
            +4.5%
          </div>
        </div>

        <div className="progress-summary-card">
          <div className="progress-summary-icon">
            <Activity size={18} />
          </div>

          <div>
            <span>LMS engagement</span>
            <strong>74%</strong>
          </div>

          <div className="progress-change">
            <TrendingUp size={13} />
            +11%
          </div>
        </div>
      </section>

      {/* Charts */}
      <section className="progress-charts">
        <ProgressChart
          title="Attendance trend"
          subtitle="Weekly attendance percentage"
          data={attendanceData}
          suffix="%"
          colorClass="chart-green"
        />

        <ProgressChart
          title="Quiz performance"
          subtitle="Average weekly quiz score"
          data={quizData}
          suffix="%"
          colorClass="chart-green"
        />

        <ProgressChart
          title="LMS engagement"
          subtitle="Learning activity over time"
          data={lmsData}
          suffix="%"
          colorClass="chart-green"
        />
      </section>

      {/* Subject performance */}
      <section className="progress-card">
        <div className="progress-card-heading">
          <div>
            <h3>Subject performance</h3>
            <p>Current performance across your subjects</p>
          </div>
        </div>

        <div className="subject-list">
          {subjects.map((subject) => (
            <div className="subject-row" key={subject.code}>
              <div className="subject-name">
                <div className="subject-code">{subject.code}</div>

                <div>
                  <strong>{subject.name}</strong>
                  <span>Attendance {subject.attendance}%</span>
                </div>
              </div>

              <div className="subject-progress">
                <div className="subject-progress-bar">
                  <span
                    style={{
                      width: `${subject.score}%`,
                    }}
                  />
                </div>

                <strong>{subject.score}%</strong>
              </div>

              <div
                className={`subject-trend ${
                  subject.trend === "up" ? "trend-up" : "trend-down"
                }`}
              >
                {subject.trend === "up" ? (
                  <TrendingUp size={14} />
                ) : (
                  <TrendingDown size={14} />
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Improvements */}
      <section className="progress-insights-grid">
        <div className="progress-card">
          <div className="progress-card-heading">
            <div>
              <h3>What's improving</h3>
              <p>Positive changes in recent weeks</p>
            </div>

            <CheckCircle2 size={18} className="heading-success" />
          </div>

          <div className="improvement-list">
            <div className="improvement-item">
              <span className="improvement-dot" />

              <div>
                <strong>LMS engagement</strong>
                <span>Increased by 11% over the last 4 weeks.</span>
              </div>

              <b>+11%</b>
            </div>

            <div className="improvement-item">
              <span className="improvement-dot" />

              <div>
                <strong>Attendance</strong>
                <span>Improved steadily since week 4.</span>
              </div>

              <b>+6%</b>
            </div>

            <div className="improvement-item">
              <span className="improvement-dot" />

              <div>
                <strong>Quiz performance</strong>
                <span>Your average has increased this month.</span>
              </div>

              <b>+4.5%</b>
            </div>
          </div>
        </div>

        <div className="progress-card">
          <div className="progress-card-heading">
            <div>
              <h3>Area to watch</h3>
              <p>Something worth paying attention to</p>
            </div>

            <TrendingDown size={18} className="heading-warning" />
          </div>

          <div className="watch-area">
            <div className="watch-icon">
              <CalendarDays size={20} />
            </div>

            <div>
              <strong>Operating Systems attendance</strong>

              <p>
                Your attendance is currently 77.5%. Attending upcoming lectures
                could help bring this closer to your 85% target.
              </p>

              <div className="watch-progress">
                <span style={{ width: "77.5%" }} />
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function ProgressChart({ title, subtitle, data, suffix, colorClass }) {
  const max = 100;
  const min = 0;

  const points = data
    .map((item, index) => {
      const x = (index / (data.length - 1)) * 100;

      const y = 100 - ((item.value - min) / (max - min)) * 100;

      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="progress-card chart-card">
      <div className="progress-card-heading">
        <div>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>

        <span className="chart-current">
          {data[data.length - 1].value}
          {suffix}
        </span>
      </div>

      <div className="chart-wrapper">
        <div className="chart-y-axis">
          <span>100</span>
          <span>75</span>
          <span>50</span>
          <span>25</span>
          <span>0</span>
        </div>

        <div className="chart-area">
          <div className="chart-grid-lines">
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>

          <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            className={`line-chart ${colorClass}`}
          >
            <polyline
              points={points}
              fill="none"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
            />

            {data.map((item, index) => {
              const x = (index / (data.length - 1)) * 100;

              const y = 100 - (item.value / 100) * 100;

              return (
                <circle
                  key={item.week}
                  cx={x}
                  cy={y}
                  r="1.5"
                  vectorEffect="non-scaling-stroke"
                />
              );
            })}
          </svg>

          <div className="chart-labels">
            {data.map((item) => (
              <span key={item.week}>{item.week}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Progress;
