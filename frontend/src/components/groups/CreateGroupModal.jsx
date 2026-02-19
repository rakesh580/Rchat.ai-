import { useState, useEffect } from "react";
import { FaTimes, FaPlus } from "react-icons/fa";
import Avatar from "../common/Avatar";
import { useAuth } from "../../context/AuthContext";
import { useChat } from "../../context/ChatContext";
import { useSocket } from "../../context/SocketContext";
import { api } from "../../api";

export default function CreateGroupModal({ onClose }) {
  const { token } = useAuth();
  const { refreshConversations, selectConversation } = useChat();
  const { socket } = useSocket();
  const [groupName, setGroupName] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

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
        // Filter out already selected users
        const selectedIds = new Set(selectedUsers.map((u) => u._id));
        setSearchResults(results.filter((u) => !selectedIds.has(u._id)));
      } catch {
        setSearchResults([]);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, token, selectedUsers]);

  const addUser = (user) => {
    setSelectedUsers((prev) => [...prev, user]);
    setSearchQuery("");
    setSearchResults([]);
  };

  const removeUser = (userId) => {
    setSelectedUsers((prev) => prev.filter((u) => u._id !== userId));
  };

  const handleCreate = async () => {
    if (!groupName.trim() || selectedUsers.length === 0) return;
    setCreating(true);
    setError("");
    try {
      const convo = await api("/conversations", {
        method: "POST",
        body: {
          type: "group",
          participant_ids: selectedUsers.map((u) => u._id),
          group_name: groupName.trim(),
        },
        token,
      });
      // Notify connected members via socket
      if (socket) {
        socket.emit("group_created", { conversation_id: convo._id });
      }
      // Refresh and select the new conversation
      const convos = await api("/conversations", { token });
      const resolved = convos.find((c) => c._id === convo._id);
      if (resolved) selectConversation(resolved);
      await refreshConversations();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h5>Create Group</h5>
          <button className="modal-close-btn" onClick={onClose}>
            <FaTimes size={18} />
          </button>
        </div>

        <div className="modal-body">
          <input
            type="text"
            className="modal-input"
            placeholder="Group name"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
          />

          {selectedUsers.length > 0 && (
            <div className="selected-users">
              {selectedUsers.map((u) => (
                <span key={u._id} className="selected-chip">
                  {u.display_name || u.username}
                  <button onClick={() => removeUser(u._id)}>
                    <FaTimes size={10} />
                  </button>
                </span>
              ))}
            </div>
          )}

          <input
            type="text"
            className="modal-input"
            placeholder="Search users to add..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          {searchResults.length > 0 && (
            <div className="modal-search-results">
              {searchResults.map((user) => (
                <div
                  key={user._id}
                  className="modal-search-item"
                  onClick={() => addUser(user)}
                >
                  <Avatar
                    name={user.display_name || user.username}
                    isBot={user.is_bot}
                    size={32}
                  />
                  <span>{user.display_name || user.username}</span>
                  <FaPlus size={12} className="add-icon" />
                </div>
              ))}
            </div>
          )}

          {error && <div className="modal-error">{error}</div>}
        </div>

        <div className="modal-footer">
          <button className="modal-cancel-btn" onClick={onClose}>
            Cancel
          </button>
          <button
            className="modal-create-btn"
            onClick={handleCreate}
            disabled={!groupName.trim() || selectedUsers.length === 0 || creating}
          >
            {creating ? "Creating..." : "Create Group"}
          </button>
        </div>
      </div>
    </div>
  );
}
