import { useState, useRef, useCallback } from "react";
import { FaPaperPlane } from "react-icons/fa";
import { useChat } from "../../context/ChatContext";

export default function MessageInput() {
  const { sendMessage, activeConversation, startTyping, stopTyping } = useChat();
  const [text, setText] = useState("");
  const typingTimerRef = useRef(null);
  const isTypingRef = useRef(false);

  const handleTyping = useCallback(() => {
    if (!activeConversation) return;
    if (!isTypingRef.current) {
      isTypingRef.current = true;
      startTyping(activeConversation._id);
    }
    clearTimeout(typingTimerRef.current);
    typingTimerRef.current = setTimeout(() => {
      isTypingRef.current = false;
      stopTyping(activeConversation._id);
    }, 2000);
  }, [activeConversation, startTyping, stopTyping]);

  const handleSend = (e) => {
    e.preventDefault();
    const content = text.trim();
    if (!content) return;
    sendMessage(content);
    setText("");
    if (isTypingRef.current) {
      isTypingRef.current = false;
      stopTyping(activeConversation._id);
      clearTimeout(typingTimerRef.current);
    }
  };

  return (
    <form className="message-input-bar" onSubmit={handleSend}>
      <input
        type="text"
        className="message-input"
        placeholder="Type a message..."
        value={text}
        maxLength={5000}
        onChange={(e) => {
          setText(e.target.value);
          handleTyping();
        }}
      />
      <button
        type="submit"
        className="message-send-btn"
        disabled={!text.trim()}
      >
        <FaPaperPlane size={18} />
      </button>
    </form>
  );
}
