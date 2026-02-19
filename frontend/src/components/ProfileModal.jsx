import { useState, useRef } from "react";
import { FaTimes, FaCamera } from "react-icons/fa";
import { useAuth } from "../context/AuthContext";
import { api, apiUpload } from "../api";

const API_BASE = "http://localhost:8000";

export default function ProfileModal({ onClose }) {
  const { user, token, refreshUser } = useAuth();
  const fileRef = useRef(null);

  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [bio, setBio] = useState(user?.bio || "");
  const [preview, setPreview] = useState(
    user?.avatar_url ? `${API_BASE}${user.avatar_url}` : null
  );
  const [selectedFile, setSelectedFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const initials = (user?.display_name || user?.username || "?")[0].toUpperCase();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      setError("Image must be under 5MB");
      return;
    }
    setSelectedFile(file);
    setPreview(URL.createObjectURL(file));
    setError("");
  };

  const handleSave = async () => {
    setError("");
    setSaving(true);
    try {
      // Upload avatar if changed
      if (selectedFile) {
        await apiUpload("/users/me/avatar", { file: selectedFile, token });
      }

      // Update profile fields
      await api("/users/me", {
        method: "PUT",
        body: { display_name: displayName.trim(), bio: bio.trim() },
        token,
      });

      await refreshUser();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content profile-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h5>Edit Profile</h5>
          <button className="modal-close-btn" onClick={onClose}>
            <FaTimes size={18} />
          </button>
        </div>

        <div className="modal-body">
          {/* Avatar */}
          <div className="profile-avatar-section">
            <div
              className="profile-avatar-preview"
              onClick={() => fileRef.current?.click()}
            >
              {preview ? (
                <img src={preview} alt="avatar" />
              ) : (
                <span className="profile-avatar-initials">{initials}</span>
              )}
              <div className="profile-avatar-overlay">
                <FaCamera size={20} />
              </div>
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              onChange={handleFileChange}
              style={{ display: "none" }}
            />
            <button
              className="profile-change-photo-btn"
              onClick={() => fileRef.current?.click()}
            >
              Change Photo
            </button>
          </div>

          {/* Display Name */}
          <div className="profile-field">
            <label className="profile-field-label">Display Name</label>
            <input
              className="modal-input"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              maxLength={50}
              placeholder="Your display name"
            />
          </div>

          {/* Bio */}
          <div className="profile-field">
            <label className="profile-field-label">Bio</label>
            <textarea
              className="modal-input profile-bio-input"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              maxLength={150}
              placeholder="Hey there! I am using Rchat.ai"
              rows={3}
            />
            <div className="profile-bio-count">{bio.length}/150</div>
          </div>

          {/* Read-only fields */}
          <div className="profile-field">
            <label className="profile-field-label">Username</label>
            <div className="profile-readonly">@{user?.username}</div>
          </div>

          <div className="profile-field">
            <label className="profile-field-label">Email</label>
            <div className="profile-readonly">{user?.email}</div>
          </div>

          {error && <div className="modal-error">{error}</div>}
        </div>

        <div className="modal-footer">
          <button className="modal-cancel-btn" onClick={onClose}>
            Cancel
          </button>
          <button
            className="modal-create-btn"
            onClick={handleSave}
            disabled={saving || !displayName.trim()}
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}
