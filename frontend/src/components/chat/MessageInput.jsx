import { useState, useRef, useCallback, useEffect } from "react";
import { FaPaperPlane } from "react-icons/fa";
import { useChat } from "../../context/ChatContext";

export default function MessageInput() {
  const { sendMessage, activeConversation, startTyping, stopTyping } = useChat();
  const [text, setText] = useState("");
  const typingTimerRef = useRef(null);
  const isTypingRef = useRef(false);
  const textareaRef = useRef(null);
  const MAX = 5000;

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    const lineHeight = 22;
    const maxHeight = lineHeight * 5 + 20;
    ta.style.height = Math.min(ta.scrollHeight, maxHeight) + "px";
  }, [text]);

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

  const handleSend = useCallback(() => {
    const content = text.trim();
    if (!content) return;
    sendMessage(content);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    if (isTypingRef.current) {
      isTypingRef.current = false;
      stopTyping(activeConversation._id);
      clearTimeout(typingTimerRef.current);
    }
  }, [text, sendMessage, activeConversation, stopTyping]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const charsLeft = MAX - text.length;
  const showCounter = text.length > 4500;

  return (
    <div className="message-input-bar">
      <div className="message-input-wrap">
        <textarea
          ref={textareaRef}
          className="message-input message-textarea"
          placeholder="Type a message... (Enter to send, Shift+Enter for newline)"
          value={text}
          maxLength={MAX}
          rows={1}
          onChange={e => { setText(e.target.value); handleTyping(); }}
          onKeyDown={handleKeyDown}
        />
        {showCounter && (
          <div className={`msg-char-counter ${charsLeft < 100 ? "msg-char-counter-warn" : ""}`}>
            {charsLeft}
          </div>
        )}
      </div>
      <button
        type="button"
        className="message-send-btn"
        disabled={!text.trim()}
        onClick={handleSend}
        aria-label="Send message"
      >
        <FaPaperPlane size={18} />
      </button>
    </div>
  );
}
