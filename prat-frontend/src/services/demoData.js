export const demoStudent = {
  id: "STU-DEMO-001",
  usn: "4NM24IS001",
  name: "Pratham",
  email: "student@eduguardian.ai",
  department: "Information Science",
  semester: 4,
  section: "A",
};

export const demoDashboard = {
  attendance: 86,
  attendanceChange: 3.2,

  averageScore: 82,
  scoreChange: 4.5,

  assignments: {
    completed: 18,
    total: 21,
    missed: 3,
  },

  lmsActivity: 74,

  recoveryProbability: 89,

  supportSignal: {
    status: "low",
    message: "Your academic engagement is stable.",
  },
};

export const demoAttendance = [
  {
    subjectCode: "DBMS",
    subjectName: "Database Management Systems",
    classesHeld: 42,
    classesAttended: 38,
    percentage: 90.48,
  },
  {
    subjectCode: "CN",
    subjectName: "Computer Networks",
    classesHeld: 40,
    classesAttended: 34,
    percentage: 85,
  },
  {
    subjectCode: "SE",
    subjectName: "Software Engineering",
    classesHeld: 38,
    classesAttended: 32,
    percentage: 84.21,
  },
  {
    subjectCode: "AI",
    subjectName: "Artificial Intelligence",
    classesHeld: 36,
    classesAttended: 30,
    percentage: 83.33,
  },
];

export const demoAssignments = [
  {
    id: 1,
    subject: "DBMS",
    name: "SQL Assignment 3",
    status: "submitted",
    marks: 18,
    maxMarks: 20,
    dueDate: "2026-08-12",
  },
  {
    id: 2,
    subject: "CN",
    name: "Network Protocol Report",
    status: "late",
    marks: 16,
    maxMarks: 20,
    dueDate: "2026-08-14",
  },
  {
    id: 3,
    subject: "AI",
    name: "Search Algorithms",
    status: "missed",
    marks: null,
    maxMarks: 20,
    dueDate: "2026-08-15",
  },
];

export const demoQuizResults = [
  {
    subjectCode: "DBMS",
    subjectName: "Database Management Systems",
    quizName: "Quiz 1",
    marks: 18,
    maxMarks: 20,
    date: "2026-08-05",
  },
  {
    subjectCode: "CN",
    subjectName: "Computer Networks",
    quizName: "Quiz 1",
    marks: 16,
    maxMarks: 20,
    date: "2026-08-07",
  },
  {
    subjectCode: "SE",
    subjectName: "Software Engineering",
    quizName: "Quiz 1",
    marks: 17,
    maxMarks: 20,
    date: "2026-08-09",
  },
  {
    subjectCode: "AI",
    subjectName: "Artificial Intelligence",
    quizName: "Quiz 1",
    marks: 15,
    maxMarks: 20,
    date: "2026-08-11",
  },
];

