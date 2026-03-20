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

function ConversationSkeleton() {
  return (
    <div className="conv-skeleton">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="conv-skeleton-item">
          <div className="conv-skeleton-avatar" />
          <div className="conv-skeleton-lines">
            <div className="conv-skeleton-name" style={{ width: `${50 + i * 10}%` }} />
            <div className="conv-skeleton-msg" style={{ width: `${30 + i * 8}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Sidebar({ onConversationSelect }) {
  const { token } = useAuth();
  const { conversations, activeConversation, selectConversation, refreshConversations, loadingConversations } = useChat();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchDone, setSearchDone] = useState(false);
  const [showGroupModal, setShowGroupModal] = useState(false);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setSearchDone(false);
      return;
    }
    setSearchDone(false);
    const timer = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const results = await api(`/users/search?q=${encodeURIComponent(searchQuery)}`, { token });
        setSearchResults(results);
      } catch {
        setSearchResults([]);
      }
      setSearchLoading(false);
      setSearchDone(true);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, token]);

  const handleUserSelect = async (selectedUser) => {
    setSearchQuery("");
    setSearchResults([]);
    setSearchDone(false);
    try {
      await api("/conversations", { method: "POST", body: { participant_ids: [selectedUser._id], type: "direct" }, token });
      const data = await api("/conversations", { token });
      const convo = data.find(c => c.type === "direct" && c.participants.some(p => p._id === selectedUser._id));
      if (convo) { selectConversation(convo); if (onConversationSelect) onConversationSelect(); }
      await refreshConversations();
    } catch { /* silent */ }
  };

  const handleConversationClick = (convo) => {
    selectConversation(convo);
    if (onConversationSelect) onConversationSelect();
  };

  const isSearching = !!searchQuery.trim();

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h5 className="sidebar-title">Chats</h5>
        <button className="new-group-btn" onClick={() => setShowGroupModal(true)} title="New Group">
          <FaUsers size={16} />
        </button>
      </div>
      <StatusCarousel />
      <SearchBar value={searchQuery} onChange={setSearchQuery} />

      {isSearching ? (
        <div className="search-results-wrap">
          {searchLoading && (
            <div className="search-results">
              <div className="search-result-item" style={{ opacity: 0.5 }}>Searching...</div>
            </div>
          )}
          {!searchLoading && searchDone && searchResults.length === 0 && (
            <div className="search-no-results">
              <span>No users found for "{searchQuery}"</span>
            </div>
          )}
          {searchResults.length > 0 && (
            <UserSearchResults results={searchResults} onSelect={handleUserSelect} loading={searchLoading} />
          )}
        </div>
      ) : (
        <div className="conversation-list">
          {loadingConversations ? (
            <ConversationSkeleton />
          ) : conversations.length === 0 ? (
            <div className="sidebar-empty">
              <div style={{ fontSize: "2rem", marginBottom: 8 }}>💬</div>
              <div>No conversations yet</div>
              <div style={{ fontSize: "0.8rem", opacity: 0.5, marginTop: 4 }}>Search for users above to start chatting!</div>
            </div>
          ) : (
            conversations.map(convo => (
              <ConversationItem
                key={convo._id}
                conversation={convo}
                isActive={activeConversation?._id === convo._id}
                onClick={() => handleConversationClick(convo)}
              />
            ))
          )}
        </div>
      )}

      {showGroupModal && <CreateGroupModal onClose={() => setShowGroupModal(false)} />}
    </div>
  );
}
