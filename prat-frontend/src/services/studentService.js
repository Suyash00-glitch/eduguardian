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

export const studentService = {
  /* =====================================================
     DASHBOARD
     ===================================================== */

  async getDashboard() {
    await wait();

    return demoDashboard;
  },

  /* =====================================================
     PROGRESS
     ===================================================== */

  async getProgress() {
    await wait();

    return {
      attendance: demoAttendance,
      assignments: demoAssignments,
      quizzes: demoQuizResults,
      lmsActivity: demoLmsActivity,
    };
  },

  async getAttendance() {
    await wait();

    return demoAttendance;
  },

  /* =====================================================
     ASSIGNMENTS
     ===================================================== */

  async getAssignments() {
    await wait();

    return demoAssignments;
  },

  async getAssignment(id) {
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
    await wait();

    return demoQuizResults;
  },

  /* =====================================================
     LMS ACTIVITY
     ===================================================== */

  async getLmsActivity() {
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
     RESOURCES
     ===================================================== */

  async getResources() {
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
