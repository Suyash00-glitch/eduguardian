import React, { useCallback, useEffect, useState } from "react";
import {
  BookOpen,
  ExternalLink,
  FileText,
  FileSpreadsheet,
  Presentation,
  X,
  Sparkles,
  Search,
  User,
  Calendar,
  Layers,
  GraduationCap,
  Download,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function getResourceType(url = "", typeOverride = "") {
  if (typeOverride) return typeOverride.toUpperCase();
  const cleanUrl = (url || "").split("?")[0].toLowerCase();

  if (cleanUrl.endsWith(".pdf")) return "PDF";
  if (cleanUrl.endsWith(".doc") || cleanUrl.endsWith(".docx")) return "DOC";
  if (cleanUrl.endsWith(".ppt") || cleanUrl.endsWith(".pptx")) return "PPT";
  if (cleanUrl.endsWith(".xls") || cleanUrl.endsWith(".xlsx")) return "XLS";

  return "PDF";
}

function ResourceIcon({ type }) {
  if (type === "PDF") return <FileText size={20} />;
  if (type === "DOC") return <FileText size={20} />;
  if (type === "PPT") return <Presentation size={20} />;
  if (type === "XLS") return <FileSpreadsheet size={20} />;

  return <BookOpen size={20} />;
}

function Resources() {
  const navigate = useNavigate();
  const [resources, setResources] = useState([]);
  const [mentor, setMentor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [category, setCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeModalResource, setActiveModalResource] = useState(null);

  const loadResources = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [resData, mentorData] = await Promise.all([
        studentService.getResources(),
        studentService.getMyMentor().catch(() => null),
      ]);
      setResources(resData || []);
      setMentor(mentorData);
    } catch (err) {
      setError(err.message || "Unable to load learning resources.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadResources();
  }, [loadResources]);

  if (loading) {
    return <LoadingState message="Loading your personalized study materials..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Unable to load resources"
        message={error}
        onRetry={loadResources}
      />
    );
  }

  const filteredResources = resources.filter((resource) => {
    const resCat = (resource.category || resource.target_category || "").toLowerCase();
    const matchesCategory = category === "all" || resCat.includes(category.toLowerCase());

    const titleMatch = (resource.title || "").toLowerCase().includes(searchQuery.toLowerCase());
    const descMatch = (resource.description || "").toLowerCase().includes(searchQuery.toLowerCase());
    const teacherMatch = (resource.teacher_name || "").toLowerCase().includes(searchQuery.toLowerCase());

    return matchesCategory && (titleMatch || descMatch || teacherMatch);
  });

  const getFullResourceUrl = (res) => {
    let targetUrl = res?.url || res?.resource_url || "";
    if (targetUrl.startsWith("/uploads")) {
      targetUrl = `http://localhost:5000${targetUrl}`;
    }
    return targetUrl;
  };

  const openResource = (res) => {
    const targetUrl = getFullResourceUrl(res);
    if (targetUrl && (targetUrl.startsWith("http://") || targetUrl.startsWith("https://"))) {
      window.open(targetUrl, "_blank", "noopener,noreferrer");
    } else {
      setActiveModalResource(res);
    }
  };

  return (
    <div className="resources-page">
      {/* HEADER */}
      <div
        className="resources-header"
        style={{
          marginBottom: "24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <h1 style={{ fontSize: "var(--font-2xl)", fontWeight: 700, margin: 0, color: "var(--text)" }}>
            Learning Resources &amp; Course Materials
          </h1>
          <p style={{ margin: "6px 0 0", fontSize: "var(--font-base)", color: "var(--text-secondary)" }}>
            Curated lecture notes, problem sets, and faculty remedial materials.
          </p>
        </div>

        <div
          style={{
            padding: "8px 16px",
            borderRadius: "10px",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <BookOpen size={20} color="var(--primary)" />
          <span style={{ fontSize: "var(--font-sm)", fontWeight: 600, color: "var(--text)" }}>
            {resources.length} {resources.length === 1 ? "Item" : "Items"} Available
          </span>
        </div>
      </div>

      {/* ASSIGNED FACULTY MENTOR CARD */}
      {mentor && (
        <div
          style={{
            background: "linear-gradient(135deg, var(--surface) 0%, rgba(6, 214, 160, 0.05) 100%)",
            border: "1px solid rgba(6, 214, 160, 0.3)",
            borderRadius: "14px",
            padding: "20px 24px",
            marginBottom: "24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "16px",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "12px",
                background: "var(--primary-soft)",
                color: "var(--primary)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <GraduationCap size={26} />
            </div>
            <div>
              <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--primary)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                Assigned Faculty Mentor
              </div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "var(--text)", marginTop: "2px" }}>
                {mentor.name || mentor.full_name}
              </div>
              <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "2px" }}>
                {mentor.designation || "Faculty Mentor"} · {mentor.department || "ISE"} · {mentor.email} {mentor.phone ? `· ${mentor.phone}` : ""}
              </div>
            </div>
          </div>

          <span
            style={{
              background: "rgba(6, 214, 160, 0.15)",
              color: "var(--primary)",
              border: "1px solid rgba(6, 214, 160, 0.3)",
              borderRadius: "20px",
              padding: "6px 14px",
              fontSize: "12px",
              fontWeight: 700,
            }}
          >
            Active 1-on-1 Mentorship
          </span>
        </div>
      )}

      {/* FILTER & SEARCH BAR */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "12px",
          marginBottom: "20px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {[
            { id: "all", label: "All Materials" },
            { id: "academic", label: "Academic Notes" },
            { id: "remedial", label: "Remedial & Guides" },
            { id: "high", label: "Priority" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setCategory(tab.id)}
              style={{
                padding: "8px 16px",
                borderRadius: "8px",
                border: "1px solid",
                borderColor: category === tab.id ? "var(--primary)" : "var(--border)",
                background: category === tab.id ? "var(--primary-soft)" : "var(--surface)",
                color: category === tab.id ? "var(--primary)" : "var(--text-secondary)",
                fontSize: "var(--font-sm)",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div style={{ position: "relative", minWidth: "260px" }}>
          <Search
            size={16}
            style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }}
          />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search notes, topics, or faculty..."
            style={{
              width: "100%",
              height: "38px",
              padding: "0 12px 0 36px",
              borderRadius: "8px",
              border: "1px solid var(--border)",
              background: "var(--surface)",
              color: "var(--text)",
              fontSize: "var(--font-sm)",
              outline: "none",
            }}
          />
        </div>
      </div>

      {/* RESOURCES GRID */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
          gap: "16px",
        }}
      >
        {filteredResources.length === 0 ? (
          <div
            style={{
              gridColumn: "1 / -1",
              textAlign: "center",
              padding: "40px 20px",
              borderRadius: "14px",
              border: "1px solid var(--border)",
              background: "var(--surface)",
              color: "var(--text-muted)",
            }}
          >
            <BookOpen size={36} style={{ opacity: 0.5, marginBottom: "10px" }} />
            <p style={{ margin: 0, fontSize: "16px", fontWeight: 600, color: "var(--text)" }}>
              No learning resources found.
            </p>
            <p style={{ margin: "6px 0 0", fontSize: "13px" }}>
              Try clearing your search or checking other category filters.
            </p>
          </div>
        ) : (
          filteredResources.map((resource) => {
            const type = getResourceType(resource.url || resource.resource_url || "", resource.type);
            const targetUrl = resource.url || resource.resource_url;

            return (
              <article
                key={resource.id}
                style={{
                  padding: "20px",
                  borderRadius: "14px",
                  border: "1px solid var(--border)",
                  background: "var(--surface)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  transition: "transform 0.15s ease, border-color 0.15s ease",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px" }}>
                    <div
                      style={{
                        width: "44px",
                        height: "44px",
                        borderRadius: "10px",
                        background: "rgba(6, 214, 160, 0.1)",
                        color: "var(--primary)",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      <ResourceIcon type={type} />
                      <span style={{ fontSize: "9px", fontWeight: 700, marginTop: "2px" }}>{type}</span>
                    </div>

                    <span
                      style={{
                        fontSize: "11px",
                        padding: "3px 8px",
                        borderRadius: "12px",
                        background: "var(--surface-soft)",
                        border: "1px solid var(--border)",
                        color: "var(--text-secondary)",
                        fontWeight: 600,
                      }}
                    >
                      {resource.category || resource.target_category || "Academic"}
                    </span>
                  </div>

                  <h3
                    style={{
                      margin: "0 0 8px",
                      fontSize: "16px",
                      fontWeight: 700,
                      color: "var(--text)",
                      lineHeight: "1.4",
                    }}
                  >
                    {resource.title}
                  </h3>

                  <p
                    style={{
                      margin: "0 0 16px",
                      fontSize: "13px",
                      color: "var(--text-secondary)",
                      lineHeight: "1.5",
                    }}
                  >
                    {resource.description || "Course study guide and key concepts shared by faculty mentor."}
                  </p>
                </div>

                <div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      fontSize: "12px",
                      color: "var(--text-muted)",
                      marginBottom: "14px",
                      paddingTop: "12px",
                      borderTop: "1px solid var(--border)",
                    }}
                  >
                    <User size={14} color="var(--primary)" />
                    <span>{resource.teacher_name || "Faculty Mentor"}</span>
                  </div>

                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      onClick={() => setActiveModalResource(resource)}
                      style={{
                        flex: 1,
                        height: "38px",
                        padding: "0 14px",
                        borderRadius: "8px",
                        border: "1px solid var(--border)",
                        background: "var(--surface-soft)",
                        color: "var(--text)",
                        fontWeight: 600,
                        fontSize: "13px",
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "6px",
                      }}
                    >
                      <span>Preview</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => openResource(resource)}
                      style={{
                        height: "38px",
                        padding: "0 16px",
                        borderRadius: "8px",
                        border: "none",
                        background: "var(--primary)",
                        color: "#061412",
                        fontWeight: 700,
                        fontSize: "13px",
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "6px",
                      }}
                    >
                      <span>Open</span>
                      <ExternalLink size={14} />
                    </button>
                  </div>
                </div>
              </article>
            );
          })
        )}
      </section>

      {/* RESOURCE PREVIEW MODAL */}
      {activeModalResource && (
        <div className="goal-form-overlay" onClick={() => setActiveModalResource(null)}>
          <div
            style={{
              padding: "26px",
              borderRadius: "16px",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              maxWidth: "540px",
              width: "100%",
              boxShadow: "0 20px 50px rgba(0,0,0,0.4)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "18px" }}>
              <div>
                <span
                  style={{
                    fontSize: "11px",
                    padding: "2px 8px",
                    borderRadius: "12px",
                    background: "var(--primary-soft)",
                    color: "var(--primary)",
                    fontWeight: 700,
                    display: "inline-block",
                    marginBottom: "6px",
                  }}
                >
                  {activeModalResource.category || activeModalResource.target_category || "Academic"}
                </span>
                <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: "var(--text)" }}>
                  {activeModalResource.title}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveModalResource(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", padding: "4px" }}
              >
                <X size={20} />
              </button>
            </div>

            <div
              style={{
                padding: "14px 16px",
                borderRadius: "10px",
                background: "var(--surface-soft)",
                border: "1px solid var(--border)",
                marginBottom: "18px",
              }}
            >
              <h4 style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", margin: "0 0 6px" }}>
                Description &amp; Syllabus Overview
              </h4>
              <p style={{ fontSize: "14px", color: "var(--text)", margin: 0, lineHeight: 1.5 }}>
                {activeModalResource.description || "Course study guide, unit slides, and revision problems shared by faculty mentor."}
              </p>
            </div>

            <div
              style={{
                padding: "12px 16px",
                borderRadius: "10px",
                background: "rgba(6,214,160,0.06)",
                border: "1px solid rgba(6,214,160,0.2)",
                marginBottom: "22px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--primary)", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>
                <Sparkles size={14} />
                Faculty Mentor Note
              </div>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
                Shared by <strong>{activeModalResource.teacher_name || "Faculty Mentor"}</strong> ({activeModalResource.teacher_designation || "Department Faculty"}).
                Review these materials before the upcoming internal assessment.
              </p>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <button
                type="button"
                onClick={() => {
                  setActiveModalResource(null);
                  navigate("/coach");
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--primary)",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <Sparkles size={16} />
                Discuss in AI Coach
              </button>

              <a
                href={getFullResourceUrl(activeModalResource) || "#"}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  height: "38px",
                  padding: "0 20px",
                  borderRadius: "8px",
                  background: "var(--primary)",
                  color: "#061412",
                  fontWeight: 700,
                  fontSize: "13px",
                  textDecoration: "none",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <Download size={14} />
                <span>Open Reference</span>
                <ExternalLink size={13} />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Resources;