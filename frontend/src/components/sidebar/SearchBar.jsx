import { FaSearch, FaTimes } from "react-icons/fa";

export default function SearchBar({ value, onChange }) {
  return (
    <div className="search-bar">
      <FaSearch className="search-icon" />
      <input
        type="text"
        placeholder="Search people & chats..."
        value={value}
        onChange={e => onChange(e.target.value)}
        className="search-input"
        maxLength={100}
      />
      {value && (
        <button className="search-clear-btn" onClick={() => onChange("")} title="Clear search" aria-label="Clear search">
          <FaTimes size={12} />
        </button>
      )}
    </div>
  );
}
