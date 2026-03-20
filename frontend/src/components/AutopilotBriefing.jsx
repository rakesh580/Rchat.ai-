import { useState, useEffect } from "react";
import { FaTimes, FaExclamationTriangle, FaTasks, FaInfoCircle, FaRobot, FaShareSquare, FaReply } from "react-icons/fa";
import { useAuth } from "../context/AuthContext";
import { useChat } from "../context/ChatContext";
import { api } from "../api";

const CATEGORY_CONFIG = {
  urgent: { icon: <FaExclamationTriangle size={12} />, label: "Urgent", cls: "briefing-urgent" },
  action_needed: { icon: <FaTasks size={12} />, label: "Action Needed", cls: "briefing-action" },
  informational: { icon: <FaInfoCircle size={12} />, label: "Info", cls: "briefing-info" },
};

export default function AutopilotBriefing({ onClose }) {
  const { token } = useAuth();
  const { selectConversation, conversations } = useChat();
  const [briefing, setBriefing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dismissing, setDismissing] = useState(false);

  useEffect(() => { fetchBriefing(); }, []);

  const fetchBriefing = async () => {
    try {
      const data = await api("/autopilot/briefing", { token });
      setBriefing(data);
    } catch {
      setBriefing(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = async () => {
    setDismissing(true);
    try {
      await api("/autopilot/briefing/dismiss", { method: "POST", token });
      onClose();
    } catch {
      setDismissing(false);
    }
  };

  const handleItemClick = (conversationId) => {
    const convo = conversations.find(c => c._id === conversationId);
    if (convo) { selectConversation(convo); onClose(); }
  };

  const formatTime = (d) => d ? new Date(d).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "";

  const actionIcon = { forwarded: <><FaShareSquare size={10} /> Forwarded</>, auto_responded: <><FaRobot size={10} /> Auto-replied</>, queued: "Queued", logged: "Logged" };

  if (loading) return (
    <div className="autopilot-briefing-overlay">
      <div className="autopilot-briefing-panel">
        <div style={{ textAlign: "center", padding: "60px 20px" }}>
          <div className="ap-spinner" />
        </div>
      </div>
    </div>
  );

  if (!briefing || briefing.total_messages === 0) return (
    <div className="autopilot-briefing-overlay" onClick={onClose}>
      <div className="autopilot-briefing-panel" onClick={e => e.stopPropagation()}>
        <div className="briefing-header">
          <h4><FaRobot style={{ marginRight: 8 }} />Welcome Back!</h4>
          <button className="modal-close-btn" onClick={onClose}><FaTimes size={18} /></button>
        </div>
        <div className="briefing-empty">
          <div style={{ fontSize: "3rem" }}>😌</div>
          <div>All quiet while you were away.</div>
          <div style={{ opacity: 0.5, fontSize: "0.85rem", marginTop: 4 }}>No messages were received.</div>
        </div>
        <div className="briefing-footer">
          <button className="modal-create-btn" onClick={onClose}>Got it</button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="autopilot-briefing-overlay" onClick={onClose}>
      <div className="autopilot-briefing-panel" onClick={e => e.stopPropagation()}>
        <div className="briefing-header">
          <h4><FaRobot style={{ marginRight: 8 }} />Welcome Back!</h4>
          <button className="modal-close-btn" onClick={onClose}><FaTimes size={18} /></button>
        </div>
        <div className="briefing-subheader">Here's what the agent handled while you were away</div>

        <div className="briefing-stats">
          <div className="briefing-stat">
            <span className="briefing-stat-num">{briefing.total_messages}</span>
            <span className="briefing-stat-label">Messages</span>
          </div>
          <div className="briefing-stat">
            <span className="briefing-stat-num">{briefing.auto_responses_sent}</span>
            <span className="briefing-stat-label">Auto-replied</span>
          </div>
          <div className="briefing-stat">
            <span className="briefing-stat-num">{briefing.messages_forwarded}</span>
            <span className="briefing-stat-label">Forwarded</span>
          </div>
        </div>

        <div className="briefing-body">
          {["urgent", "action_needed", "informational"].map(cat => {
            const items = briefing[cat] || [];
            if (!items.length) return null;
            const cfg = CATEGORY_CONFIG[cat];
            return (
              <div key={cat} className="briefing-section">
                <div className={`briefing-section-title ${cfg.cls}`}>
                  {cfg.icon} {cfg.label} ({items.length})
                </div>
                {items.map(item => (
                  <div key={item._id || item.id} className={`briefing-item briefing-item-${cat === "action_needed" ? "action" : cat}`}>
                    <div className="briefing-item-top">
                      <span className="briefing-item-sender">{item.sender_name || "Unknown"}</span>
                      <span className="briefing-item-time">{formatTime(item.created_at)}</span>
                    </div>
                    {item.auto_response_content && (
                      <div className="briefing-item-preview">"{item.auto_response_content.substring(0, 80)}{item.auto_response_content.length > 80 ? "…" : ""}"</div>
                    )}
                    <div className="briefing-item-footer">
                      <span className="briefing-item-action">{actionIcon[item.action_taken] || item.action_taken}</span>
                      <button
                        className="briefing-reply-btn"
                        onClick={() => handleItemClick(item.conversation_id)}
                      >
                        <FaReply size={11} /> Reply
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            );
          })}
        </div>

        <div className="briefing-footer">
          <button className="modal-cancel-btn" onClick={onClose}>Close</button>
          <button className="modal-create-btn" onClick={handleDismiss} disabled={dismissing}>
            {dismissing ? "Dismissing..." : "Dismiss All"}
          </button>
        </div>
      </div>
    </div>
  );
}
