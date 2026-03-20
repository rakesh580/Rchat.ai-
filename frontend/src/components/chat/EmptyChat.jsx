export default function EmptyChat() {
  return (
    <div className="empty-chat">
      <div className="empty-chat-illustration">
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
          <circle cx="40" cy="40" r="36" fill="var(--accent)" opacity="0.1" />
          <rect x="18" y="24" width="44" height="30" rx="8" fill="var(--accent)" opacity="0.3" />
          <rect x="18" y="24" width="44" height="30" rx="8" stroke="var(--accent)" strokeWidth="2" fill="none" />
          <circle cx="30" cy="39" r="3" fill="var(--accent)" />
          <circle cx="40" cy="39" r="3" fill="var(--accent)" />
          <circle cx="50" cy="39" r="3" fill="var(--accent)" />
          <polygon points="22,54 30,54 22,62" fill="var(--accent)" opacity="0.3" />
        </svg>
      </div>
      <h3 className="empty-chat-title">
        Rchat<span className="text-primary">.ai</span>
      </h3>
      <p className="empty-chat-subtitle">Select a conversation to start messaging</p>
      <p className="empty-chat-hint">or search for users in the sidebar to begin a new chat</p>
    </div>
  );
}
