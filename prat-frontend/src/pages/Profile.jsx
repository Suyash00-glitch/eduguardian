import React, { useCallback, useEffect, useState } from "react";
import {
  User,
  Mail,
  GraduationCap,
  Building2,
  Hash,
} from "lucide-react";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function Profile() {
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
 

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await studentService.getStudent();
      setStudent(data);

    
    } catch (err) {
      setError(err.message || "Unable to load profile.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);



  if (loading) {
    return <LoadingState message="Loading your profile..." />;
  }

  if (error && !student) {
    return (
      <ErrorState
        title="Unable to load profile"
        message={error}
        onRetry={loadProfile}
      />
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-header">
        <div>
          <span className="dashboard-eyebrow">ACCOUNT</span>

          <h2>Profile</h2>

          <p>Manage your student information.</p>
        </div>

        
      </div>

      {error && <div className="profile-error">{error}</div>}

      <section className="profile-card">
        <div className="profile-banner">
          <div className="profile-avatar">
            {student?.name?.charAt(0) || "P"}
          </div>

          <div>
            <h3>{student?.name}</h3>

            <span>{student?.usn}</span>
          </div>
        </div>

       
          <div className="profile-details">
            <div className="profile-detail">
              <div className="profile-detail-icon">
                <User size={15} />
              </div>

              <div>
                <span>FULL NAME</span>
                <strong>{student?.name}</strong>
              </div>
            </div>

            <div className="profile-detail">
              <div className="profile-detail-icon">
                <Mail size={15} />
              </div>

              <div>
                <span>EMAIL</span>
                <strong>{student?.email}</strong>
              </div>
            </div>

            <div className="profile-detail">
              <div className="profile-detail-icon">
                <Hash size={15} />
              </div>

              <div>
                <span>USN</span>
                <strong>{student?.usn}</strong>
              </div>
            </div>

            <div className="profile-detail">
              <div className="profile-detail-icon">
                <Building2 size={15} />
              </div>

              <div>
                <span>DEPARTMENT</span>
                <strong>{student?.department}</strong>
              </div>
            </div>

            <div className="profile-detail">
              <div className="profile-detail-icon">
                <GraduationCap size={15} />
              </div>

              <div>
                <span>SEMESTER</span>
                <strong>Semester {student?.semester}</strong>
              </div>
            </div>

            <div className="profile-detail">
              <div className="profile-detail-icon">
                <Hash size={15} />
              </div>

              <div>
                <span>SECTION</span>
                <strong>{student?.section}</strong>
              </div>
            </div>
          </div>
        
      </section>
    </div>
  );
}

export default Profile;
