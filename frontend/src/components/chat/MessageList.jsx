import { useEffect, useRef, useMemo } from "react";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";
import { useChat } from "../../context/ChatContext";
import { useAuth } from "../../context/AuthContext";

export default function MessageList() {
  const { messages, loadingMessages, activeConversation, typingUsers } = useChat();
  const { user } = useAuth();
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typingUsers]);

  // Build a name lookup from participants
  const participantMap = useMemo(() => {
    const map = {};
    if (activeConversation?.participants) {
      for (const p of activeConversation.participants) {
        map[p._id] = p.display_name || p.username || "Unknown";
      }
    }
    return map;
  }, [activeConversation?.participants]);

  const convTyping = activeConversation
    ? typingUsers[activeConversation._id]
    : null;
  const typingList = convTyping
    ? [...convTyping].filter((id) => id !== user?._id)
    : [];

  const isGroup = activeConversation?.type === "group";

  if (loadingMessages) {
    return (
      <div className="message-list">
        <div className="message-list-empty">Loading messages...</div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.length === 0 && (
        <div className="message-list-empty">
          <p>No messages yet. Say hello!</p>
        </div>
      )}
      {messages.map((msg) => (
        <MessageBubble
          key={msg._id}
          message={msg}
          showSender={isGroup}
          senderName={participantMap[msg.sender_id] || ""}
        />
      ))}
      {typingList.length > 0 && <TypingIndicator />}
      <div ref={endRef} />
    </div>
  );
}
