import { useState, useEffect } from "react";
import { FaPlus } from "react-icons/fa";
import { useAuth } from "../../context/AuthContext";
import { api, API_HOST } from "../../api";
import StatusCreator from "./StatusCreator";
import StatusViewer from "./StatusViewer";

export default function StatusCarousel() {
  const { user, token } = useAuth();
  const [myStatuses, setMyStatuses] = useState([]);
  const [feed, setFeed] = useState([]);
  const [showCreator, setShowCreator] = useState(false);
  const [viewingUser, setViewingUser] = useState(null); // { user info + statuses }
  const [viewingIndex, setViewingIndex] = useState(0); // index in feed array

  const fetchStatuses = async () => {
    if (!token) return;
    try {
      const [mine, feedData] = await Promise.all([
        api("/status/me", { token }),
        api("/status/feed", { token }),
      ]);
      setMyStatuses(mine);
      setFeed(feedData);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    fetchStatuses();
    const interval = setInterval(fetchStatuses, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, [token]);

  const handleMyClick = () => {
    if (myStatuses.length > 0) {
      // View own statuses
      setViewingUser({
        user_id: user._id,
        username: user.username,
        display_name: user.display_name || user.username,
        avatar_url: user.avatar_url || "",
        statuses: myStatuses,
        has_unseen: false,
      });
      setViewingIndex(-1); // -1 = viewing own
    } else {
      setShowCreator(true);
    }
  };

  const handleFeedClick = (userGroup, idx) => {
    setViewingUser(userGroup);
    setViewingIndex(idx);
  };

  const handleViewerClose = () => {
    setViewingUser(null);
    fetchStatuses(); // refresh after viewing (marks as seen)
  };

  const handleViewerNext = () => {
    // Move to next user's statuses
    if (viewingIndex >= 0 && viewingIndex < feed.length - 1) {
      const nextIdx = viewingIndex + 1;
      setViewingUser(feed[nextIdx]);
      setViewingIndex(nextIdx);
    } else {
      setViewingUser(null);
      fetchStatuses();
    }
  };

  const handleCreatorDone = () => {
    setShowCreator(false);
    fetchStatuses();
  };

  const myInitials = (user?.display_name || user?.username || "?")[0].toUpperCase();
  const myAvatar = user?.avatar_url ? `${API_HOST}${user.avatar_url}` : null;

  return (
    <>
      <div className="status-carousel">
        {/* My status slot */}
        <div className="status-slot" onClick={handleMyClick}>
          <div className={`status-avatar-ring ${myStatuses.length > 0 ? "has-status" : "no-status"}`}>
            <div className="status-avatar">
              {myAvatar ? (
                <img src={myAvatar} alt="You" />
              ) : (
                <span>{myInitials}</span>
              )}
            </div>
            {myStatuses.length === 0 && (
              <div className="status-add-icon">
                <FaPlus size={10} />
              </div>
            )}
          </div>
          <span className="status-slot-name">You</span>
        </div>

        {/* Contacts' statuses */}
        {feed.map((userGroup, idx) => {
          const avatar = userGroup.avatar_url
            ? `${API_HOST}${userGroup.avatar_url}`
            : null;
          const initials = (userGroup.display_name || userGroup.username || "?")[0].toUpperCase();
          const name = userGroup.display_name || userGroup.username;
          const shortName = name.length > 7 ? name.slice(0, 7) : name;

          return (
            <div
              key={userGroup.user_id}
              className="status-slot"
              onClick={() => handleFeedClick(userGroup, idx)}
            >
              <div className={`status-avatar-ring ${userGroup.has_unseen ? "unseen" : "seen"}`}>
                <div className="status-avatar">
                  {avatar ? (
                    <img src={avatar} alt={name} />
                  ) : (
                    <span>{initials}</span>
                  )}
                </div>
              </div>
              <span className="status-slot-name">{shortName}</span>
            </div>
          );
        })}
      </div>

      {showCreator && (
        <StatusCreator onClose={() => setShowCreator(false)} onDone={handleCreatorDone} />
      )}

      {viewingUser && (
        <StatusViewer
          userGroup={viewingUser}
          onClose={handleViewerClose}
          onNextUser={handleViewerNext}
        />
      )}
    </>
  );
}
