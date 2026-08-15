import React, { useCallback, useEffect, useState } from "react";
import {
  User,
  Mail,
  GraduationCap,
  Building2,
  Hash,
  Pencil,
  Save,
  X,
} from "lucide-react";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function Profile() {
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
  });

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await studentService.getStudent();
      setStudent(data);

      setForm({
        name: data.name || "",
        email: data.email || "",
      });
    } catch (err) {
      setError(err.message || "Unable to load profile.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const saveProfile = async (event) => {
    event.preventDefault();

    try {
      const updated = await studentService.updateProfile(form);

      setStudent((current) => ({
        ...current,
        ...updated,
      }));

      setEditing(false);
    } catch (err) {
      setError(err.message || "Unable to update profile.");
    }
  };

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

        {!editing && (
          <button
            className="profile-edit-button"
            onClick={() => setEditing(true)}
          >
            <Pencil size={13} />
            Edit profile
          </button>
        )}
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

        {editing ? (
          <form className="profile-form" onSubmit={saveProfile}>
            <label>
              Full name
              <input
                value={form.name}
                onChange={(e) =>
                  setForm({
                    ...form,
                    name: e.target.value,
                  })
                }
              />
            </label>

            <label>
              Email
              <input
                type="email"
                value={form.email}
                onChange={(e) =>
                  setForm({
                    ...form,
                    email: e.target.value,
                  })
                }
              />
            </label>

            <div className="profile-form-actions">
              <button
                type="button"
                className="profile-cancel"
                onClick={() => setEditing(false)}
              >
                <X size={13} />
                Cancel
              </button>

              <button type="submit" className="profile-save">
                <Save size={13} />
                Save changes
              </button>
            </div>
          </form>
        ) : (
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
        )}
      </section>
    </div>
  );
}

export default Profile;
