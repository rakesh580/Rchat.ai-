import { useState, useRef } from "react";
import { FaTimes, FaImage, FaVideo } from "react-icons/fa";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../api";

const API_BASE = "http://localhost:8000/api/v1";

const BG_COLORS = [
  "#6C5CE7", "#0984E3", "#00B894", "#FDCB6E",
  "#E17055", "#D63031", "#2D3436", "#A29BFE",
];

export default function StatusCreator({ onClose, onDone }) {
  const { token } = useAuth();
  const [tab, setTab] = useState("text");
  const [text, setText] = useState("");
  const [bgColor, setBgColor] = useState(BG_COLORS[0]);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [caption, setCaption] = useState("");
  const [posting, setPosting] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef(null);

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setError("");
  };

  const handlePost = async () => {
    setError("");
    setPosting(true);

    try {
      const formData = new FormData();
      formData.append("type", tab);

      if (tab === "text") {
        if (!text.trim()) {
          setError("Please enter some text");
          setPosting(false);
          return;
        }
        formData.append("content", text.trim());
        formData.append("background_color", bgColor);
      } else {
        if (!file) {
          setError(`Please select ${tab === "image" ? "an image" : "a video"}`);
          setPosting(false);
          return;
        }
        formData.append("file", file);
        if (caption.trim()) {
          formData.append("caption", caption.trim());
        }
      }

      const res = await fetch(`${API_BASE}/status`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to post status");
      }

      onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="status-creator-overlay" onClick={onClose}>
      <div className="status-creator" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="status-creator-header">
          <button className="modal-close-btn" onClick={onClose}>
            <FaTimes size={20} />
          </button>
          <h5>Create Status</h5>
          <button
            className="status-post-btn"
            onClick={handlePost}
            disabled={posting}
          >
            {posting ? "Posting..." : "Post"}
          </button>
        </div>

        {/* Type tabs */}
        <div className="status-tabs">
          <button
            className={`status-tab ${tab === "text" ? "active" : ""}`}
            onClick={() => setTab("text")}
          >
            Text
          </button>
          <button
            className={`status-tab ${tab === "image" ? "active" : ""}`}
            onClick={() => setTab("image")}
          >
            <FaImage size={14} /> Image
          </button>
          <button
            className={`status-tab ${tab === "video" ? "active" : ""}`}
            onClick={() => setTab("video")}
          >
            <FaVideo size={14} /> Video
          </button>
        </div>

        {/* Content area */}
        <div className="status-creator-body">
          {tab === "text" && (
            <>
              <div
                className="status-text-preview"
                style={{ background: bgColor }}
              >
                <textarea
                  className="status-text-input"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Type your status..."
                  maxLength={500}
                />
              </div>
              <div className="status-bg-colors">
                {BG_COLORS.map((c) => (
                  <button
                    key={c}
                    className={`status-bg-swatch ${bgColor === c ? "active" : ""}`}
                    style={{ background: c }}
                    onClick={() => setBgColor(c)}
                  />
                ))}
              </div>
            </>
          )}

          {(tab === "image" || tab === "video") && (
            <>
              <div className="status-media-area">
                {preview ? (
                  tab === "image" ? (
                    <img src={preview} alt="preview" className="status-media-preview" />
                  ) : (
                    <video src={preview} className="status-media-preview" controls />
                  )
                ) : (
                  <div
                    className="status-media-placeholder"
                    onClick={() => fileRef.current?.click()}
                  >
                    {tab === "image" ? <FaImage size={40} /> : <FaVideo size={40} />}
                    <span>Click to select {tab}</span>
                  </div>
                )}
                <input
                  ref={fileRef}
                  type="file"
                  accept={tab === "image" ? "image/*" : "video/*"}
                  onChange={handleFileChange}
                  style={{ display: "none" }}
                />
                {preview && (
                  <button
                    className="status-change-file-btn"
                    onClick={() => fileRef.current?.click()}
                  >
                    Change {tab}
                  </button>
                )}
              </div>
              <input
                className="modal-input"
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                placeholder="Write a caption..."
                maxLength={200}
              />
            </>
          )}

          {error && <div className="modal-error">{error}</div>}
        </div>
      </div>
    </div>
  );
}
