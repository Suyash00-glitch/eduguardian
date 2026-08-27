/**
 * EduGuardian Student Academic Standing & Guidance Helper
 * ========================================================
 * Derives student-facing academic standing and supportive guidance
 * based strictly on real academic records (CGPA, SGPA, trajectory, backlogs, completed sems).
 *
 * DO NOT display internal risk classification labels (HIGH/MEDIUM/LOW RISK),
 * risk scores, confidence, factors, or SHAP explanations.
 */

export function deriveAcademicStanding(histPerf, guidanceData) {
  const cgpa = histPerf?.cgpa !== null && histPerf?.cgpa !== undefined ? Number(histPerf.cgpa) : null;
  const latestSgpa = histPerf?.latest_sgpa !== null && histPerf?.latest_sgpa !== undefined ? Number(histPerf.latest_sgpa) : null;
  const trend = (histPerf?.sgpa_trend || "stable").toLowerCase();
  const backlogs = Number(histPerf?.arrears_count || 0);
  const completedSems = Number(histPerf?.total_semesters_completed || histPerf?.completed_semesters || 0);

  const cgpaStr = cgpa !== null ? cgpa.toFixed(2) : null;
  const sgpaStr = latestSgpa !== null ? latestSgpa.toFixed(2) : null;

  // 1. Foundation Building (CGPA < 5.0 OR backlogs >= 4 OR (latestSgpa < 5.0 && backlogs > 0))
  if ((cgpa !== null && cgpa < 5.0) || backlogs >= 4 || (latestSgpa !== null && latestSgpa < 5.0 && backlogs > 0)) {
    const backlogTxt = backlogs > 0 ? `, ${backlogs} pending backlog(s)` : "";
    return {
      state: "foundation_building",
      badge: "ACADEMIC FOUNDATION BUILDING",
      badgeTone: "warning",
      headline: "Strengthen Your Academic Foundation",
      standingLabel: "Academic Foundation Building",
      outlookStatus: "Foundation Building",
      outlookIcon: "attention",
      message:
        guidanceData?.message ||
        `Let's build a stronger academic foundation 💪 Recent examination records indicate areas needing dedicated focus (CGPA: ${cgpaStr || "—"}, Latest SGPA: ${sgpaStr || "—"}${backlogTxt}). Focused revision in key foundational subjects and working with your faculty mentor will help you systematically clear pending coursework.`,
      outlookMessage:
        guidanceData?.outlook_message ||
        "Systematic subject-by-subject preparation and clearing pending coursework will help establish a solid academic baseline.",
      trajectory: trend,
    };
  }

  // 2. Focus on Strengthening Performance (CGPA 5.0-5.99 OR 1-3 backlogs OR (trend === "declining" && CGPA < 7.5))
  if ((cgpa !== null && cgpa < 6.0) || (backlogs > 0 && backlogs <= 3) || (trend === "declining" && (cgpa || 0) < 7.5)) {
    const backlogTxt = backlogs > 0 ? ` with ${backlogs} pending subject(s)` : "";
    return {
      state: "strengthening_required",
      badge: "FOCUS ON STRENGTHENING",
      badgeTone: "warning",
      headline: "Focus on Strengthening Performance",
      standingLabel: backlogs > 0 ? "Attention Recommended" : "Passing Standing",
      outlookStatus: "Focus Required",
      outlookIcon: "attention",
      message:
        guidanceData?.message ||
        `Let's focus on strengthening your academic momentum 💪 (CGPA: ${cgpaStr || "—"}, Latest SGPA: ${sgpaStr || "—"}${backlogTxt}). Targeted practice on core topics and clearing pending subjects will help elevate your upcoming semester results.`,
      outlookMessage:
        guidanceData?.outlook_message ||
        "Focus on targeted revision and clearing pending subjects to rebuild positive academic momentum.",
      trajectory: trend,
    };
  }

  // 3. Steady Academic Progress (CGPA 6.0-7.49 and 0 backlogs)
  if (cgpa !== null && cgpa >= 6.0 && cgpa < 7.5 && backlogs === 0) {
    return {
      state: "steady_progress",
      badge: cgpa >= 6.5 ? "FIRST CLASS STANDING" : "STEADY PROGRESS",
      badgeTone: "primary",
      headline: "Steady Academic Progress",
      standingLabel: cgpa >= 6.5 ? "First Class standing" : "Good standing",
      outlookStatus: "Steady Progress",
      outlookIcon: "check",
      message:
        guidanceData?.message ||
        `You're on a steady academic path 👍 (CGPA: ${cgpaStr}, Latest SGPA: ${sgpaStr || "—"}). Consistent study habits across current coursework will help you advance towards academic distinction.`,
      outlookMessage:
        guidanceData?.outlook_message ||
        `Consistent academic performance across ${completedSems} completed semesters with a clear record.`,
      trajectory: trend,
    };
  }

  // 4. Strong & Consistent Performance (CGPA >= 7.5, stable, 0 backlogs)
  if (cgpa !== null && cgpa >= 7.5 && trend === "stable" && backlogs === 0) {
    return {
      state: "strong_consistent",
      badge: cgpa >= 8.5 ? "DISTINCTION STANDING" : "STRONG STANDING",
      badgeTone: "primary",
      headline: "Strong & Consistent Performance",
      standingLabel: cgpa >= 8.5 ? "Distinction standing" : "First Class with Distinction",
      outlookStatus: "Consistent High Standing",
      outlookIcon: "check",
      message:
        guidanceData?.message ||
        `You're maintaining a strong and consistent academic record 👍 (CGPA: ${cgpaStr}, Latest SGPA: ${sgpaStr || "—"}). Keep up your disciplined coursework preparation to sustain high academic achievement.`,
      outlookMessage:
        guidanceData?.outlook_message ||
        `Maintaining strong academic performance with CGPA ${cgpaStr} across ${completedSems} completed semesters.`,
      trajectory: trend,
    };
  }

  // 5. Strong Academic Momentum (CGPA >= 7.5, improving/positive, 0 backlogs)
  if (cgpa !== null && cgpa >= 7.5 && backlogs === 0) {
    return {
      state: "strong_momentum",
      badge: cgpa >= 8.5 ? "DISTINCTION STANDING" : "STRONG MOMENTUM",
      badgeTone: "primary",
      headline: "Strong Academic Momentum",
      standingLabel: cgpa >= 8.5 ? "Distinction standing" : "First Class with Distinction",
      outlookStatus: "Positive Trajectory",
      outlookIcon: "check",
      message:
        guidanceData?.message ||
        `You're building strong momentum 🌟 Your historical academic performance is strong with an improving trajectory (CGPA: ${cgpaStr}, Latest SGPA: ${sgpaStr || "—"}). Maintaining consistent study habits will keep you on track for academic distinction.`,
      outlookMessage:
        guidanceData?.outlook_message ||
        `Maintaining distinction performance with CGPA ${cgpaStr} across ${completedSems} completed semesters.`,
      trajectory: trend,
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
    trajectory: trend,
  };
}
