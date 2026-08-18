import React, { useEffect } from "react";
import { CheckCircle2, X } from "lucide-react";

function SuccessToast({ message, onClose, duration = 3000 }) {
  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(() => {
      onClose?.();
    }, duration);

    return () => clearTimeout(timer);
  }, [message, duration, onClose]);

  if (!message) {
    return null;
  }

  return (
    <div className="success-toast">
      <CheckCircle2 size={16} />

      <span>{message}</span>

      <button onClick={onClose}>
        <X size={13} />
      </button>
    </div>
  );
}

export default SuccessToast;
