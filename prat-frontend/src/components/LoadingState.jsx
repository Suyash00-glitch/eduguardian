import React from "react";
import { Loader2 } from "lucide-react";

function LoadingState({ message = "Loading..." }) {
  return (
    <div className="ui-state loading-state">
      <Loader2 className="ui-spinner" size={22} />

      <strong>{message}</strong>

      <span>Please wait a moment.</span>
    </div>
  );
}

export default LoadingState;
