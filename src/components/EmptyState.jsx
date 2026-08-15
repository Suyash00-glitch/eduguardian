import React from "react";
import { Inbox } from "lucide-react";

function EmptyState({
  title = "Nothing here yet",
  message = "There is no information to display.",
  action,
  actionLabel = "Refresh",
}) {
  return (
    <div className="ui-state empty-state">
      <div className="ui-state-icon">
        <Inbox size={20} />
      </div>

      <strong>{title}</strong>

      <span>{message}</span>

      {action && (
        <button className="state-action-button" onClick={action}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export default EmptyState;
