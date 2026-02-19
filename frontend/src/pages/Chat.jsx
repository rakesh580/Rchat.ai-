import { useState } from "react";
import Sidebar from "../components/sidebar/Sidebar";
import ChatWindow from "../components/chat/ChatWindow";

export default function Chat() {
  const [showChat, setShowChat] = useState(false);

  return (
    <div className="chat-layout">
      <div className={`chat-sidebar ${showChat ? "hide-mobile" : ""}`}>
        <Sidebar onConversationSelect={() => setShowChat(true)} />
      </div>
      <div className={`chat-main ${!showChat ? "hide-mobile" : ""}`}>
        <ChatWindow onBack={() => setShowChat(false)} />
      </div>
    </div>
  );
}
