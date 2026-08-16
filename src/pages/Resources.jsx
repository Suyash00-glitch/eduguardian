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
} from "lucide-react";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function getResourceType(url = "") {
  const cleanUrl = url.split("?")[0].toLowerCase();

  if (cleanUrl.endsWith(".pdf")) return "PDF";
  if (cleanUrl.endsWith(".doc") || cleanUrl.endsWith(".docx")) return "DOC";
  if (cleanUrl.endsWith(".ppt") || cleanUrl.endsWith(".pptx")) return "PPT";
  if (cleanUrl.endsWith(".xls") || cleanUrl.endsWith(".xlsx")) return "XLS";

  return "LINK";
}

function ResourceIcon({ type }) {
  if (type === "PDF") return <FileText size={21} />;
  if (type === "DOC") return <FileText size={21} />;
  if (type === "PPT") return <Presentation size={21} />;
  if (type === "XLS") return <FileSpreadsheet size={21} />;

  return <Link2 size={21} />;
}

function Resources() {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [category, setCategory] = useState("all");

  const loadResources = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await studentService.getResources();
      setResources(data);
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
            resource.target_category?.toLowerCase() === category
        );

  return (
    <div className="resources-page">
      {/* HEADER */}

      <div className="resources-header">
        <div>
          <span className="dashboard-eyebrow">LEARNING MATERIAL</span>

          <h2>Resources</h2>

          <p>
            Materials and links shared with you by your teachers.
          </p>
        </div>

        <div className="resources-header-icon">
          <BookOpen size={22} />
        </div>
      </div>

      {/* CONTENT HEADER */}

      <section className="resources-panel">
        <div className="resources-panel-header">
          <div>
            <span className="section-eyebrow">SHARED WITH YOU</span>

            <h3>Learning resources</h3>

            <span className="resources-count">
              {filteredResources.length}{" "}
              {filteredResources.length === 1
                ? "resource"
                : "resources"}
            </span>
          </div>

          <div className="resource-filter">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              <option value="high">High Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="low">Low Priority</option>
            </select>

            <ChevronDown size={15} />
          </div>
        </div>

        {/* EMPTY */}

        {filteredResources.length === 0 ? (
          <div className="resources-empty">
            <div className="resources-empty-icon">
              <BookOpen size={24} />
            </div>

            <strong>No resources yet</strong>

            <span>
              Your teachers haven't shared any resources with you yet.
            </span>
          </div>
        ) : (
          <div className="resource-list">
            {filteredResources.map((resource) => {
              const type = getResourceType(resource.url);

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
                        Shared by{" "}
                        <strong>
                          {resource.teacher_name || "Teacher"}
                        </strong>
                      </span>

                      <span className="resource-dot">•</span>

                      <span>
                        {resource.created_at
                          ? new Date(
                              resource.created_at
                            ).toLocaleDateString()
                          : "Recently shared"}
                      </span>
                    </div>
                  </div>

                  <div className="resource-category">
                    <span
                      className={`priority-badge ${
                        resource.target_category || "general"
                      }`}
                    >
                      {resource.target_category
                        ? resource.target_category === "all"
                          ? "General"
                          : `${resource.target_category
                              .charAt(0)
                              .toUpperCase()}${resource.target_category.slice(
                              1
                            )} Priority`
                        : "General"}
                    </span>
                  </div>

                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="resource-open"
                  >
                    <span>Open</span>
                    <ExternalLink size={15} />
                  </a>
                </article>
              );
            })}
          </div>
        )}

        {/* FOOTER */}

        {filteredResources.length > 0 && (
          <div className="resources-footer">
            <span>
              Showing 1 to {filteredResources.length} of{" "}
              {filteredResources.length} resources
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
    </div>
  );
}

export default Resources;