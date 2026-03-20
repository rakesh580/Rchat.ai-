import { useState, useCallback } from "react";
import { FaRobot, FaCopy, FaCheck } from "react-icons/fa";
import { useAuth } from "../../context/AuthContext";
import StatusTicks from "../common/StatusTicks";
import TimeStamp from "../common/TimeStamp";

const AUTOPILOT_PREFIX = "[Auto-reply via Autopilot] ";
const QUICK_REACTIONS = ["👍", "❤️", "😄", "😮", "😢"];

export default function MessageBubble({ message, showSender, senderName }) {
  const { user } = useAuth();
  const isMine = message.sender_id === user?._id;
  const isAutopilotReply = message.content?.startsWith(AUTOPILOT_PREFIX) || message.is_autopilot_reply;
  const displayContent = isAutopilotReply
    ? message.content.replace(AUTOPILOT_PREFIX, "")
    : message.content;

  const [showActions, setShowActions] = useState(false);
  const [copied, setCopied] = useState(false);
  const [reactions, setReactions] = useState({});

  const handleCopy = useCallback(async (e) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(displayContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // fallback — select text
    }
  }, [displayContent]);

  const handleReact = useCallback((emoji) => {
    setReactions(prev => {
      const count = (prev[emoji] || 0);
      if (count > 0) {
        const updated = { ...prev };
        delete updated[emoji];
        return updated;
      }
      return { ...prev, [emoji]: 1 };
    });
  }, []);

  const reactionEntries = Object.entries(reactions);

  return (
    <div
      className={`msg-bubble-wrap ${isMine ? "msg-wrap-mine" : "msg-wrap-theirs"}`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* Hover action bar */}
      {showActions && (
        <div className={`msg-actions ${isMine ? "msg-actions-mine" : "msg-actions-theirs"}`}>
          {QUICK_REACTIONS.map(emoji => (
            <button
              key={emoji}
              className={`msg-reaction-btn ${reactions[emoji] ? "active" : ""}`}
              onClick={() => handleReact(emoji)}
              title={`React ${emoji}`}
            >
              {emoji}
            </button>
          ))}
          <button className="msg-action-icon" onClick={handleCopy} title="Copy">
            {copied ? <FaCheck size={11} color="#00b894" /> : <FaCopy size={11} />}
          </button>
        </div>
      )}

      <div className={`msg-bubble ${isMine ? "msg-mine" : "msg-theirs"} ${isAutopilotReply ? "msg-autopilot" : ""}`}>
        {showSender && !isMine && senderName && (
          <div className="msg-sender-name">{senderName}</div>
        )}
        {isAutopilotReply && (
          <div className="msg-autopilot-label">
            <FaRobot size={11} /> Autopilot
          </div>
        )}
        <div className="msg-content">{displayContent}</div>
        <div className="msg-meta">
          <TimeStamp dateStr={message.created_at} />
          {isMine && <StatusTicks status={message.status} />}
        </div>
      </div>

      {/* Reaction display */}
      {reactionEntries.length > 0 && (
        <div className={`msg-reactions-bar ${isMine ? "reactions-mine" : "reactions-theirs"}`}>
          {reactionEntries.map(([emoji, count]) => (
            <button
              key={emoji}
              className="msg-reaction-chip"
              onClick={() => handleReact(emoji)}
            >
              {emoji} {count > 1 && <span>{count}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
