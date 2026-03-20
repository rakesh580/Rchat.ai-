import { useState, useEffect, useMemo } from "react";
import { FaArrowLeft, FaRobot } from "react-icons/fa";
import Avatar from "../common/Avatar";
import { useAuth } from "../../context/AuthContext";
import { useSocket } from "../../context/SocketContext";
import { useChat } from "../../context/ChatContext";
import { api } from "../../api";

export default function ChatHeader({ onBack, onGroupInfoToggle }) {
  const { user, token } = useAuth();
  const { onlineUsers } = useSocket();
  const { activeConversation, typingUsers } = useChat();
  const [autopilotStatus, setAutopilotStatus] = useState(null);

  if (!activeConversation) return null;

  const isGroup = activeConversation.type === "group";
  const otherParticipant = !isGroup
    ? activeConversation.participants.find(p => p._id !== user?._id)
    : null;

  const name = isGroup
    ? activeConversation.group_name || "Group"
    : otherParticipant?.display_name || otherParticipant?.username || "Unknown";

  const isOnline = otherParticipant
    ? otherParticipant.is_bot || onlineUsers.has(otherParticipant._id)
    : false;
  const isBot = otherParticipant?.is_bot || false;

  // Build participant name map for typing labels
  const participantMap = useMemo(() => {
    const map = {};
    for (const p of (activeConversation.participants || [])) {
      map[p._id] = p.display_name || p.username || "Someone";
    }
    return map;
  }, [activeConversation.participants]);

  useEffect(() => {
    setAutopilotStatus(null);
    if (!isGroup && otherParticipant && !isBot && token) {
      api(`/autopilot/status/${otherParticipant._id}`, { token })
        .then(data => setAutopilotStatus(data))
        .catch(() => setAutopilotStatus(null));
    }
  }, [otherParticipant?._id, isGroup, isBot, token]);

  const convTyping = typingUsers[activeConversation._id];
  const typingIds = convTyping ? [...convTyping].filter(id => id !== user?._id) : [];
  const someoneTyping = typingIds.length > 0;

  // Build typing label with names
  const typingLabel = useMemo(() => {
    if (!someoneTyping) return "";
    const names = typingIds.map(id => participantMap[id] || "Someone");
    if (names.length === 1) return `${names[0]} is typing...`;
    if (names.length === 2) return `${names[0]} and ${names[1]} are typing...`;
    return "Several people are typing...";
  }, [typingIds, participantMap, someoneTyping]);

  let statusText = "";
  if (someoneTyping) {
    statusText = typingLabel;
  } else if (isGroup) {
    const count = activeConversation.participants.length;
    const onlineCount = activeConversation.participants.filter(p => p.is_bot || onlineUsers.has(p._id)).length;
    statusText = `${count} members · ${onlineCount} online`;
  } else if (isBot) {
    statusText = "Always online";
  } else if (isOnline) {
    statusText = "Online";
  } else {
    statusText = "Offline";
  }

  return (
    <div className="chat-header">
      <button className="back-btn" onClick={onBack} aria-label="Back">
        <FaArrowLeft size={18} />
      </button>
      <div
        className={`chat-header-clickable ${isGroup ? "clickable" : ""}`}
        onClick={isGroup && onGroupInfoToggle ? onGroupInfoToggle : undefined}
        title={isGroup ? "View group info" : undefined}
      >
        <Avatar name={name} isOnline={isOnline} isBot={isBot} size={40} isAutopilot={autopilotStatus?.is_autopilot} />
        <div className="chat-header-info">
          <span className="chat-header-name">{name}</span>
          <span className={`chat-header-status ${someoneTyping ? "typing" : ""}`}>
            {statusText}
          </span>
        </div>
      </div>
      {autopilotStatus?.is_autopilot && (
        <div className="autopilot-banner autopilot-banner-v2">
          <FaRobot size={13} />
          <div className="autopilot-banner-text">
            <span className="autopilot-banner-label">Agent Active</span>
            {autopilotStatus.away_message && (
              <span className="autopilot-banner-msg">{autopilotStatus.away_message}</span>
            )}
          </div>
          {autopilotStatus.expected_return_date && (
            <span className="autopilot-banner-return">
              Back {new Date(autopilotStatus.expected_return_date).toLocaleDateString()}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
