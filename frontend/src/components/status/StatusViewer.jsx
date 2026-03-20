import { useState, useEffect, useRef, useCallback } from "react";
import { FaTimes } from "react-icons/fa";
import { useAuth } from "../../context/AuthContext";
import { api, API_HOST } from "../../api";
const STATUS_DURATION = 5000; // 5 seconds per status

export default function StatusViewer({ userGroup, onClose, onNextUser }) {
  const { token, user } = useAuth();
  const [currentIdx, setCurrentIdx] = useState(0);
  const [progress, setProgress] = useState(0);
  const [paused, setPaused] = useState(false);
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);
  const elapsedRef = useRef(0);

  const statuses = userGroup.statuses || [];
  const current = statuses[currentIdx];

  const markViewed = useCallback(async (statusId) => {
    if (!token) return;
    try {
      await api(`/status/${statusId}/view`, { method: "POST", token });
    } catch { /* ignore */ }
  }, [token]);

  const goNext = useCallback(() => {
    if (currentIdx < statuses.length - 1) {
      setCurrentIdx((i) => i + 1);
      setProgress(0);
      elapsedRef.current = 0;
    } else {
      onNextUser();
    }
  }, [currentIdx, statuses.length, onNextUser]);

  const goPrev = useCallback(() => {
    if (currentIdx > 0) {
      setCurrentIdx((i) => i - 1);
      setProgress(0);
      elapsedRef.current = 0;
    }
  }, [currentIdx]);

  // Auto-advance timer
  useEffect(() => {
    if (paused || !current) return;

    startTimeRef.current = Date.now();

    const animate = () => {
      const elapsed = elapsedRef.current + (Date.now() - startTimeRef.current);
      const pct = Math.min((elapsed / STATUS_DURATION) * 100, 100);
      setProgress(pct);

      if (pct >= 100) {
        goNext();
        return;
      }
      timerRef.current = requestAnimationFrame(animate);
    };

    timerRef.current = requestAnimationFrame(animate);

    return () => {
      if (timerRef.current) cancelAnimationFrame(timerRef.current);
      elapsedRef.current += Date.now() - startTimeRef.current;
    };
  }, [currentIdx, paused, current, goNext]);

  // Mark as viewed when viewing a status
  useEffect(() => {
    if (current && user) {
      markViewed(current._id);
    }
  }, [current, user, markViewed]);

  // Reset on new user
  useEffect(() => {
    setCurrentIdx(0);
    setProgress(0);
    elapsedRef.current = 0;
  }, [userGroup.user_id]);

  const handleTap = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    if (x < rect.width / 2) {
      goPrev();
    } else {
      goNext();
    }
  };

  const handlePauseStart = () => {
    setPaused(true);
    if (timerRef.current) cancelAnimationFrame(timerRef.current);
    elapsedRef.current += Date.now() - startTimeRef.current;
  };

  const handlePauseEnd = () => {
    setPaused(false);
  };

  if (!current) return null;

  const avatarSrc = userGroup.avatar_url
    ? `${API_HOST}${userGroup.avatar_url}`
    : null;
  const initials = (userGroup.display_name || userGroup.username || "?")[0].toUpperCase();

  const timeAgo = getTimeAgo(current.created_at);

  return (
    <div className="status-viewer-overlay">
      {/* Progress bars */}
      <div className="status-progress-bars">
        {statuses.map((_, idx) => (
          <div key={idx} className="status-progress-track">
            <div
              className="status-progress-fill"
              style={{
                width:
                  idx < currentIdx
                    ? "100%"
                    : idx === currentIdx
                      ? `${progress}%`
                      : "0%",
              }}
            />
          </div>
        ))}
      </div>

      {/* Header */}
      <div className="status-viewer-header">
        <div className="status-viewer-user">
          <div className="status-viewer-avatar">
            {avatarSrc ? (
              <img src={avatarSrc} alt="" />
            ) : (
              <span>{initials}</span>
            )}
          </div>
          <div>
            <div className="status-viewer-name">
              {userGroup.display_name || userGroup.username}
            </div>
            <div className="status-viewer-time">{timeAgo}</div>
          </div>
        </div>
        <button className="status-viewer-close" onClick={onClose}>
          <FaTimes size={22} />
        </button>
      </div>

      {/* Content */}
      <div
        className="status-viewer-content"
        onClick={handleTap}
        onMouseDown={handlePauseStart}
        onMouseUp={handlePauseEnd}
        onMouseLeave={handlePauseEnd}
        onTouchStart={handlePauseStart}
        onTouchEnd={handlePauseEnd}
      >
        {current.type === "text" && (
          <div
            className="status-viewer-text"
            style={{ background: current.background_color || "#6C5CE7" }}
          >
            <p>{current.content}</p>
          </div>
        )}

        {current.type === "image" && (
          <div className="status-viewer-media">
            <img src={`${API_HOST}${current.media_url}`} alt="status" />
            {current.caption && (
              <div className="status-viewer-caption">{current.caption}</div>
            )}
          </div>
        )}

        {current.type === "video" && (
          <div className="status-viewer-media">
            <video
              src={`${API_HOST}${current.media_url}`}
              autoPlay
              muted
              playsInline
            />
            {current.caption && (
              <div className="status-viewer-caption">{current.caption}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function getTimeAgo(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);

  if (diff < 60) return "Just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return "1d ago";
}
