/**
 * EduGuardian Student Academic Standing & Guidance Helper
 * ========================================================
 * Derives student-facing academic standing and supportive guidance
 * based strictly on real academic records (CGPA, SGPA, credits, completed sems).
 *
 * DO NOT display internal risk classification labels (HIGH/MEDIUM/LOW RISK),
 * risk scores, confidence, factors, or SHAP explanations to the student.
 * All messaging is strictly encouraging, positive, and constructive.
 */

export function deriveAcademicStanding(histPerf, guidanceData) {
  const cgpa = histPerf?.cgpa !== null && histPerf?.cgpa !== undefined ? Number(histPerf.cgpa) : null;
  const latestSgpa = histPerf?.latest_sgpa !== null && histPerf?.latest_sgpa !== undefined ? Number(histPerf.latest_sgpa) : null;
  const backlogs = Number(histPerf?.arrears_count || 0);
  const completedSems = Number(histPerf?.total_semesters_completed || histPerf?.completed_semesters || 0);

  const cgpaStr = cgpa !== null ? cgpa.toFixed(2) : null;
  const sgpaStr = latestSgpa !== null ? latestSgpa.toFixed(2) : null;

  // 1. Foundation Building (CGPA < 5.0 OR backlogs >= 4 OR (latestSgpa < 5.0 && backlogs > 0))
  if ((cgpa !== null && cgpa < 5.0) || backlogs >= 4 || (latestSgpa !== null && latestSgpa < 5.0 && backlogs > 0)) {
    return {
      state: "foundation_building",
      badge: "ACADEMIC BASELINE BUILDING",
      badgeTone: "warning",
      headline: "Strengthen Your Academic Foundation",
      standingLabel: "Foundation Building",
      outlookStatus: "Foundation Building",
      outlookIcon: "attention",
      message:
        guidanceData?.message ||
        `Let's build a stronger academic foundation 💪 Focused preparation in foundational subjects and connecting with your faculty mentor will help you systematically elevate your upcoming semester coursework.`,
      outlookMessage:
        guidanceData?.outlook_message ||
        "Systematic subject-by-subject preparation and concept practice will help establish a solid academic baseline.",
    };
  }

  // 2. Focus on Strengthening Performance (CGPA 5.0-5.99 OR 1-3 backlogs OR recent lower SGPA)
  if ((cgpa !== null && cgpa < 6.0) || backlogs > 0 || (latestSgpa !== null && latestSgpa < 6.0)) {
    return {
      state: "strengthening_required",
      badge: "FOCUSED MOMENTUM",
      badgeTone: "warning",
      headline: "Focus on Strengthening Performance",
      standingLabel: "Active Standing",
      outlookStatus: "Focused Revision",
      outlookIcon: "attention",
      message:
        guidanceData?.message ||
        `Let's focus on strengthening your academic momentum 💪 (CGPA: ${cgpaStr || "—"}, Latest SGPA: ${sgpaStr || "—"}). Targeted practice on core technical topics will help elevate your upcoming examination results.`,
      outlookMessage:
        guidanceData?.outlook_message ||
        "Focus on targeted revision and key syllabus modules to build positive academic momentum.",
    };
  }

  // 3. Steady Academic Progress (CGPA 6.0-7.49 and 0 backlogs)
  if (cgpa !== null && cgpa >= 6.0 && cgpa < 7.5 && backlogs === 0) {
    return {
      state: "steady_progress",
      badge: cgpa >= 6.5 ? "FIRST CLASS STANDING" : "STEADY PROGRESS",
      badgeTone: "primary",
      headline: "Steady Academic Progress",
      standingLabel: cgpa >= 6.5 ? "First Class Standing" : "Good Standing",
      outlookStatus: "Steady Progress",
      outlookIcon: "check",
      message:
        guidanceData?.message ||
        `You're on a steady academic path 👍 (CGPA: ${cgpaStr}, Latest SGPA: ${sgpaStr || "—"}). Consistent study habits across current coursework will help you advance towards academic distinction.`,
      outlookMessage:
        guidanceData?.outlook_message ||
        `Consistent academic performance across ${completedSems} completed semesters with a clear record.`,
    };
  }

  // 4. Strong & Consistent Performance (CGPA >= 7.5, 0 backlogs)
  if (cgpa !== null && cgpa >= 7.5 && backlogs === 0) {
    return {
      state: "strong_consistent",
      badge: cgpa >= 8.5 ? "DISTINCTION STANDING" : "FIRST CLASS WITH DISTINCTION",
      badgeTone: "primary",
      headline: "Strong & Consistent Performance",
      standingLabel: cgpa >= 8.5 ? "Distinction Standing" : "First Class with Distinction",
      outlookStatus: "Distinction Track",
      outlookIcon: "check",
      message:
        guidanceData?.message ||
        `You're maintaining a strong and consistent academic record 👍 (CGPA: ${cgpaStr}, Latest SGPA: ${sgpaStr || "—"}). Keep up your disciplined coursework preparation to sustain high academic achievement.`,
      outlookMessage:
        guidanceData?.outlook_message ||
        `Maintaining strong academic performance with CGPA ${cgpaStr} across ${completedSems} completed semesters.`,
    };
  }

  // Default / New Semester
  return {
    state: "active_profile",
    badge: "ACTIVE PROFILE",
    badgeTone: "neutral",
    headline: "Academic Profile Active",
    standingLabel: "Enrolled",
    outlookStatus: "Active Standing",
    outlookIcon: "info",
    message:
      guidanceData?.message ||
      "Your academic profile is active. Stay engaged with lectures and coursework as examination records are published.",
    outlookMessage:
      guidanceData?.outlook_message ||
      "Active standing evaluated from completed semester examinations.",
  };
}
