import { useState, useEffect } from "react";
import { FaTimes, FaExclamationTriangle, FaTasks, FaInfoCircle, FaRobot, FaShareSquare } from "react-icons/fa";
import { useAuth } from "../context/AuthContext";
import { useChat } from "../context/ChatContext";
import { api } from "../api";

export default function AutopilotBriefing({ onClose }) {
  const { token } = useAuth();
  const { selectConversation, conversations } = useChat();
  const [briefing, setBriefing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dismissing, setDismissing] = useState(false);

  useEffect(() => {
    fetchBriefing();
  }, []);

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
    const convo = conversations.find((c) => c._id === conversationId);
    if (convo) {
      selectConversation(convo);
      onClose();
    }
  };

  const formatTime = (dateStr) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  if (loading) {
    return (
      <div className="autopilot-briefing-overlay">
        <div className="autopilot-briefing-panel">
          <div style={{ textAlign: "center", padding: "60px 20px" }}>Loading briefing...</div>
        </div>
      </div>
    );
  }

  if (!briefing || briefing.total_messages === 0) {
    return (
      <div className="autopilot-briefing-overlay" onClick={onClose}>
        <div className="autopilot-briefing-panel" onClick={(e) => e.stopPropagation()}>
          <div className="briefing-header">
            <h4><FaRobot style={{ marginRight: 8 }} />Welcome Back!</h4>
            <button className="modal-close-btn" onClick={onClose}><FaTimes size={18} /></button>
          </div>
          <div style={{ textAlign: "center", padding: "60px 20px", opacity: 0.6 }}>
            No messages were received while you were away.
          </div>
          <div className="briefing-footer">
            <button className="modal-create-btn" onClick={onClose}>Got it</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="autopilot-briefing-overlay" onClick={onClose}>
      <div className="autopilot-briefing-panel" onClick={(e) => e.stopPropagation()}>
        <div className="briefing-header">
          <h4><FaRobot style={{ marginRight: 8 }} />Welcome Back!</h4>
          <button className="modal-close-btn" onClick={onClose}><FaTimes size={18} /></button>
        </div>

        <div className="briefing-subheader">
          Here's what happened while you were away
        </div>

        {/* Stats */}
        <div className="briefing-stats">
          <div className="briefing-stat">
            <span className="briefing-stat-num">{briefing.total_messages}</span>
            <span className="briefing-stat-label">Messages</span>
          </div>
          <div className="briefing-stat">
            <span className="briefing-stat-num">{briefing.auto_responses_sent}</span>
            <span className="briefing-stat-label">Auto-replies</span>
          </div>
          <div className="briefing-stat">
            <span className="briefing-stat-num">{briefing.messages_forwarded}</span>
            <span className="briefing-stat-label">Forwarded</span>
          </div>
        </div>

        <div className="briefing-body">
          {/* Urgent */}
          {briefing.urgent.length > 0 && (
            <div className="briefing-section">
              <div className="briefing-section-title briefing-urgent">
                <FaExclamationTriangle size={14} /> Urgent ({briefing.urgent.length})
              </div>
              {briefing.urgent.map((item) => (
                <div
                  key={item._id || item.id}
                  className="briefing-item briefing-item-urgent"
                  onClick={() => handleItemClick(item.conversation_id)}
                >
                  <div className="briefing-item-sender">{item.sender_name}</div>
                  <div className="briefing-item-action">
                    {item.action_taken === "forwarded" && <><FaShareSquare size={11} /> Forwarded to backup</>}
                    {item.action_taken === "auto_responded" && <><FaRobot size={11} /> Auto-replied</>}
                  </div>
                  <div className="briefing-item-time">{formatTime(item.created_at)}</div>
                </div>
              ))}
            </div>
          )}

          {/* Action Needed */}
          {briefing.action_needed.length > 0 && (
            <div className="briefing-section">
              <div className="briefing-section-title briefing-action">
                <FaTasks size={14} /> Action Needed ({briefing.action_needed.length})
              </div>
              {briefing.action_needed.map((item) => (
                <div
                  key={item._id || item.id}
                  className="briefing-item briefing-item-action"
                  onClick={() => handleItemClick(item.conversation_id)}
                >
                  <div className="briefing-item-sender">{item.sender_name}</div>
                  <div className="briefing-item-action">
                    {item.deadline && `Suggested deadline: ${formatTime(item.deadline)}`}
                  </div>
                  <div className="briefing-item-time">{formatTime(item.created_at)}</div>
                </div>
              ))}
            </div>
          )}

          {/* Informational */}
          {briefing.informational.length > 0 && (
            <div className="briefing-section">
              <div className="briefing-section-title briefing-info">
                <FaInfoCircle size={14} /> Informational ({briefing.informational.length})
              </div>
              {briefing.informational.map((item) => (
                <div
                  key={item._id || item.id}
                  className="briefing-item briefing-item-info"
                  onClick={() => handleItemClick(item.conversation_id)}
                >
                  <div className="briefing-item-sender">{item.sender_name}</div>
                  <div className="briefing-item-time">{formatTime(item.created_at)}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="briefing-footer">
          <button
            className="modal-create-btn"
            onClick={handleDismiss}
            disabled={dismissing}
          >
            {dismissing ? "Dismissing..." : "Dismiss All"}
          </button>
        </div>
      </div>
    </div>
  );
}
