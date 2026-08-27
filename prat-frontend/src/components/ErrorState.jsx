import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

function ErrorState({
  title = "Something went wrong",
  message = "We couldn't load this information.",
  onRetry,
}) {
  return (
    <div className="ui-state error-state">
      <div className="ui-state-icon error">
        <AlertCircle size={20} />
      </div>

      <strong>{title}</strong>

      <span>{message}</span>

      {onRetry && (
        <button className="state-action-button" onClick={onRetry}>
          <RotateCcw size={13} />
          Try again
        </button>
      )}
    </div>
  );
}

export default ErrorState;