export const demoLmsActivity = [
  {
    date: "Mon",
    minutes: 85,
    activities: 12,
  },
  {
    date: "Tue",
    minutes: 110,
    activities: 16,
  },
  {
    date: "Wed",
    minutes: 72,
    activities: 9,
  },
  {
    date: "Thu",
    minutes: 125,
    activities: 18,
  },
  {
    date: "Fri",
    minutes: 95,
    activities: 14,
  },
  {
    date: "Sat",
    minutes: 65,
    activities: 8,
  },
  {
    date: "Sun",
    minutes: 40,
    activities: 5,
  },
];
export const demoInsights = {
  riskLevel: "low",
  recoveryProbability: 89,

  signal: "Your academic engagement is currently stable.",

  summary:
    "Your recent attendance, assignment completion and LMS activity indicate a positive academic trajectory.",

  factors: [
    {
      name: "Attendance",
      impact: "positive",
      value: "+8%",
      explanation: "Your attendance has remained above the recommended level.",
    },
    {
      name: "LMS Activity",
      impact: "positive",
      value: "+12%",
      explanation: "You have been spending more time learning through the LMS.",
    },
    {
      name: "Assignment Completion",
      impact: "negative",
      value: "-4%",
      explanation: "A few assignments were submitted late or missed recently.",
    },
  ],

  changes: [
    {
      label: "Attendance",
      value: "+3.2%",
      direction: "up",
    },
    {
      label: "LMS engagement",
      value: "+12%",
      direction: "up",
    },
    {
      label: "Missed assignments",
      value: "+1",
      direction: "down",
    },
  ],
};
export const demoRecoveryPlan = {
  title: "Your Academic Recovery Plan",

  summary:
    "A few focused actions can help you maintain your current academic trajectory.",

  progress: 42,

  goals: [
    {
      id: 1,
      title: "Complete pending AI assignment",
      description: "Submit the Search Algorithms assignment.",
      category: "Assignment",
      dueDate: "2026-08-17",
      completed: false,
    },
    {
      id: 2,
      title: "Maintain attendance",
      description: "Keep attendance above 85% this week.",
      category: "Attendance",
      dueDate: "2026-08-21",
      completed: true,
    },
    {
      id: 3,
      title: "Complete 3 LMS study sessions",
      description: "Spend at least 45 minutes per session.",
      category: "LMS",
      dueDate: "2026-08-21",
      completed: false,
    },
    {
      id: 4,
      title: "Review Computer Networks",
      description: "Revise the topics covered in the latest quiz.",
      category: "Study",
      dueDate: "2026-08-19",
      completed: false,
    },
  ],
};
export const demoCoachReplies = {
  attendance:
    "Your attendance is currently around 86%. Try to maintain it above 85% by attending your upcoming classes consistently.",

  study:
    "Based on your recent activity, I recommend two focused study sessions each day: one for your weakest subject and one for revision. Keep each session around 45–60 minutes.",

  assignment:
    "You currently have one missed assignment. I'd recommend completing it first, then reviewing the topics covered before your next assessment.",

  default:
    "I can help you with study planning, assignments, attendance, time management, and your recovery goals. What would you like to work on?",
};
export const demoGoals = [
  {
    id: 1,
    title: "Maintain 85% attendance",
    target: "85%",
    progress: 86,
    status: "on-track",
  },
  {
    id: 2,
    title: "Complete all pending assignments",
    target: "100%",
    progress: 72,
    status: "in-progress",
  },
  {
    id: 3,
    title: "Improve weekly LMS activity",
    target: "8 hours",
    progress: 78,
    status: "on-track",
  },
];
export const demoAssignmentList = [
  {
    id: "ASM-001",
    subjectCode: "DBMS",
    subjectName: "Database Management Systems",
    title: "SQL Assignment 3",
    description: "Write SQL queries based on the provided database schema.",
    dueDate: "2026-08-20T23:59:00",
    maxMarks: 20,
    status: "pending",
    submissionStatus: "not-submitted",
  },
  {
    id: "ASM-002",
    subjectCode: "CN",
    subjectName: "Computer Networks",
    title: "Network Protocol Report",
    description:
      "Prepare a report explaining TCP, UDP and application-layer protocols.",
    dueDate: "2026-08-14T23:59:00",
    maxMarks: 20,
    status: "submitted",
    submissionStatus: "submitted",
    submittedAt: "2026-08-13T18:42:00",
    marks: 16,
  },
  {
    id: "ASM-003",
    subjectCode: "AI",
    subjectName: "Artificial Intelligence",
    title: "Search Algorithms",
    description: "Implement and compare BFS, DFS and A* search algorithms.",
    dueDate: "2026-08-15T23:59:00",
    maxMarks: 20,
    status: "overdue",
    submissionStatus: "missed",
  },
  {
    id: "ASM-004",
    subjectCode: "SE",
    subjectName: "Software Engineering",
    title: "Software Requirements Specification",
    description: "Prepare an SRS document for the assigned software system.",
    dueDate: "2026-08-22T23:59:00",
    maxMarks: 25,
    status: "pending",
    submissionStatus: "not-submitted",
  },
  {
    id: "ASM-005",
    subjectCode: "DBMS",
    subjectName: "Database Management Systems",
    title: "Normalization Exercise",
    description: "Normalize the given relational schemas up to BCNF.",
    dueDate: "2026-08-10T23:59:00",
    maxMarks: 15,
    status: "submitted",
    submissionStatus: "submitted",
    submittedAt: "2026-08-09T16:20:00",
    marks: 14,
  },
];
