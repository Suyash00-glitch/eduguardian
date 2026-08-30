import React, { useState, useEffect } from "react";
import { Bot, RefreshCw, ExternalLink } from "lucide-react";
import { getStoredSession } from "../services/authService";

function Coach() {
  const [iframeKey, setIframeKey] = useState(0);
  const [currentUser, setCurrentUser] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);

  useEffect(() => {
    const session = getStoredSession();
    if (session && session.user) {
      setCurrentUser(session.user);
      setCurrentSession(session);
    }

    const handleMessage = (event) => {
      if (
        event.data &&
        (event.data.type === "STUDY_PLAN_GENERATED" ||
          event.data.type === "PLAN_CREATED" ||
          event.data.study_plan)
      ) {
        const planData = event.data.plan || event.data.study_plan;
        import("../services/studentService").then(({ studentService }) => {
          studentService.syncAiStudyPlan(planData);
        });
      }
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  const studentIdentifier =
    currentUser?.usn || currentUser?.email || currentUser?.id || "1MS21IS001";
  const sessionToken = currentSession?.token || "";

  // Dynamically resolve chatbot URL with student identity and auth token
  const tokenParam = sessionToken ? `&token=${encodeURIComponent(sessionToken)}` : "";
  const chatbotUrl =
    typeof window !== "undefined"
      ? `${window.location.protocol}//${window.location.hostname}:3000?student_id=${encodeURIComponent(
          studentIdentifier
        )}${tokenParam}&theme=dark&_v=${iframeKey}`
      : `http://localhost:3000?student_id=${encodeURIComponent(studentIdentifier)}${tokenParam}&theme=dark&_v=${iframeKey}`;

  return (
    <div
      className="coach-page"
      style={{
        height: "calc(100vh - 20px)",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        padding: "0",
        margin: "0",
      }}
    >
      {/* SLEEK COMPACT TOP BAR */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "2px 4px 6px 4px",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <h2
            style={{
              fontSize: "17px",
              fontWeight: "700",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              margin: 0,
              color: "var(--text)",
            }}
          >
            <Bot size={20} color="var(--primary)" />
            AI Academic & Recovery Coach
          </h2>
          {currentUser?.full_name && (
            <span
              style={{
                fontSize: "11px",
                padding: "2px 8px",
                borderRadius: "12px",
                background: "var(--primary-soft)",
                color: "var(--primary)",
                fontWeight: "600",
                letterSpacing: "0.2px",
              }}
            >
              {currentUser.full_name} ({currentUser.usn || "ISE-5-C"})
            </span>
          )}
        </div>

        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
          <button
            onClick={() => setIframeKey((k) => k + 1)}
            title="Reset Chat Session"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "5px",
              padding: "4px 10px",
              borderRadius: "6px",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              color: "var(--text)",
              cursor: "pointer",
              fontSize: "11px",
              fontWeight: "500",
            }}
          >
            <RefreshCw size={12} />
            Reset Chat
          </button>
          <a
            href={chatbotUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "5px",
              padding: "4px 10px",
              borderRadius: "6px",
              background: "var(--primary-soft)",
              border: "1px solid var(--border)",
              color: "var(--primary)",
              textDecoration: "none",
              fontSize: "11px",
              fontWeight: "600",
            }}
          >
            <ExternalLink size={12} />
            Full Window
          </a>
        </div>
      </div>

      {/* FULL VIEWPORT EMBEDDED CHATBOT */}
      <div
        style={{
          flex: 1,
          width: "100%",
          borderRadius: "12px",
          overflow: "hidden",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          boxShadow: "0 6px 24px rgba(0,0,0,0.2)",
          position: "relative",
        }}
      >
        <iframe
          key={iframeKey}
          src={chatbotUrl}
          title="EduGuardian AI Academic Coach"
          style={{
            width: "100%",
            height: "100%",
            border: "none",
            display: "block",
          }}
        />
      </div>
    </div>
  );
}

export default Coach;

