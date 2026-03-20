import { FaRobot } from "react-icons/fa";
import { useAuth } from "../../context/AuthContext";
import StatusTicks from "../common/StatusTicks";
import TimeStamp from "../common/TimeStamp";

const AUTOPILOT_PREFIX = "[Auto-reply via Autopilot] ";

export default function MessageBubble({ message, showSender, senderName }) {
  const { user } = useAuth();
  const isMine = message.sender_id === user?._id;
  const isAutopilotReply = message.content?.startsWith(AUTOPILOT_PREFIX) || message.is_autopilot_reply;
  const displayContent = isAutopilotReply
    ? message.content.replace(AUTOPILOT_PREFIX, "")
    : message.content;

  return (
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
  );
}
