import { useEffect, useRef, useMemo, useState, useCallback } from "react";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";
import { useChat } from "../../context/ChatContext";
import { useAuth } from "../../context/AuthContext";
import { FaArrowDown } from "react-icons/fa";

function DateSeparator({ date }) {
  const label = (() => {
    const d = new Date(date);
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);
    if (d.toDateString() === today.toDateString()) return "Today";
    if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
    return d.toLocaleDateString(undefined, { month: "long", day: "numeric", year: d.getFullYear() !== today.getFullYear() ? "numeric" : undefined });
  })();
  return <div className="msg-date-separator"><span>{label}</span></div>;
}

export default function MessageList() {
  const { messages, loadingMessages, activeConversation, typingUsers } = useChat();
  const { user } = useAuth();
  const endRef = useRef(null);
  const listRef = useRef(null);
  const [showJumpBtn, setShowJumpBtn] = useState(false);

  const scrollToBottom = useCallback((smooth = true) => {
    endRef.current?.scrollIntoView({ behavior: smooth ? "smooth" : "auto" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    const handleScroll = () => {
      const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      setShowJumpBtn(distFromBottom > 200);
    };
    el.addEventListener("scroll", handleScroll, { passive: true });
    return () => el.removeEventListener("scroll", handleScroll);
  }, []);

  const participantMap = useMemo(() => {
    const map = {};
    if (activeConversation?.participants) {
      for (const p of activeConversation.participants) {
        map[p._id] = p.display_name || p.username || "Unknown";
      }
    }
    return map;
  }, [activeConversation?.participants]);

  const convTyping = activeConversation ? typingUsers[activeConversation._id] : null;
  const typingList = convTyping ? [...convTyping].filter(id => id !== user?._id) : [];
  const typingNames = typingList.map(id => participantMap[id] || "Someone");
  const typingText = typingNames.length === 1
    ? `${typingNames[0]} is typing`
    : typingNames.length === 2
    ? `${typingNames[0]} and ${typingNames[1]} are typing`
    : typingNames.length > 2
    ? "Several people are typing"
    : "";

  const isGroup = activeConversation?.type === "group";

  // Build messages with date separators
  const messagesWithDates = useMemo(() => {
    const result = [];
    let lastDate = null;
    for (const msg of messages) {
      const msgDate = msg.created_at ? new Date(msg.created_at).toDateString() : null;
      if (msgDate && msgDate !== lastDate) {
        result.push({ type: "separator", date: msg.created_at, key: `sep-${msg.created_at}` });
        lastDate = msgDate;
      }
      result.push({ type: "message", msg, key: msg._id });
    }
    return result;
  }, [messages]);

  if (loadingMessages) {
    return (
      <div className="message-list">
        <div className="msg-skeleton-wrap">
          {[...Array(5)].map((_, i) => (
            <div key={i} className={`msg-skeleton ${i % 2 === 0 ? "msg-skeleton-mine" : "msg-skeleton-theirs"}`}>
              <div className="msg-skeleton-bubble" style={{ width: `${40 + (i * 17) % 40}%` }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="message-list" ref={listRef}>
      {messages.length === 0 && (
        <div className="message-list-empty">
          <div className="msg-empty-icon">💬</div>
          <p>No messages yet</p>
          <span>Be the first to say something!</span>
        </div>
      )}

      {messagesWithDates.map(item =>
        item.type === "separator"
          ? <DateSeparator key={item.key} date={item.date} />
          : <MessageBubble
              key={item.key}
              message={item.msg}
              showSender={isGroup}
              senderName={participantMap[item.msg.sender_id] || ""}
            />
      )}

      {typingList.length > 0 && (
        <div className="typing-row">
          <TypingIndicator />
          {typingText && <span className="typing-name-label">{typingText}...</span>}
        </div>
      )}

      {showJumpBtn && (
        <button className="jump-to-bottom-btn" onClick={() => scrollToBottom(true)} title="Jump to latest">
          <FaArrowDown size={14} />
        </button>
      )}

      <div ref={endRef} />
    </div>
  );
}
