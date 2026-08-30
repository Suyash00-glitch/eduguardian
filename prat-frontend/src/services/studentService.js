import {
  demoStudent,
  demoGoals,
  demoDashboard,
  demoAttendance,
  demoAssignments,
  demoQuizResults,
  demoLmsActivity,
  demoInsights,
} from "./demoData";

const wait = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms));

/* =====================================================
   DEMO NOTIFICATIONS
   ===================================================== */

const demoNotifications = [
  {
    id: 1,
    title: "Assignment reminder",
    message: "Your AI assignment is due soon.",
    createdAt: "Today",
    read: false,
    type: "assignment",
  },
  {
    id: 2,
    title: "Academic update",
    message: "Your recent academic progress has been updated.",
    createdAt: "Yesterday",
    read: false,
    type: "academic",
  },
  {
    id: 3,
    title: "Recovery plan",
    message: "You have a new recommended action in your recovery plan.",
    createdAt: "2 days ago",
    read: false,
    type: "recovery",
  },
  {
    id: 4,
    title: "Quiz result",
    message: "Your latest quiz result has been recorded.",
    createdAt: "3 days ago",
    read: true,
    type: "quiz",
  },
];

const RAW_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
const API_URL = RAW_URL.endsWith("/api") ? RAW_URL.slice(0, -4) : RAW_URL;

