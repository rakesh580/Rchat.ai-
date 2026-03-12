import { useState, useEffect } from "react";
import { FaTimes, FaRobot, FaPlane } from "react-icons/fa";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export default function AutopilotModal({ onClose, onDeactivated }) {
  const { token } = useAuth();

  const [isActive, setIsActive] = useState(false);
  const [awayMessage, setAwayMessage] = useState("");
  const [backupPersonId, setBackupPersonId] = useState("");
  const [autoRespond, setAutoRespond] = useState(true);
  const [returnDate, setReturnDate] = useState("");
  const [contacts, setContacts] = useState([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [wasActive, setWasActive] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [settingsData, contactsData] = await Promise.all([
        api("/autopilot/settings", { token }),
        api("/contacts", { token }),
      ]);
      setIsActive(settingsData.is_active || false);
      setWasActive(settingsData.is_active || false);
      setAwayMessage(settingsData.away_message || "");
      setBackupPersonId(settingsData.backup_person_id || "");
      setAutoRespond(settingsData.auto_respond_enabled !== false);
      if (settingsData.expected_return_date) {
        const d = new Date(settingsData.expected_return_date);
        setReturnDate(d.toISOString().split("T")[0]);
      }
      setContacts(contactsData || []);
    } catch (err) {
      setError("Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setError("");
    setSaving(true);
    try {
      await api("/autopilot/settings", {
        method: "PUT",
        token,
        body: {
          is_active: isActive,
          away_message: awayMessage.trim(),
          backup_person_id: backupPersonId || null,
          auto_respond_enabled: autoRespond,
          expected_return_date: returnDate ? new Date(returnDate).toISOString() : null,
        },
      });

      // If deactivating, trigger briefing
      if (wasActive && !isActive && onDeactivated) {
        onDeactivated();
      }
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content autopilot-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-body" style={{ textAlign: "center", padding: "40px" }}>
            Loading...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content autopilot-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h5><FaRobot style={{ marginRight: 8, opacity: 0.7 }} />Conversation Autopilot</h5>
          <button className="modal-close-btn" onClick={onClose}>
            <FaTimes size={18} />
          </button>
        </div>

        <div className="modal-body">
          {/* Main Toggle */}
          <div className="autopilot-toggle-row">
            <div className="autopilot-toggle-info">
              <FaPlane size={16} style={{ opacity: 0.6 }} />
              <div>
                <div className="autopilot-toggle-label">
                  {isActive ? "Autopilot Active" : "Autopilot Off"}
                </div>
                <div className="autopilot-toggle-desc">
                  AI handles your messages while you're away
                </div>
              </div>
            </div>
            <label className="autopilot-switch">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
              <span className="autopilot-slider"></span>
            </label>
          </div>

          {isActive && (
            <>
              {/* Away Message */}
              <div className="profile-field">
                <label className="profile-field-label">Away Message (optional)</label>
                <textarea
                  className="modal-input"
                  value={awayMessage}
                  onChange={(e) => setAwayMessage(e.target.value)}
                  maxLength={500}
                  placeholder="I'm currently on vacation. I'll be back soon!"
                  rows={3}
                />
                <div className="profile-bio-count">{awayMessage.length}/500</div>
              </div>

              {/* Backup Person */}
              <div className="profile-field">
                <label className="profile-field-label">Backup Person</label>
                <select
                  className="modal-input autopilot-select"
                  value={backupPersonId}
                  onChange={(e) => setBackupPersonId(e.target.value)}
                >
                  <option value="">None — don't forward urgent messages</option>
                  {contacts.map((c) => (
                    <option key={c.contact?._id || c.contact_id} value={c.contact?._id || c.contact_id}>
                      {c.contact?.display_name || c.contact?.username || "Unknown"}
                    </option>
                  ))}
                </select>
                <div className="autopilot-field-hint">
                  Urgent messages will be forwarded to this person
                </div>
              </div>

              {/* Auto-Respond Toggle */}
              <div className="autopilot-toggle-row autopilot-sub-toggle">
                <div className="autopilot-toggle-info">
                  <div>
                    <div className="autopilot-toggle-label">Auto-respond</div>
                    <div className="autopilot-toggle-desc">
                      AI answers factual questions on your behalf
                    </div>
                  </div>
                </div>
                <label className="autopilot-switch">
                  <input
                    type="checkbox"
                    checked={autoRespond}
                    onChange={(e) => setAutoRespond(e.target.checked)}
                  />
                  <span className="autopilot-slider"></span>
                </label>
              </div>

              {/* Expected Return Date */}
              <div className="profile-field">
                <label className="profile-field-label">Expected Return Date (optional)</label>
                <input
                  type="date"
                  className="modal-input"
                  value={returnDate}
                  onChange={(e) => setReturnDate(e.target.value)}
                  min={new Date().toISOString().split("T")[0]}
                />
              </div>
            </>
          )}

          {error && <div className="modal-error">{error}</div>}
        </div>

        <div className="modal-footer">
          <button className="modal-cancel-btn" onClick={onClose}>
            Cancel
          </button>
          <button
            className="modal-create-btn"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? "Saving..." : isActive ? "Activate Autopilot" : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}
