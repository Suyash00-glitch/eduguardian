import React, { useCallback, useEffect, useState } from "react";
import {
  BookOpen,
  ExternalLink,
  FileText,
  Link2,
  FileSpreadsheet,
  Presentation,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  X,
  Download,
  Sparkles,
  CheckCircle2,
  Bookmark,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

const RESOURCE_DETAILS_MAP = {
  1: {
    modules: ["Unit 1: Relational Algebra & SQL DDL/DML", "Unit 2: Normalization (1NF, 2NF, 3NF, BCNF)", "Unit 3: Transaction Processing & ACID Properties", "Unit 4: Indexing & B-Trees"],
    tips: "Focus on query optimization and indexing questions for upcoming assessments.",
    fileUrl: "https://en.wikipedia.org/wiki/Database_management_system",
  },
  2: {
    modules: ["Unit 1: OSI 7-Layer & TCP/IP Model", "Unit 2: Data Link Layer & Framing", "Unit 3: IP Addressing & Subnetting", "Unit 4: Routing Protocols (OSPF, BGP)"],
    tips: "Review subnet calculation formulas and packet header structures.",
    fileUrl: "https://en.wikipedia.org/wiki/Computer_network",
  },
  3: {
    modules: ["Unit 1: Software Development Life Cycle (SDLC)", "Unit 2: Agile & Scrum Methodology", "Unit 3: UML Diagrams & System Architecture", "Unit 4: Testing & CI/CD Pipelines"],
    tips: "Prepare use case and class diagrams for the semester project submission.",
    fileUrl: "https://en.wikipedia.org/wiki/Software_engineering",
  },
  4: {
    modules: ["Unit 1: Search Algorithms (A*, BFS, DFS)", "Unit 2: Knowledge Representation & First-Order Logic", "Unit 3: Machine Learning Foundations", "Unit 4: Neural Networks Basics"],
    tips: "Review heuristic functions and state space search trees.",
    fileUrl: "https://en.wikipedia.org/wiki/Artificial_intelligence",
  },
  5: {
    modules: ["Part 1: Daily 60-minute Active Recall Routine", "Part 2: Pomodoro Technique & Spaced Repetition", "Part 3: Exam Review Roadmap", "Part 4: High-Yield Practice Sets"],
    tips: "Follow the 3-step review cycle: Notes -> Practice Set -> Summary Card.",
    fileUrl: "https://en.wikipedia.org/wiki/Active_recall",
  },
};

function getResourceType(url = "", typeOverride = "") {
  if (typeOverride) return typeOverride.toUpperCase();
  const cleanUrl = url.split("?")[0].toLowerCase();

  if (cleanUrl.endsWith(".pdf")) return "PDF";
  if (cleanUrl.endsWith(".doc") || cleanUrl.endsWith(".docx")) return "DOC";
  if (cleanUrl.endsWith(".ppt") || cleanUrl.endsWith(".pptx")) return "PPT";
  if (cleanUrl.endsWith(".xls") || cleanUrl.endsWith(".xlsx")) return "XLS";

  return "PDF";
}

function ResourceIcon({ type }) {
  if (type === "PDF") return <FileText size={21} />;
  if (type === "DOC") return <FileText size={21} />;
  if (type === "PPT") return <Presentation size={21} />;
  if (type === "XLS") return <FileSpreadsheet size={21} />;

  return <BookOpen size={21} />;
}

function Resources() {
  const navigate = useNavigate();
  const [resources, setResources] = useState([]);
  const [mentor, setMentor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [category, setCategory] = useState("all");
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
      setError(err.message || "Unable to load resources.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadResources();
  }, [loadResources]);

  if (loading) {
    return <LoadingState message="Loading your resources..." />;
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

  const filteredResources =
    category === "all"
      ? resources
      : resources.filter(
          (resource) =>
            resource.category?.toLowerCase() === category ||
            resource.target_category?.toLowerCase() === category
        );

  const openResource = (res) => {
    if (res.url && res.url.startsWith("http")) {
      window.open(res.url, "_blank", "noopener,noreferrer");
    } else {
      setActiveModalResource(res);
    }
  };

  return (
    <div className="resources-page">
      {/* HEADER */}
      <div className="resources-header">
        <div>
          <span className="dashboard-eyebrow">LEARNING MATERIAL</span>
          <h2>Resources &amp; Materials</h2>
          <p>
            Curated course notes, syllabus guides, and reference materials shared by your faculty and mentor.
          </p>
        </div>

        <div className="resources-header-icon">
          <BookOpen size={22} />
        </div>
      </div>

      {/* ASSIGNED MENTOR BANNER */}
      {mentor && (
        <div style={{
          background: "linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(5, 150, 105, 0.04) 100%)",
          border: "1px solid rgba(16, 185, 129, 0.25)",
          borderRadius: "12px",
          padding: "16px 20px",
          marginBottom: "20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px"
        }}>
          <div>
            <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", color: "#10b981", textTransform: "uppercase" }}>
              YOUR ASSIGNED FACULTY MENTOR
            </span>
            <div style={{ fontSize: "16px", fontWeight: 700, color: "#fff", marginTop: "2px" }}>
              {mentor.name}
            </div>
            <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.7)", marginTop: "2px" }}>
              {mentor.designation} · {mentor.department} · {mentor.email} {mentor.phone ? `· ${mentor.phone}` : ""}
            </div>
          </div>
          <span style={{
            background: "rgba(16, 185, 129, 0.15)",
            color: "#34d399",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: "6px",
            padding: "4px 10px",
            fontSize: "11px",
            fontWeight: 700
          }}>
            1-ON-1 ACTIVE MENTOR
          </span>
        </div>
      )}

      {/* CONTENT PANEL */}
      <section className="resources-panel">
        <div className="resources-panel-header">
          <div>
            <span className="section-eyebrow">SHARED WITH YOU</span>
            <h3>Learning resources</h3>
            <span className="resources-count">
              {filteredResources.length}{" "}
              {filteredResources.length === 1 ? "resource" : "resources"}
            </span>
          </div>

          <div className="resource-filter">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="all">All Resources</option>
              <option value="academic">Academic Material</option>
              <option value="high">High Priority</option>
            </select>
            <ChevronDown size={15} />
          </div>
        </div>

        {/* LIST */}
        {filteredResources.length === 0 ? (
          <div className="resources-empty">
            <div className="resources-empty-icon">
              <BookOpen size={24} />
            </div>
            <strong>No resources yet</strong>
            <span>Your teachers haven't shared any resources in this category yet.</span>
          </div>
        ) : (
          <div className="resource-list">
            {filteredResources.map((resource) => {
              const type = getResourceType(resource.url || "", resource.type);

              return (
                <article className="resource-card" key={resource.id}>
                  <div className={`resource-file-icon ${type.toLowerCase()}`}>
                    <ResourceIcon type={type} />
                    <span>{type}</span>
                  </div>

                  <div className="resource-main">
                    <h3>{resource.title}</h3>
                    <div className="resource-details">
                      <span>
                        Shared by <strong>{resource.teacher_name || "Faculty Mentor"}</strong>
                      </span>
                      <span className="resource-dot">•</span>
                      <span>{resource.description || "Course study guide and key concepts"}</span>
                    </div>
                  </div>

                  <div className="resource-category">
                    <span className="priority-badge general">
                      {resource.category || "Study Material"}
                    </span>
                  </div>

                  <button
                    type="button"
                    className="resource-open-btn"
                    onClick={() => openResource(resource)}
                    title={`Open ${resource.title}`}
                  >
                    <span>Open</span>
                    <ExternalLink size={14} />
                  </button>
                </article>
              );
            })}
          </div>
        )}

        {/* FOOTER */}
        {filteredResources.length > 0 && (
          <div className="resources-footer">
            <span>
              Showing 1 to {filteredResources.length} of {filteredResources.length} resources
            </span>
            <div className="resource-pagination">
              <button disabled>
                <ChevronLeft size={16} />
              </button>
              <button className="active">1</button>
              <button disabled>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </section>

      {/* RESOURCE STUDY VIEWER MODAL */}
      {activeModalResource && (
        <div className="resource-modal-overlay" onClick={() => setActiveModalResource(null)}>
          <div className="resource-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="resource-modal-header">
              <div className="resource-modal-title">
                <span className="section-eyebrow">COURSE MATERIAL & STUDY GUIDE</span>
                <h3>{activeModalResource.title}</h3>
              </div>
              <button
                type="button"
                className="resource-modal-close"
                onClick={() => setActiveModalResource(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="resource-modal-body">
              <div className="resource-meta-bar">
                <div className="meta-pill">
                  <Bookmark size={13} />
                  <span>{activeModalResource.category || "Core Curriculum"}</span>
                </div>
                <div className="meta-pill">
                  <FileText size={13} />
                  <span>Format: PDF / Digital Guide</span>
                </div>
              </div>

              <div className="resource-section-block">
                <h4>Key Modules & Syllabus Units</h4>
                <div className="resource-module-list">
                  {(
                    RESOURCE_DETAILS_MAP[activeModalResource.id]?.modules || [
                      "Unit 1: Core Fundamentals & Principles",
                      "Unit 2: Implementation & Practical Exercises",
                      "Unit 3: Advanced Applications & Review",
                    ]
                  ).map((mod, i) => (
                    <div className="resource-module-item" key={i}>
                      <CheckCircle2 size={15} />
                      <span>{mod}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="resource-section-block study-tip-box">
                <div className="tip-header">
                  <Sparkles size={14} />
                  <strong>Study Tip from Faculty</strong>
                </div>
                <p>
                  {RESOURCE_DETAILS_MAP[activeModalResource.id]?.tips ||
                    "Review summary notes after each lecture and solve the end-of-chapter practice problems."}
                </p>
              </div>
            </div>

            <div className="resource-modal-actions">
              <button
                type="button"
                className="modal-ai-btn"
                onClick={() => {
                  setActiveModalResource(null);
                  navigate("/coach");
                }}
              >
                <Sparkles size={14} />
                <span>Ask AI Coach about this</span>
              </button>

              <a
                href={
                  RESOURCE_DETAILS_MAP[activeModalResource.id]?.fileUrl ||
                  "https://en.wikipedia.org/wiki/Computer_science"
                }
                target="_blank"
                rel="noopener noreferrer"
                className="modal-primary-btn"
              >
                <Download size={14} />
                <span>Open External Reference</span>
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