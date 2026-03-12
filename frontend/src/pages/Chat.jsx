import { useState } from "react";
import Sidebar from "../components/sidebar/Sidebar";
import ChatWindow from "../components/chat/ChatWindow";
import AutopilotBriefing from "../components/AutopilotBriefing";
import { useChat } from "../context/ChatContext";

export default function Chat() {
  const [showChat, setShowChat] = useState(false);
  const { showBriefing, setShowBriefing } = useChat();

  return (
    <div className="chat-layout">
      <div className={`chat-sidebar ${showChat ? "hide-mobile" : ""}`}>
        <Sidebar onConversationSelect={() => setShowChat(true)} />
      </div>
      <div className={`chat-main ${!showChat ? "hide-mobile" : ""}`}>
        <ChatWindow onBack={() => setShowChat(false)} />
      </div>
      {showBriefing && <AutopilotBriefing onClose={() => setShowBriefing(false)} />}
    </div>
  );
}
