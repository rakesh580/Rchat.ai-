import Avatar from "../common/Avatar";
import { formatTime } from "../../utils/formatTime";
import { useAuth } from "../../context/AuthContext";
import { useSocket } from "../../context/SocketContext";
import { useChat } from "../../context/ChatContext";

const AP_PREFIX = "[Auto-reply via Autopilot] ";

export default function ConversationItem({ conversation, isActive, onClick }) {
  const { user } = useAuth();
  const { onlineUsers } = useSocket();
  const { typingUsers } = useChat();

  const otherParticipant = conversation.type === "direct"
    ? conversation.participants.find(p => p._id !== user?._id)
    : null;

  const name = conversation.type === "direct"
    ? otherParticipant?.display_name || otherParticipant?.username || "Unknown"
    : conversation.group_name || "Group";

  const isOnline = otherParticipant
    ? otherParticipant.is_bot || onlineUsers.has(otherParticipant._id)
    : false;

  const isBot = otherParticipant?.is_bot || false;

  // Typing indicator
  const convTyping = typingUsers[conversation._id];
  const someoneTyping = convTyping && [...convTyping].some(id => id !== user?._id);

  const lastMsg = conversation.last_message;
  let lastMsgPreview = "No messages yet";
  if (someoneTyping) {
    lastMsgPreview = "typing...";
  } else if (lastMsg?.content) {
    let content = lastMsg.content;
    if (content.startsWith(AP_PREFIX)) content = "🤖 " + content.replace(AP_PREFIX, "");
    lastMsgPreview = content.length > 40 ? content.substring(0, 40) + "…" : content;
  }

  const timeStr = lastMsg?.created_at || lastMsg?.timestamp;

  return (
    <div className={`conversation-item ${isActive ? "active" : ""}`} onClick={onClick}>
      <Avatar name={name} isOnline={isOnline} isBot={isBot} size={48} />
      <div className="conversation-info">
        <div className="conversation-top">
          <span className="conversation-name">{name}</span>
          {timeStr && <span className="conversation-time">{formatTime(timeStr)}</span>}
        </div>
        <div className="conversation-bottom">
          <span className={`conversation-last-msg ${someoneTyping ? "conv-typing-preview" : ""}`}>
            {lastMsgPreview}
          </span>
          {conversation.unread_count > 0 && (
            <span className="unread-badge">{conversation.unread_count > 99 ? "99+" : conversation.unread_count}</span>
          )}
        </div>
      </div>
    </div>
  );
}
