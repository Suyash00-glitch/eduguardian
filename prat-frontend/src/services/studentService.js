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

    if (!token) return null;

    try {
      const res = await fetch(`${API_URL}/api/students/portal-context`, {
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
          note: assessmentStatus === "available" ? null : "Current semester assessment records have not yet been published."
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
        // Historical performance metrics (authoritative from semesters 1-4)
        historical_academic_performance: {
          cgpa: histPerf.cgpa ?? null,
          latest_sgpa: histPerf.latest_sgpa ?? null,
          sgpa_trend: histPerf.sgpa_trend || "insufficient_data",
          completed_semesters: histPerf.total_semesters_completed || histSems.length,
          arrears_count: histPerf.arrears_count ?? 0,
          total_credits_earned: histPerf.total_credits_earned ?? null,
        },
        // Risk & Outlook presentation
        risk: {
          level: riskLevel,
          confidence: riskConfidence,
          status: riskStatus,
          basis: "Historical academic performance",
          reason: "Current-semester attendance and assessment records are not yet available. Risk is currently estimated from historical academic performance.",
          recoveryProbability: recoveryProb,
        },
        supportSignal: {
          status: riskLevel.toUpperCase() + " RISK",
          message: supportSignalStr,
          confidence: riskConfidence,
        },
        // Student Context
        identity: ctx.identity || {},
        historical_semesters: histSems,
        enrolled_subjects: ctx.current_academic_profile?.enrolled_subjects || [],
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
      if (att && att.status === "available" && Array.isArray(att.records)) {
        return att.records;
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
     GOALS
     ===================================================== */

  async getGoals() {
    await wait();

    return demoGoals;
  },

  async createGoal(data) {
    await wait(400);

    return {
      id: Date.now(),
      title: data.title,
      target: data.target,
      progress: 0,
      status: "in-progress",
    };
  },

  /* =====================================================
     RESOURCES & MENTOR
     ===================================================== */

  async getResources() {
    try {
      const token = localStorage.getItem("token") || localStorage.getItem("student_token");
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
        title: "Database Management Systems",
        description:
          "Learning resources for DBMS concepts, SQL and database design.",
        category: "Academic",
        type: "PDF",
      },
      {
        id: 2,
        title: "Computer Networks",
        description:
          "Study material covering networking concepts and protocols.",
        category: "Academic",
        type: "PDF",
      },
      {
        id: 3,
        title: "Software Engineering",
        description:
          "Resources covering software development methodologies and practices.",
        category: "Academic",
        type: "PDF",
      },
      {
        id: 4,
        title: "Artificial Intelligence",
        description: "Resources for AI algorithms, search and problem solving.",
        category: "Academic",
        type: "PDF",
      },
      {
        id: 5,
        title: "Academic Study Guide",
        description:
          "Practical tips for improving study habits and academic performance.",
        category: "Guidance",
        type: "Guide",
      },
    ];
  },

  async getMyMentor() {
    try {
      const token = localStorage.getItem("token") || localStorage.getItem("student_token");
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
