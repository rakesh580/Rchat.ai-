import Avatar from "../common/Avatar";

export default function UserSearchResults({ results, onSelect, loading }) {
  if (loading)
    return (
      <div className="search-results">
        <div className="search-result-item">Searching...</div>
      </div>
    );

  if (results.length === 0) return null;

  return (
    <div className="search-results">
      {results.map((user) => (
        <div
          key={user._id}
          className="search-result-item"
          onClick={() => onSelect(user)}
        >
          <Avatar
            name={user.display_name || user.username}
            isBot={user.is_bot}
            size={36}
          />
          <div className="search-result-info">
            <span className="search-result-name">
              {user.display_name || user.username}
            </span>
            <span className="search-result-username">@{user.username}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
