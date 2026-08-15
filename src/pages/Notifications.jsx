import React, { useCallback, useEffect, useState } from "react";
import { Bell, Check, CheckCheck, Clock3, Info, Sparkles } from "lucide-react";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await studentService.getNotifications();
      setNotifications(data);
    } catch (err) {
      setError(err.message || "Unable to load notifications.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  const markRead = async (id) => {
    try {
      await studentService.markNotificationRead(id);

      setNotifications((current) =>
        current.map((item) =>
          item.id === id ? { ...item, read: true } : item,
        ),
      );
    } catch (err) {
      setError(err.message || "Unable to update notification.");
    }
  };

  const markAllRead = async () => {
    const unread = notifications.filter((item) => !item.read);

    try {
      await Promise.all(
        unread.map((item) => studentService.markNotificationRead(item.id)),
      );

      setNotifications((current) =>
        current.map((item) => ({
          ...item,
          read: true,
        })),
      );
    } catch (err) {
      setError(err.message || "Unable to update notifications.");
    }
  };

  if (loading) {
    return <LoadingState message="Loading notifications..." />;
  }

  if (error && !notifications.length) {
    return (
      <ErrorState
        title="Unable to load notifications"
        message={error}
        onRetry={loadNotifications}
      />
    );
  }

  const unreadCount = notifications.filter((item) => !item.read).length;

  return (
    <div className="notifications-page">
      <div className="notifications-header">
        <div>
          <span className="dashboard-eyebrow">ACCOUNT</span>

          <h2>Notifications</h2>

          <p>Important updates about your academic journey.</p>
        </div>

        {unreadCount > 0 && (
          <button className="mark-all-button" onClick={markAllRead}>
            <CheckCheck size={13} />
            Mark all as read
          </button>
        )}
      </div>

      {error && <div className="notification-inline-error">{error}</div>}

      <section className="notifications-panel">
        <div className="notifications-panel-header">
          <div>
            <span className="section-eyebrow">RECENT UPDATES</span>

            <h3>
              {unreadCount > 0
                ? `${unreadCount} unread notification${
                    unreadCount > 1 ? "s" : ""
                  }`
                : "You're all caught up"}
            </h3>
          </div>

          <Bell size={16} />
        </div>

        {notifications.length === 0 ? (
          <div className="notifications-empty">
            <Bell size={22} />

            <strong>No notifications</strong>

            <span>You're all caught up.</span>
          </div>
        ) : (
          <div className="notification-list">
            {notifications.map((item) => (
              <div
                key={item.id}
                className={`notification-row ${item.read ? "read" : "unread"}`}
              >
                <div className="notification-icon">
                  {item.title?.toLowerCase().includes("assignment") ? (
                    <Clock3 size={15} />
                  ) : item.title?.toLowerCase().includes("update") ? (
                    <Sparkles size={15} />
                  ) : (
                    <Info size={15} />
                  )}
                </div>

                <div className="notification-content">
                  <div className="notification-title">
                    <strong>{item.title}</strong>

                    {!item.read && <span className="unread-dot" />}
                  </div>

                  <p>{item.message}</p>

                  <span className="notification-date">{item.createdAt}</span>
                </div>

                {!item.read && (
                  <button
                    className="notification-read-button"
                    onClick={() => markRead(item.id)}
                    title="Mark as read"
                  >
                    <Check size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default Notifications;
