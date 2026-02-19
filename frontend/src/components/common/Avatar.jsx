const COLORS = [
  "#6C5CE7", "#A29BFE", "#0984E3", "#00B894",
  "#E17055", "#FDCB6E", "#D63031", "#00CEC9",
];

export default function Avatar({ name, isOnline, isBot, size = 42, avatarUrl }) {
  const letter = (name || "?")[0].toUpperCase();
  const colorIndex = name ? name.charCodeAt(0) % COLORS.length : 0;

  return (
    <div className="avatar-wrapper" style={{ width: size, height: size, minWidth: size }}>
      <div
        className="avatar-circle"
        style={{
          background: isBot
            ? "linear-gradient(135deg, #FDCB6E, #E17055)"
            : avatarUrl
              ? "transparent"
              : COLORS[colorIndex],
          width: size,
          height: size,
          fontSize: size * 0.4,
        }}
      >
        {avatarUrl ? (
          <img src={avatarUrl} alt={name} />
        ) : isBot ? (
          "AI"
        ) : (
          letter
        )}
      </div>
      {isOnline && <span className="avatar-online-dot" />}
    </div>
  );
}
