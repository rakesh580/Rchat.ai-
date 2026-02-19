import { useState, useEffect } from "react";
import { FaUsers } from "react-icons/fa";
import SearchBar from "./SearchBar";
import UserSearchResults from "./UserSearchResults";
import ConversationItem from "./ConversationItem";
import CreateGroupModal from "../groups/CreateGroupModal";
import StatusCarousel from "../status/StatusCarousel";
import { useChat } from "../../context/ChatContext";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../api";

export default function Sidebar({ onConversationSelect }) {
  const { token } = useAuth();
  const {
    conversations,
    activeConversation,
    selectConversation,
    refreshConversations,
    loadingConversations,
  } = useChat();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showGroupModal, setShowGroupModal] = useState(false);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const results = await api(
          `/users/search?q=${encodeURIComponent(searchQuery)}`,
          { token }
        );
        setSearchResults(results);
      } catch {
        setSearchResults([]);
      }
      setSearchLoading(false);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, token]);

  const handleUserSelect = async (selectedUser) => {
    setSearchQuery("");
    setSearchResults([]);
    try {
      await api("/conversations", {
        method: "POST",
        body: { participant_ids: [selectedUser._id], type: "direct" },
        token,
      });
      const data = await api("/conversations", { token });
      const convo = data.find(
        (c) =>
          c.type === "direct" &&
          c.participants.some((p) => p._id === selectedUser._id)
      );
      if (convo) {
        selectConversation(convo);
        if (onConversationSelect) onConversationSelect();
      }
      await refreshConversations();
    } catch (err) {
      /* failed silently */
    }
  };

  const handleConversationClick = (convo) => {
    selectConversation(convo);
    if (onConversationSelect) onConversationSelect();
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h5 className="sidebar-title">Chats</h5>
        <button
          className="new-group-btn"
          onClick={() => setShowGroupModal(true)}
          title="New Group"
        >
          <FaUsers size={16} />
        </button>
      </div>
      <StatusCarousel />
      <SearchBar value={searchQuery} onChange={setSearchQuery} />
      {searchResults.length > 0 && (
        <UserSearchResults
          results={searchResults}
          onSelect={handleUserSelect}
          loading={searchLoading}
        />
      )}
      <div className="conversation-list">
        {loadingConversations ? (
          <div className="sidebar-empty">Loading...</div>
        ) : conversations.length === 0 ? (
          <div className="sidebar-empty">
            No conversations yet. Search for users to start chatting!
          </div>
        ) : (
          conversations.map((convo) => (
            <ConversationItem
              key={convo._id}
              conversation={convo}
              isActive={activeConversation?._id === convo._id}
              onClick={() => handleConversationClick(convo)}
            />
          ))
        )}
      </div>
      {showGroupModal && (
        <CreateGroupModal onClose={() => setShowGroupModal(false)} />
      )}
    </div>
  );
}
