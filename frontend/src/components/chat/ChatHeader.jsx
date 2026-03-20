import { useState, useEffect } from "react";
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

  const otherParticipant =
    !isGroup
      ? activeConversation.participants.find((p) => p._id !== user?._id)
      : null;

  const name = isGroup
    ? activeConversation.group_name || "Group"
    : otherParticipant?.display_name || otherParticipant?.username || "Unknown";

  const isOnline = otherParticipant
    ? otherParticipant.is_bot || onlineUsers.has(otherParticipant._id)
    : false;

  const isBot = otherParticipant?.is_bot || false;

  // Fetch autopilot status for direct conversations
  useEffect(() => {
    setAutopilotStatus(null);
    if (!isGroup && otherParticipant && !isBot && token) {
      api(`/autopilot/status/${otherParticipant._id}`, { token })
        .then((data) => setAutopilotStatus(data))
        .catch(() => setAutopilotStatus(null));
    }
  }, [otherParticipant?._id, isGroup, isBot, token]);

  const convTyping = typingUsers[activeConversation._id];
  const someoneTyping = convTyping && convTyping.size > 0;

  let statusText = "";
  if (someoneTyping) {
    statusText = "typing...";
  } else if (isGroup) {
    const count = activeConversation.participants.length;
    const onlineCount = activeConversation.participants.filter(
      (p) => p.is_bot || onlineUsers.has(p._id)
    ).length;
    statusText = `${count} members, ${onlineCount} online`;
  } else if (isBot) {
    statusText = "Always online";
  } else if (isOnline) {
    statusText = "Online";
  } else {
    statusText = "Offline";
  }

  const handleHeaderClick = () => {
    if (isGroup && onGroupInfoToggle) {
      onGroupInfoToggle();
    }
  };

  return (
    <div className="chat-header">
      <button className="back-btn" onClick={onBack}>
        <FaArrowLeft size={18} />
      </button>
      <div
        className={`chat-header-clickable ${isGroup ? "clickable" : ""}`}
        onClick={handleHeaderClick}
      >
        <Avatar name={name} isOnline={isOnline} isBot={isBot} size={40} isAutopilot={autopilotStatus?.is_autopilot} />
        <div className="chat-header-info">
          <span className="chat-header-name">{name}</span>
          <span
            className={`chat-header-status ${someoneTyping ? "typing" : ""}`}
          >
            {statusText}
          </span>
        </div>
      </div>
      {autopilotStatus?.is_autopilot && (
        <div className="autopilot-banner">
          <FaRobot size={13} />
          <span>
            Autopilot active
            {autopilotStatus.away_message && ` — ${autopilotStatus.away_message}`}
            {autopilotStatus.expected_return_date && ` (back ${new Date(autopilotStatus.expected_return_date).toLocaleDateString()})`}
          </span>
        </div>
      )}
    </div>
  );
}
