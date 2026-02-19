import { useAuth } from "../../context/AuthContext";
import StatusTicks from "../common/StatusTicks";
import TimeStamp from "../common/TimeStamp";

export default function MessageBubble({ message, showSender, senderName }) {
  const { user } = useAuth();
  const isMine = message.sender_id === user?._id;

  return (
    <div className={`msg-bubble ${isMine ? "msg-mine" : "msg-theirs"}`}>
      {showSender && !isMine && senderName && (
        <div className="msg-sender-name">{senderName}</div>
      )}
      <div className="msg-content">{message.content}</div>
      <div className="msg-meta">
        <TimeStamp dateStr={message.created_at} />
        {isMine && <StatusTicks status={message.status} />}
      </div>
    </div>
  );
}
