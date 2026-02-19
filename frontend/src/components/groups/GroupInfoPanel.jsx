import { useState, useEffect } from "react";
import { FaTimes, FaPlus, FaSignOutAlt, FaUserMinus } from "react-icons/fa";
import Avatar from "../common/Avatar";
import { useAuth } from "../../context/AuthContext";
import { useChat } from "../../context/ChatContext";
import { useSocket } from "../../context/SocketContext";
import { api } from "../../api";

export default function GroupInfoPanel({ onClose }) {
  const { token, user } = useAuth();
  const { activeConversation, refreshConversations, selectConversation } = useChat();
  const { onlineUsers } = useSocket();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [showAddMember, setShowAddMember] = useState(false);

  if (!activeConversation || activeConversation.type !== "group") return null;

  const isAdmin = activeConversation.admins?.includes(user?._id);
  const participants = activeConversation.participants || [];

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const results = await api(
          `/users/search?q=${encodeURIComponent(searchQuery)}`,
          { token }
        );
        const memberIds = new Set(participants.map((p) => p._id));
        setSearchResults(results.filter((u) => !memberIds.has(u._id)));
      } catch {
        setSearchResults([]);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, token]);

  const handleAddMember = async (userId) => {
    try {
      const updated = await api(
        `/conversations/${activeConversation._id}/members`,
        { method: "POST", body: { user_id: userId }, token }
      );
      selectConversation(updated);
      await refreshConversations();
      setSearchQuery("");
      setSearchResults([]);
    } catch (err) {
      /* failed silently */
    }
  };

  const handleRemoveMember = async (memberId) => {
    try {
      const updated = await api(
        `/conversations/${activeConversation._id}/members/${memberId}`,
        { method: "DELETE", token }
      );
      selectConversation(updated);
      await refreshConversations();
    } catch (err) {
      /* failed silently */
    }
  };

  const handleLeaveGroup = async () => {
    try {
      await api(
        `/conversations/${activeConversation._id}/members/${user._id}`,
        { method: "DELETE", token }
      );
      selectConversation(null);
      await refreshConversations();
      onClose();
    } catch (err) {
      /* failed silently */
    }
  };

  return (
    <div className="group-info-panel">
      <div className="group-info-header">
        <h5>Group Info</h5>
        <button className="modal-close-btn" onClick={onClose}>
          <FaTimes size={18} />
        </button>
      </div>

      <div className="group-info-name">
        <Avatar
          name={activeConversation.group_name}
          size={64}
        />
        <h4>{activeConversation.group_name}</h4>
        <span className="group-member-count">
          {participants.length} members
        </span>
      </div>

      <div className="group-members-section">
        <div className="group-members-header">
          <span>Members</span>
          {isAdmin && (
            <button
              className="group-add-btn"
              onClick={() => setShowAddMember(!showAddMember)}
            >
              <FaPlus size={12} /> Add
            </button>
          )}
        </div>

        {showAddMember && (
          <div className="group-add-member">
            <input
              type="text"
              className="modal-input"
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchResults.map((u) => (
              <div
                key={u._id}
                className="modal-search-item"
                onClick={() => handleAddMember(u._id)}
              >
                <Avatar name={u.display_name || u.username} size={32} />
                <span>{u.display_name || u.username}</span>
                <FaPlus size={12} className="add-icon" />
              </div>
            ))}
          </div>
        )}

        <div className="group-member-list">
          {participants.map((p) => (
            <div key={p._id} className="group-member-item">
              <Avatar
                name={p.display_name || p.username}
                isOnline={p.is_bot || onlineUsers.has(p._id)}
                isBot={p.is_bot}
                size={40}
              />
              <div className="group-member-info">
                <span className="group-member-name">
                  {p.display_name || p.username}
                  {p._id === user?._id && " (You)"}
                </span>
                {activeConversation.admins?.includes(p._id) && (
                  <span className="group-admin-badge">Admin</span>
                )}
              </div>
              {isAdmin && p._id !== user?._id && !p.is_bot && (
                <button
                  className="group-remove-btn"
                  onClick={() => handleRemoveMember(p._id)}
                >
                  <FaUserMinus size={14} />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <button className="group-leave-btn" onClick={handleLeaveGroup}>
        <FaSignOutAlt size={14} /> Leave Group
      </button>
    </div>
  );
}
