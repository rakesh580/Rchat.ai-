import { useState, useEffect } from "react";
import { FaTimes, FaRobot, FaSearch, FaEdit, FaExclamationTriangle, FaClipboardList, FaCog, FaBolt, FaChevronDown, FaChevronUp } from "react-icons/fa";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

const CAPABILITIES = [
  { icon: "🔍", title: "Classify Urgency", desc: "Reads every message and tags it urgent, action needed, or informational" },
  { icon: "✍️", title: "Auto-Compose Replies", desc: "Writes polished, context-aware replies in your voice" },
  { icon: "🚨", title: "Forward Urgent", desc: "Instantly notifies your backup person when something can't wait" },
  { icon: "📋", title: "Log All Activity", desc: "Keeps a full record so you're briefed the moment you return" },
];

const TONES = ["Professional", "Casual", "Concise"];

export default function AutopilotModal({ onClose, onDeactivated }) {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState("settings");
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
  const [tone, setTone] = useState(() => localStorage.getItem("autopilot_tone") || "Professional");
  const [showHowItWorks, setShowHowItWorks] = useState(false);
  const [recentActivity, setRecentActivity] = useState([]);
  const [activityLoading, setActivityLoading] = useState(false);

  useEffect(() => { loadData(); }, []);

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
    } catch {
      setError("Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const loadActivity = async () => {
    setActivityLoading(true);
    try {
      const data = await api("/autopilot/briefing", { token });
      const all = [...(data.urgent || []), ...(data.action_needed || []), ...(data.informational || [])];
      all.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setRecentActivity(all.slice(0, 5));
    } catch {
      setRecentActivity([]);
    } finally {
      setActivityLoading(false);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === "activity" && recentActivity.length === 0) loadActivity();
  };

  const handleToneChange = (t) => {
    setTone(t);
    localStorage.setItem("autopilot_tone", t);
  };

  const handleSave = async () => {
    setError("");
    setSaving(true);
    try {
      await api("/autopilot/settings", {
        method: "PUT", token,
        body: {
          is_active: isActive,
          away_message: awayMessage.trim(),
          backup_person_id: backupPersonId || null,
          auto_respond_enabled: autoRespond,
          expected_return_date: returnDate ? new Date(returnDate).toISOString() : null,
        },
      });
      if (wasActive && !isActive && onDeactivated) onDeactivated();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const formatTime = (d) => d ? new Date(d).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "";
  const actionLabel = { forwarded: "Forwarded", auto_responded: "Auto-replied", queued: "Queued", logged: "Logged" };

  if (loading) return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content autopilot-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-body" style={{ textAlign: "center", padding: "40px" }}>
          <div className="ap-spinner" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content autopilot-modal autopilot-modal-v2" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <h5><FaRobot style={{ marginRight: 8, color: "var(--accent)" }} />Conversation Autopilot</h5>
          <button className="modal-close-btn" onClick={onClose}><FaTimes size={18} /></button>
        </div>

        {/* Tabs */}
        <div className="ap-tabs">
          {["settings", "agent", "activity"].map(tab => (
            <button
              key={tab}
              className={`ap-tab ${activeTab === tab ? "ap-tab-active" : ""}`}
              onClick={() => handleTabChange(tab)}
            >
              {tab === "settings" && <FaCog size={13} />}
              {tab === "agent" && <FaBolt size={13} />}
              {tab === "activity" && <FaClipboardList size={13} />}
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="modal-body ap-tab-body">

          {/* ── SETTINGS TAB ── */}
          {activeTab === "settings" && (
            <>
              <div className="autopilot-toggle-row">
                <div className="autopilot-toggle-info">
                  <div>
                    <div className="autopilot-toggle-label" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {isActive ? "Autopilot Active" : "Autopilot Off"}
                      {isActive && <span className="ap-status-chip">● Live</span>}
                    </div>
                    <div className="autopilot-toggle-desc">AI agent handles your messages while you're away</div>
                  </div>
                </div>
                <label className="autopilot-switch">
                  <input type="checkbox" checked={isActive} onChange={e => setIsActive(e.target.checked)} />
                  <span className="autopilot-slider" />
                </label>
              </div>

              {isActive && (<>
                <div className="profile-field">
                  <label className="profile-field-label">Away Message (optional)</label>
                  <textarea className="modal-input" value={awayMessage} onChange={e => setAwayMessage(e.target.value)} maxLength={500} placeholder="I'm currently on vacation. I'll be back soon!" rows={3} />
                  <div className="profile-bio-count">{awayMessage.length}/500</div>
                </div>

                <div className="profile-field">
                  <label className="profile-field-label">Backup Person</label>
                  <select className="modal-input autopilot-select" value={backupPersonId} onChange={e => setBackupPersonId(e.target.value)}>
                    <option value="">None — don't forward urgent messages</option>
                    {contacts.map(c => (
                      <option key={c.contact?._id || c.contact_id} value={c.contact?._id || c.contact_id}>
                        {c.contact?.display_name || c.contact?.username || "Unknown"}
                      </option>
                    ))}
                  </select>
                  <div className="autopilot-field-hint">Urgent messages will be forwarded to this person</div>
                </div>

                <div className="autopilot-toggle-row autopilot-sub-toggle">
                  <div className="autopilot-toggle-info">
                    <div>
                      <div className="autopilot-toggle-label">Auto-respond to messages</div>
                      <div className="autopilot-toggle-desc">Agent composes and sends replies on your behalf</div>
                    </div>
                  </div>
                  <label className="autopilot-switch">
                    <input type="checkbox" checked={autoRespond} onChange={e => setAutoRespond(e.target.checked)} />
                    <span className="autopilot-slider" />
                  </label>
                </div>

                <div className="profile-field">
                  <label className="profile-field-label">Expected Return Date (optional)</label>
                  <input type="date" className="modal-input" value={returnDate} onChange={e => setReturnDate(e.target.value)} min={new Date().toISOString().split("T")[0]} />
                </div>
              </>)}
              {error && <div className="modal-error">{error}</div>}
            </>
          )}

          {/* ── AGENT TAB ── */}
          {activeTab === "agent" && (
            <>
              <div className="ap-capabilities-header">
                <span>What the agent does for you</span>
                <span className="ap-model-badge">LangGraph · llama-3.3-70b</span>
              </div>
              <div className="ap-capabilities-grid">
                {CAPABILITIES.map(cap => (
                  <div key={cap.title} className="ap-capability-card">
                    <div className="ap-cap-icon">{cap.icon}</div>
                    <div className="ap-cap-title">{cap.title}</div>
                    <div className="ap-cap-desc">{cap.desc}</div>
                  </div>
                ))}
              </div>

              <div className="profile-field" style={{ marginTop: 20 }}>
                <label className="profile-field-label">Response Tone</label>
                <div className="ap-tone-pills">
                  {TONES.map(t => (
                    <button key={t} className={`ap-tone-pill ${tone === t ? "active" : ""}`} onClick={() => handleToneChange(t)}>{t}</button>
                  ))}
                </div>
                <div className="autopilot-field-hint">How the agent writes replies on your behalf</div>
              </div>

              <div className="ap-how-it-works">
                <button className="ap-how-toggle" onClick={() => setShowHowItWorks(v => !v)}>
                  How does it work? {showHowItWorks ? <FaChevronUp size={11} /> : <FaChevronDown size={11} />}
                </button>
                {showHowItWorks && (
                  <div className="ap-how-body">
                    When someone messages you, the agent runs a <strong>7-step LangGraph pipeline</strong>: it loads your context, sanitizes the message for privacy, classifies urgency, optionally forwards to your backup, composes a reply if needed, sends it on your behalf, and logs everything for your briefing.
                  </div>
                )}
              </div>
            </>
          )}

          {/* ── ACTIVITY TAB ── */}
          {activeTab === "activity" && (
            <>
              <div className="ap-activity-header">Recent Agent Actions</div>
              {activityLoading ? (
                <div style={{ textAlign: "center", padding: "40px", opacity: 0.5 }}>Loading activity...</div>
              ) : recentActivity.length === 0 ? (
                <div className="ap-activity-empty">
                  <FaClipboardList size={32} style={{ opacity: 0.2, marginBottom: 10 }} />
                  <div>No activity yet.</div>
                  <div style={{ fontSize: "0.8rem", opacity: 0.5 }}>Activity appears here once the agent handles messages.</div>
                </div>
              ) : (
                <div className="ap-activity-list">
                  {recentActivity.map((item, i) => (
                    <div key={item._id || i} className="ap-activity-item">
                      <div className="ap-activity-dot" data-cat={item.category} />
                      <div className="ap-activity-content">
                        <span className="ap-activity-sender">{item.sender_name || "Someone"}</span>
                        <span className="ap-activity-action">{actionLabel[item.action_taken] || item.action_taken}</span>
                      </div>
                      <div className="ap-activity-time">{formatTime(item.created_at)}</div>
                    </div>
                  ))}
                </div>
              )}
              <button className="ap-refresh-btn" onClick={loadActivity}>Refresh</button>
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="modal-cancel-btn" onClick={onClose}>Cancel</button>
          {activeTab === "settings" && (
            <button className="modal-create-btn" onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : isActive ? "Activate Autopilot" : "Save Changes"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
