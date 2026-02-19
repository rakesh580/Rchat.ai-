import { IoCheckmark, IoCheckmarkDone } from "react-icons/io5";

export default function StatusTicks({ status }) {
  if (status === "read")
    return <IoCheckmarkDone size={16} className="status-tick status-read" />;
  if (status === "delivered")
    return <IoCheckmarkDone size={16} className="status-tick" />;
  if (status === "sent")
    return <IoCheckmark size={16} className="status-tick" />;
  return null;
}
