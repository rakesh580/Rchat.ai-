import { FaArrowLeft } from "react-icons/fa";
import Avatar from "../common/Avatar";
import { useAuth } from "../../context/AuthContext";
import { useSocket } from "../../context/SocketContext";
import { useChat } from "../../context/ChatContext";

export default function ChatHeader({ onBack, onGroupInfoToggle }) {
  const { user } = useAuth();
  const { onlineUsers } = useSocket();
  const { activeConversation, typingUsers } = useChat();

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
        <Avatar name={name} isOnline={isOnline} isBot={isBot} size={40} />
        <div className="chat-header-info">
          <span className="chat-header-name">{name}</span>
          <span
            className={`chat-header-status ${someoneTyping ? "typing" : ""}`}
          >
            {statusText}
          </span>
        </div>
      </div>
    </div>
  );
}
