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

export const studentService = {
  // DASHBOARD
  async getDashboard() {
    await wait();
    return {
      student: demoStudent,
      ...demoDashboard,
    };
  },

  // PROGRESS
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

  async getAssignments() {
    await wait();
    return demoAssignments;
  },

  async getQuizResults() {
    await wait();
    return demoQuizResults;
  },

  async getLmsActivity() {
    await wait();
    return demoLmsActivity;
  },

  // INSIGHTS
  async getInsights() {
    await wait();
    return demoInsights;
  },

  // PROFILE
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

  // GOALS
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

  

    // RESOURCES
  async getResources() {
    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token");

    const response = await fetch(
      "http://localhost:8000/api/interventions/resources",
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Unable to load resources."
      );
    }

    return data;
  },









  // NOTIFICATIONS
  async getNotifications() {
    await wait();

    return [
      {
        id: 1,
        title: "Assignment reminder",
        message: "Your AI assignment is due soon.",
        createdAt: "Today",
        read: false,
      },
      {
        id: 2,
        title: "Academic update",
        message: "Your recent academic progress has been updated.",
        createdAt: "Yesterday",
        read: false,
      },
      {
        id: 3,
        title: "Recovery plan",
        message: "You have a new recommended action.",
        createdAt: "2 days ago",
        read: false,
      },
      {
        id: 4,
        title: "Quiz result",
        message: "Your latest quiz result has been recorded.",
        createdAt: "3 days ago",
        read: true,
      },
    ];
  },

  async markNotificationRead(id) {
    await wait(200);

    return {
      success: true,
      id,
    };
  },
};
