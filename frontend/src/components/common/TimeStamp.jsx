import { formatMessageTime } from "../../utils/formatTime";

export default function TimeStamp({ dateStr }) {
  return <span className="timestamp">{formatMessageTime(dateStr)}</span>;
}
