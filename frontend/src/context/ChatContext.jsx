import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { useAuth } from "./AuthContext";
import { useSocket } from "./SocketContext";
import { api } from "../api";

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const { token, user } = useAuth();
  const { socket } = useSocket();
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [typingUsers, setTypingUsers] = useState({});
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);

  // Load conversations
  useEffect(() => {
    if (!token) return;
    api("/conversations", { token })
      .then((data) => {
        setConversations(data);
        setLoadingConversations(false);
      })
      .catch(() => setLoadingConversations(false));
  }, [token]);

  // Load messages when active conversation changes
  useEffect(() => {
    if (!activeConversation || !token) {
      setMessages([]);
      return;
    }
    setLoadingMessages(true);
    api(`/conversations/${activeConversation._id}/messages`, { token })
      .then((data) => {
        setMessages(data);
        setLoadingMessages(false);
        if (socket) {
          socket.emit("message_read", {
            conversation_id: activeConversation._id,
          });
        }
      })
      .catch(() => setLoadingMessages(false));
  }, [activeConversation?._id, token]);

  // Socket event listeners
  useEffect(() => {
    if (!socket) return;

    const handleNewMessage = (msg) => {
      // Clear typing indicator for the sender (especially AI bot)
      setTypingUsers((prev) => {
        const convTyping = prev[msg.conversation_id];
        if (convTyping && convTyping.has(msg.sender_id)) {
          const next = new Set(convTyping);
          next.delete(msg.sender_id);
          return { ...prev, [msg.conversation_id]: next };
        }
        return prev;
      });

      // Update messages if in active conversation
      if (activeConversation && msg.conversation_id === activeConversation._id) {
        setMessages((prev) => {
          // Check duplicates by _id or temp_id
          if (prev.some((m) => m._id === msg._id || (m.temp_id && m._id === msg._id))) return prev;
          return [...prev, msg];
        });
        socket.emit("message_read", {
          conversation_id: msg.conversation_id,
        });
      }

      // Update conversation sidebar
      setConversations((prev) =>
        prev
          .map((c) => {
            if (c._id === msg.conversation_id) {
              return {
                ...c,
                last_message: {
                  content: msg.content,
                  sender_id: msg.sender_id,
                  created_at: msg.created_at,
                },
                updated_at: msg.created_at,
                unread_count:
                  activeConversation?._id === msg.conversation_id
                    ? 0
                    : (c.unread_count || 0) +
                      (msg.sender_id !== user?._id ? 1 : 0),
              };
            }
            return c;
          })
          .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
      );
    };

    const handleMessageSent = (data) => {
      setMessages((prev) =>
        prev.map((m) => {
          if (m.temp_id === data.temp_id) {
            return {
              ...m,
              _id: data.message_id,
              created_at: data.created_at,
              status: "sent",
            };
          }
          return m;
        })
      );
    };

    const handleTypingIndicator = ({ conversation_id, user_id, is_typing }) => {
      setTypingUsers((prev) => {
        const convTyping = new Set(prev[conversation_id] || []);
        if (is_typing) {
          convTyping.add(user_id);
        } else {
          convTyping.delete(user_id);
        }
        return { ...prev, [conversation_id]: convTyping };
      });
    };

    const handleAiTyping = ({ conversation_id }) => {
      setTypingUsers((prev) => {
        const convTyping = new Set(prev[conversation_id] || []);
        convTyping.add("000000000000000000000001");
        return { ...prev, [conversation_id]: convTyping };
      });
    };

    const handleReadReceipt = ({ conversation_id, reader_id }) => {
      setMessages((prev) =>
        prev.map((m) => {
          if (
            m.conversation_id === conversation_id &&
            !m.read_by?.includes(reader_id)
          ) {
            return {
              ...m,
              read_by: [...(m.read_by || []), reader_id],
              status: "read",
            };
          }
          return m;
        })
      );
    };

    const handleMessageStatus = ({ message_id, status }) => {
      setMessages((prev) =>
        prev.map((m) => {
          if (m._id === message_id) {
            return { ...m, status };
          }
          return m;
        })
      );
    };

    const handleConversationNew = () => {
      // A new group was created that includes us — refresh conversations
      if (token) {
        api("/conversations", { token })
          .then((data) => setConversations(data))
          .catch(() => {});
      }
    };

    socket.on("message:new", handleNewMessage);
    socket.on("message:sent", handleMessageSent);
    socket.on("typing:indicator", handleTypingIndicator);
    socket.on("ai:typing", handleAiTyping);
    socket.on("message:read_receipt", handleReadReceipt);
    socket.on("message:status", handleMessageStatus);
    socket.on("conversation:new", handleConversationNew);

    return () => {
      socket.off("message:new", handleNewMessage);
      socket.off("message:sent", handleMessageSent);
      socket.off("typing:indicator", handleTypingIndicator);
      socket.off("ai:typing", handleAiTyping);
      socket.off("message:read_receipt", handleReadReceipt);
      socket.off("message:status", handleMessageStatus);
      socket.off("conversation:new", handleConversationNew);
    };
  }, [socket, activeConversation?._id, user?._id, token]);

  const sendMessage = useCallback(
    (content) => {
      if (!socket || !activeConversation) return;
      const tempId = `temp_${Date.now()}`;

      const optimisticMsg = {
        _id: tempId,
        temp_id: tempId,
        conversation_id: activeConversation._id,
        sender_id: user?._id,
        content,
        message_type: "text",
        status: "sending",
        read_by: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticMsg]);

      socket.emit("message_send", {
        conversation_id: activeConversation._id,
        content,
        temp_id: tempId,
      });
    },
    [socket, activeConversation, user]
  );

  const startTyping = useCallback(
    (conversationId) => {
      if (socket) socket.emit("typing_start", { conversation_id: conversationId });
    },
    [socket]
  );

  const stopTyping = useCallback(
    (conversationId) => {
      if (socket) socket.emit("typing_stop", { conversation_id: conversationId });
    },
    [socket]
  );

  const selectConversation = useCallback((convo) => {
    setActiveConversation(convo);
    if (convo) {
      setConversations((prev) =>
        prev.map((c) => (c._id === convo._id ? { ...c, unread_count: 0 } : c))
      );
    }
  }, []);

  // Update browser tab title with unread count
  useEffect(() => {
    const totalUnread = conversations.reduce(
      (sum, c) => sum + (c.unread_count || 0),
      0
    );
    document.title = totalUnread > 0 ? `(${totalUnread}) Rchat.ai` : "Rchat.ai";
  }, [conversations]);

  const refreshConversations = useCallback(async () => {
    if (!token) return;
    try {
      const data = await api("/conversations", { token });
      setConversations(data);
    } catch {
      // ignore
    }
  }, [token]);

  return (
    <ChatContext.Provider
      value={{
        conversations,
        activeConversation,
        messages,
        typingUsers,
        loadingConversations,
        loadingMessages,
        sendMessage,
        startTyping,
        stopTyping,
        selectConversation,
        setConversations,
        refreshConversations,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
