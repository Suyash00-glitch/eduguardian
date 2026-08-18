import React from "react";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

function BackButton({ fallback = "/dashboard", label = "Back" }) {
  const navigate = useNavigate();

  const handleBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate(fallback);
    }
  };

  return (
    <button className="back-button" onClick={handleBack}>
      <ArrowLeft size={14} />
      {label}
    </button>
  );
}

export default BackButton;