export const studentService = {
  /* =====================================================
     PORTAL CONTEXT & RISK ENGINE INTEGRATION
     ===================================================== */

  async getPortalContext() {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token");

    let storedCtx = null;
    try {
      const rawStored =
        localStorage.getItem("eduguardian_student_context") ||
        sessionStorage.getItem("eduguardian_student_context");
      if (rawStored) {
        storedCtx = JSON.parse(rawStored);
      }
    } catch {
      // ignore
    }

    if (!token) return storedCtx;

    try {
      const res = await fetch(`${API_URL}/api/students/portal-context`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) {
        const liveCtx = await res.json();
        if (
          liveCtx &&
          (!liveCtx.historical_semesters || liveCtx.historical_semesters.length === 0) &&
          storedCtx?.historical_semesters?.length > 0
        ) {
          liveCtx.historical_semesters = storedCtx.historical_semesters;
          liveCtx.historical_academic_performance =
            storedCtx.historical_academic_performance || liveCtx.historical_academic_performance;
        }
        if (liveCtx) {
          try {
            localStorage.setItem("eduguardian_student_context", JSON.stringify(liveCtx));
          } catch {}
          return liveCtx;
        }
      }
    } catch {
      // fallback
    }
    return storedCtx;
  },

  async getRiskAnalysis() {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token");

    if (!token) return null;

    try {
      const res = await fetch(`${API_URL}/api/students/risk-analysis`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // fallback
    }
    return null;
  },

  /* =====================================================
     DASHBOARD
     ===================================================== */

  async getDashboard() {
    const ctx = await this.getPortalContext();
    if (ctx && ctx.data_source === "student_portal") {
      const att = ctx.attendance || {};
      const risk = ctx.risk_evaluation || {};
      const histPerf = ctx.historical_academic_performance || {};
      const histSems = ctx.historical_semesters || [];

      // Current attendance
      const attendanceStatus = att.status || "not_available";
      const attendanceValue = (attendanceStatus === "available" && att.value !== null) ? att.value : null;

      // Current assessment / IA
      const assessmentStatus = ctx.current_assessments?.status || "not_available";
      const assessmentValue = (assessmentStatus === "available" && ctx.current_assessments.value !== null) ? ctx.current_assessments.value : null;

      // Risk output from portal engine
      const riskLevel = risk.risk_level || "low";
      const riskConfidence = risk.confidence || "low";
      const riskStatus = risk.risk_status || "evaluated_historical";
      const recoveryProb = risk.recovery_probability ?? 85.0;
      const supportSignalStr = risk.support_signal || "Strong historical academic performance. Current-semester attendance and assessment data are pending.";

      return {
        data_source: "student_portal",
        // Current metrics
        attendance: {
          status: attendanceStatus,
          value: attendanceValue,
          classes_held: att.classes_held ?? null,
          classes_attended: att.classes_attended ?? null,
          note: attendanceStatus === "available" ? null : "Current semester attendance has not yet been published by faculty."
        },
        assessments: {
          status: assessmentStatus,
          value: assessmentValue,
          note: assessmentStatus === "available" ? null : "Current semester IA assessments have not yet been published."
        },
        assignments: {
          status: ctx.assignments?.status || "not_available",
          completed: null,
          total: null,
          missed: ctx.assignments?.missed_count ?? null,
          note: "Assignment tracking is not integrated into this portal."
        },
        lmsActivity: {
          status: ctx.lms_engagement?.status || "not_available",
          value: null,
          note: "LMS tracking is not integrated into this portal."
        },
        risk: {
          level: riskLevel,
          confidence: riskConfidence,
          status: riskStatus,
          recoveryProbability: recoveryProb,
          supportSignal: supportSignalStr,
          dataAvailable: {
            attendance: attendanceStatus === "available",
            assessments: assessmentStatus === "available",
            historical: histSems.length > 0
          }
        },
        // Historical performance
        historical_academic_performance: histPerf,
        historical_semesters: histSems,
        current_academic_profile: ctx.current_academic_profile || {},
        identity: ctx.identity || {},
        academic_guidance: ctx.academic_guidance || {}
      };
    }
    await wait();
    return demoDashboard;
  },

  /* =====================================================
     PROGRESS
     ===================================================== */

  async getProgress() {
    const ctx = await this.getPortalContext();
    if (ctx && ctx.data_source === "student_portal") {
      return {
        data_source: "student_portal",
        attendance:
          ctx.attendance?.status === "available"
            ? ctx.attendance
            : { status: "not_available", value: null },
        assignments: [],
        quizzes: [],
        lmsActivity: [],
        historical_semesters: ctx.historical_semesters || [],
        historical_academic_performance: ctx.historical_academic_performance || {},
        enrolled_subjects:
          ctx.current_academic_profile?.enrolled_subjects || [],
      };
    }
    await wait();
    return {
      attendance: demoAttendance,
      assignments: demoAssignments,
      quizzes: demoQuizResults,
      lmsActivity: demoLmsActivity,
    };
  },

  async getAttendance() {
    const ctx = await this.getPortalContext();
    if (ctx && ctx.data_source === "student_portal") {
      const att = ctx.attendance;
      if (att && att.status === "available" && Array.isArray(att.records) && att.records.length > 0) {
        return att.records.map((r) => {
          const rawSubcode = r.subject_code || r.subjectCode || r.fsubcode || r.code || "SUB";
          const rawSubname = r.subject_name || r.subjectName || r.fsubname || r.name || rawSubcode;
          let subCode = rawSubcode;
          let subName = rawSubname;

          if (rawSubname && rawSubname.includes(" - ")) {
            const parts = rawSubname.split(" - ");
            if (parts.length >= 2 && /\d/.test(parts[parts.length - 1])) {
              subCode = parts[parts.length - 1].trim();
              subName = parts.slice(0, -1).join(" - ").trim();
            }
          }

          const conducted = Number(r.conducted ?? r.classes_held ?? r.classesHeld ?? r.held ?? 20);
          const attended = Number(r.attended ?? r.classes_attended ?? r.classesAttended ?? 20);
          const percentage = Number(r.percentage ?? (conducted > 0 ? (attended / conducted * 100) : 100));

          return {
            subjectCode: subCode,
            subjectName: subName,
            classesHeld: conducted,
            classesAttended: attended,
            percentage: percentage,
          };
        });
      }
      // Check database attendance endpoint
      const token =
        localStorage.getItem("eduguardian_token") ||
        sessionStorage.getItem("eduguardian_token");
      if (token) {
        try {
          const res = await fetch(`${API_URL}/api/students/attendance`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (res.ok) {
            const data = await res.json();
            if (data?.attendance && Array.isArray(data.attendance) && data.attendance.length > 0) {
              return data.attendance;
            }
          }
        } catch {
          // ignore
        }
      }
      return [];
    }
    await wait();
    return demoAttendance;
  },

  /* =====================================================
     ASSIGNMENTS
     ===================================================== */

  async getAssignments() {
    const ctx = await this.getPortalContext();
    if (ctx && ctx.data_source === "student_portal") {
      return [];
    }
    await wait();
    return demoAssignments;
  },

  async getAssignment(id) {
    const ctx = await this.getPortalContext();
    if (ctx && ctx.data_source === "student_portal") {
      throw new Error("Assignments not integrated into University Student Portal.");
    }
    await wait();
    const assignment = demoAssignments.find(
      (item) => String(item.id) === String(id),
    );
    if (!assignment) {
      throw new Error("Assignment not found.");
    }
    return assignment;
  },

  /* =====================================================
     QUIZ RESULTS
     ===================================================== */

  async getQuizResults() {
    const ctx = await this.getPortalContext();
    if (ctx && ctx.data_source === "student_portal") {
      const assess = ctx.current_assessments;
      if (assess && assess.status === "available" && Array.isArray(assess.records)) {
        return assess.records;
      }
      return [];
    }
    await wait();
    return demoQuizResults;
  },

  /* =====================================================
     LMS ACTIVITY
     ===================================================== */

  async getLmsActivity() {
    const ctx = await this.getPortalContext();
    if (ctx && ctx.data_source === "student_portal") {
      return [];
    }
    await wait();
    return demoLmsActivity;
  },

  /* =====================================================
     INSIGHTS
     ===================================================== */

  async getInsights() {
    await wait();

    return demoInsights;
  },

  /* =====================================================
     PROFILE
     ===================================================== */

  async getStudent() {
    // Try real portal context first
    const ctx = await this.getPortalContext();
    if (ctx && ctx.data_source === "student_portal" && ctx.identity) {
      const id = ctx.identity;
      return {
        data_source: "student_portal",
        id: id.student_id || id.usn,
        name: id.name || "—",
        usn: id.usn || "—",
        email: "Not available from Student Portal",
        department: id.department || "—",
        degree: id.degree || "—",
        semester: id.semester || null,
        section: id.section || null,
        college: id.college || null,
      };
    }
    // Explicit demo fallback
    await wait();
    return demoStudent;
  },

  async updateProfile(data) {
    await wait(500);
    return {
      ...demoStudent,
      ...data,
    };
  },

  /* =====================================================
     GOALS (DYNAMIC API)
     ===================================================== */

  async getGoals() {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (token) {
      try {
        const res = await fetch(`${API_URL}/api/goals`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            return data;
          }
        }
      } catch (e) {
        console.warn("Failed to fetch goals from backend:", e);
      }
    }

    await wait();
    return demoGoals;
  },

  async createGoal(data) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (token) {
      try {
        const res = await fetch(`${API_URL}/api/goals`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            title: data.title,
            category: data.category || "Academic",
            target: data.target || "100%",
            due_date: data.due_date || null,
            milestones: data.milestones || [],
          }),
        });

        if (res.ok) {
          return await res.json();
        }
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create goal.");
      } catch (e) {
        console.warn("Backend createGoal error:", e);
        throw e;
      }
    }

    await wait(400);
    return {
      id: Date.now(),
      title: data.title,
      category: data.category || "Academic",
      target: data.target || "100%",
      progress: 0,
      status: "in-progress",
      milestones: data.milestones || [],
    };
  },

  async updateGoal(id, data) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (token) {
      const res = await fetch(`${API_URL}/api/goals/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });
      if (res.ok) {
        return await res.json();
      }
      const err = await res.json();
      throw new Error(err.detail || "Failed to update goal.");
    }
    return data;
  },

  async deleteGoal(id) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (token) {
      const res = await fetch(`${API_URL}/api/goals/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to delete goal.");
      }
      return true;
    }
    return true;
  },

  async toggleGoalMilestone(goalId, milestoneId) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (token) {
      const res = await fetch(`${API_URL}/api/goals/${goalId}/milestones/${milestoneId}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) {
        return await res.json();
      }
      const err = await res.json();
      throw new Error(err.detail || "Failed to toggle milestone.");
    }
    return null;
  },

  async addGoalMilestone(goalId, title) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (token) {
      const res = await fetch(`${API_URL}/api/goals/${goalId}/milestones`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ title }),
      });
      if (res.ok) {
        return await res.json();
      }
      const err = await res.json();
      throw new Error(err.detail || "Failed to add milestone.");
    }
    return null;
  },

  async deleteGoalMilestone(goalId, milestoneId) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (token) {
      const res = await fetch(`${API_URL}/api/goals/${goalId}/milestones/${milestoneId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) {
        return await res.json();
      }
      const err = await res.json();
      throw new Error(err.detail || "Failed to delete milestone.");
    }
    return null;
  },

  /* =====================================================
     STUDENT ASSIGNMENTS & SUBMISSIONS (REALTIME SYNC)
     ===================================================== */

  async getAssignments() {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (!token) {
      return demoAssignments || [];
    }

    try {
      const res = await fetch(`${API_URL}/api/assignments/student`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        throw new Error(`Failed to fetch assignments: ${res.status}`);
      }

      const data = await res.json();
      return data.assignments || [];
    } catch (err) {
      console.error("studentService.getAssignments error:", err);
      return demoAssignments || [];
    }
  },

  async getAssignment(assignmentId) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (!token) {
      const found = (demoAssignments || []).find((a) => String(a.id) === String(assignmentId));
      if (!found) throw new Error("Assignment not found");
      return found;
    }

    const res = await fetch(`${API_URL}/api/assignments/student/${assignmentId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Unable to load assignment details.");
    }

    return await res.json();
  },

  async submitAssignment(assignmentId, formData) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (!token) {
      throw new Error("Authentication required to submit assignments.");
    }

    const res = await fetch(`${API_URL}/api/assignments/student/${assignmentId}/submit`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to submit assignment.");
    }

    return await res.json();
  },

  /* =====================================================
     STUDENT SUPPORT & HELP DESK TICKETS
     ===================================================== */

  async getSupportTickets() {
    try {
      const token =
        localStorage.getItem("eduguardian_token") ||
        sessionStorage.getItem("eduguardian_token") ||
        localStorage.getItem("token");

      if (token) {
        const res = await fetch(`${API_URL}/api/feedback/my`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          return data.tickets || [];
        }
      }
    } catch (e) {
      console.warn("Could not fetch support tickets:", e);
    }
    return [];
  },

  async createSupportTicket(ticketData) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token");

    if (!token) throw new Error("Please log in to submit a support request.");

    const res = await fetch(`${API_URL}/api/feedback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(ticketData),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.message || "Failed to submit ticket.");
    return data;
  },

  /* =====================================================
     RESOURCES & MENTOR (DYNAMIC API)
     ===================================================== */

  async getResources() {
    try {
      const token =
        localStorage.getItem("eduguardian_token") ||
        sessionStorage.getItem("eduguardian_token") ||
        localStorage.getItem("token") ||
        localStorage.getItem("student_token");

      if (token) {
        const res = await fetch(`${API_URL}/api/interventions/resources`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const liveData = await res.json();
          if (Array.isArray(liveData) && liveData.length > 0) {
            return liveData;
          }
        }
      }
    } catch (e) {
      console.warn("Could not fetch backend student resources:", e);
    }

    await wait();

    return [
      {
        id: 1,
        title: "Data Communication and Networking - IP Subnetting & OSI Guide",
        description:
          "Comprehensive lecture notes covering OSI model, TCP/IP, IP addressing calculation, and packet routing.",
        category: "Academic",
        type: "PDF",
        teacher_name: "Dr. Ravi B",
        url: "https://en.wikipedia.org/wiki/Computer_network",
      },
      {
        id: 2,
        title: "Machine Learning Foundations - Lab Manual & Supervised Algorithms",
        description:
          "Jupyter notebooks and problem sets covering linear regression, SVM, decision trees, and gradient descent.",
        category: "Academic",
        type: "PDF",
        teacher_name: "Dr. Ramesh G",
        url: "https://en.wikipedia.org/wiki/Machine_learning",
      },
      {
        id: 3,
        title: "Operating Systems - Process Synchronization & Scheduling",
        description:
          "Practical guide with examples on Semaphores, Deadlock resolution, and Virtual Memory management.",
        category: "Guide",
        type: "Guide",
        teacher_name: "Ms. Prathyakshini",
        url: "https://en.wikipedia.org/wiki/Operating_system",
      },
      {
        id: 4,
        title: "Universal Human Values - Professional Ethics & Study Guide",
        description:
          "Course reading pack on self-exploration, professional ethics, and harmonious living guidelines.",
        category: "Academic",
        type: "PDF",
        teacher_name: "Dr. Preethi Salian K",
        url: "https://en.wikipedia.org/wiki/Ethics",
      },
      {
        id: 5,
        title: "Academic Recovery & Exam Prep Blueprint",
        description:
          "Structured 3-step active recall method, high-yield practice roadmap, and time management strategies.",
        category: "Remedial",
        type: "Guide",
        teacher_name: "Faculty Mentorship Cell",
        url: "https://en.wikipedia.org/wiki/Active_recall",
      },
    ];
  },

  async getMyMentor() {
    try {
      const token =
        localStorage.getItem("eduguardian_token") ||
        sessionStorage.getItem("eduguardian_token") ||
        localStorage.getItem("token") ||
        localStorage.getItem("student_token");

      if (token) {
        const res = await fetch(`${API_URL}/api/mentors/my-mentor`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          return data.mentor || null;
        }
      }
    } catch (e) {
      console.warn("Could not fetch student mentor:", e);
    }
    return null;
  },

  /* =====================================================
     RECOVERY & AI STUDY PLAN INTEGRATION
     ===================================================== */

  async getRecoveryPlan() {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token") ||
      localStorage.getItem("student_token");

    // 1. Try Backend API
    if (token) {
      try {
        const res = await fetch(`${API_URL}/api/recovery/plan`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const plan = await res.json();
          if (plan && plan.goals) {
            try {
              localStorage.setItem("eduguardian_recovery_plan", JSON.stringify(plan));
            } catch {}
            return plan;
          }
        }
      } catch (e) {
        console.warn("Could not fetch recovery plan from API, checking local store:", e);
      }
    }

    // 2. Try Local Storage Cache
    try {
      const stored = localStorage.getItem("eduguardian_recovery_plan");
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {}

    // 3. Generate fallback plan personalized to active context
    const ctx = await this.getPortalContext();
    const risk = ctx?.risk_evaluation?.risk_level || "low";
    const name = ctx?.identity?.name || "Student";

    const defaultGoals = [
      {
        id: "task-1",
        title: "Daily 45-min Active Recall & Problem-Solving Session",
        category: "Remediation",
        description: "Work through step-by-step solved examples from Unit 1 and Unit 2 in core subjects. Avoid passive re-reading.",
        dueDate: "In 2 days",
        completed: false,
        priority: "high",
        impact: "High Impact",
        timeEstimate: "45 mins/day",
        steps: [
          "Review key formulae and algorithm steps without looking at notes",
          "Attempt 2 previous exam problems per chapter",
          "Self-correct errors in a separate revision notebook"
        ]
      },
      {
        id: "task-2",
        title: "Continuous Internal Evaluation (CIE) Question Bank Drill",
        category: "Exam Prep",
        description: "Solve previous 3 semesters' CIE test papers for analytical and technical subjects with self-timed practice.",
        dueDate: "In 5 days",
        completed: false,
        priority: "high",
        impact: "High Impact",
        timeEstimate: "60 mins",
        steps: [
          "Complete 1 full mock module test under 45 minutes",
          "Cross-verify step scoring against textbook solutions",
          "Review tricky theoretical derivations"
        ]
      },
      {
        id: "task-3",
        title: "Attendance & Classroom Participation Stabilization",
        category: "Attendance",
        description: "Maintain 100% attendance across all upcoming lecture and lab hours to meet the university 75% examination eligibility standard.",
        dueDate: "Next week",
        completed: false,
        priority: "critical",
        impact: "Mandatory Requirement",
        timeEstimate: "Daily",
        steps: [
          "Attend all scheduled morning theory sessions punctually",
          "Submit lab observation records at the end of each session",
          "Verify weekly portal attendance logs with class advisor"
        ]
      },
      {
        id: "task-4",
        title: "Faculty Mentor 1-on-1 Concept Review Session",
        category: "Mentorship",
        description: "Schedule a 15-minute consultation with your faculty mentor to clarify doubt topics and review your progress roadmap.",
        dueDate: "In 2 weeks",
        completed: false,
        priority: "medium",
        impact: "Medium Impact",
        timeEstimate: "15 mins",
        steps: [
          "Compile a list of 3-5 specific doubt concepts",
          "Share your weekly practice log with your mentor",
          "Get feedback on internal marks improvement strategy"
        ]
      }
    ];

    const fallbackPlan = {
      title: risk === "high"
        ? "Personalized Academic Recovery & Remediation Blueprint"
        : "Structured Academic Strengthening & Exam Readiness Plan",
      summary: `Tailored study and recovery milestones for ${name} to maintain steady academic growth and achieve exam readiness.`,
      progress: 0,
      goals: defaultGoals,
      generated_by: "EduGuardian AI Academic Coach",
      last_updated: new Date().toISOString()
    };

    try {
      localStorage.setItem("eduguardian_recovery_plan", JSON.stringify(fallbackPlan));
    } catch {}

    return fallbackPlan;
  },

  async toggleRecoveryTask(taskId) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token") ||
      localStorage.getItem("student_token");

    if (token) {
      try {
        const res = await fetch(`${API_URL}/api/recovery/tasks/${encodeURIComponent(taskId)}/toggle`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const updated = await res.json();
          try {
            localStorage.setItem("eduguardian_recovery_plan", JSON.stringify(updated));
          } catch {}
          return updated;
        }
      } catch (e) {
        console.warn("Could not toggle task via API, using local storage:", e);
      }
    }

    // Local Storage fallback
    const plan = await this.getRecoveryPlan();
    const goals = plan.goals || [];
    for (const g of goals) {
      if (String(g.id) === String(taskId)) {
        g.completed = !g.completed;
        break;
      }
    }
    const completed = goals.filter((g) => g.completed).length;
    plan.progress = goals.length > 0 ? Math.round((completed / goals.length) * 100) : 0;
    try {
      localStorage.setItem("eduguardian_recovery_plan", JSON.stringify(plan));
    } catch {}
    return plan;
  },

  async syncAiStudyPlan(aiPlanData) {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token") ||
      localStorage.getItem("student_token");

    if (token) {
      try {
        const res = await fetch(`${API_URL}/api/recovery/ai-sync`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(aiPlanData)
        });
        if (res.ok) {
          const updated = await res.json();
          try {
            localStorage.setItem("eduguardian_recovery_plan", JSON.stringify(updated));
          } catch {}
          // Dispatch local event so any open tab/page updates live
          window.dispatchEvent(new CustomEvent("eduguardian_recovery_plan_updated", { detail: updated }));
          return updated;
        }
      } catch (e) {
        console.warn("Could not sync AI plan via API:", e);
      }
    }

    // Local Storage sync
    const current = await this.getRecoveryPlan();
    if (aiPlanData.goals && Array.isArray(aiPlanData.goals)) {
      current.goals = aiPlanData.goals;
      if (aiPlanData.title) current.title = aiPlanData.title;
      if (aiPlanData.summary) current.summary = aiPlanData.summary;
    } else if (aiPlanData.tasks || aiPlanData.milestones) {
      const tasks = aiPlanData.tasks || aiPlanData.milestones || [];
      const newGoals = tasks.map((t, idx) => {
        if (typeof t === "string") {
          return {
            id: `ai-task-${Date.now()}-${idx}`,
            title: t,
            category: "AI Study Goal",
            description: `AI recommended milestone: ${t}`,
            dueDate: `In ${idx + 2} days`,
            completed: false,
            priority: "high",
            impact: "High Impact",
            timeEstimate: "45 mins",
            steps: ["Focus study session", "Complete practical problems"]
          };
        }
        return {
          id: t.id || `ai-task-${Date.now()}-${idx}`,
          title: t.title || t.subject || "Study Session",
          category: t.category || "AI Study Goal",
          description: t.description || t.notes || "AI recommended study focus area.",
          dueDate: t.dueDate || `In ${idx + 2} days`,
          completed: Boolean(t.completed),
          priority: t.priority || "high",
          impact: t.impact || "High Impact",
          timeEstimate: t.timeEstimate || "45 mins",
          steps: t.steps || ["Review core concepts", "Complete exercises"]
        };
      });
      current.goals = [...(current.goals || []), ...newGoals];
    }
    const completed = current.goals.filter((g) => g.completed).length;
    current.progress = current.goals.length > 0 ? Math.round((completed / current.goals.length) * 100) : 0;
    try {
      localStorage.setItem("eduguardian_recovery_plan", JSON.stringify(current));
    } catch {}
    window.dispatchEvent(new CustomEvent("eduguardian_recovery_plan_updated", { detail: current }));
    return current;
  },

  async generateAiRecoveryPlan(prompt = "") {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token") ||
      localStorage.getItem("token") ||
      localStorage.getItem("student_token");

    if (token) {
      try {
        const res = await fetch(`${API_URL}/api/recovery/ai-generate`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ prompt })
        });
        if (res.ok) {
          const fresh = await res.json();
          try {
            localStorage.setItem("eduguardian_recovery_plan", JSON.stringify(fresh));
          } catch {}
          window.dispatchEvent(new CustomEvent("eduguardian_recovery_plan_updated", { detail: fresh }));
          return fresh;
        }
      } catch (e) {
        console.warn("Could not generate AI plan via API:", e);
      }
    }
    return this.getRecoveryPlan();
  },

  /* =====================================================
     NOTIFICATIONS
     ===================================================== */

  async getNotifications() {
    await wait();

    // Return a new array so the UI cannot accidentally
    // modify the original demo data.
    return demoNotifications.map((notification) => ({
      ...notification,
    }));
  },

  async markNotificationRead(id) {
    await wait(200);

    const notification = demoNotifications.find(
      (item) => String(item.id) === String(id),
    );

    if (!notification) {
      throw new Error("Notification not found.");
    }

    notification.read = true;

    return {
      success: true,
      id,
    };
  },
};
