import { useState } from "react";
import ChatHeader from "./ChatHeader";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import EmptyChat from "./EmptyChat";
import GroupInfoPanel from "../groups/GroupInfoPanel";
import { useChat } from "../../context/ChatContext";

export default function ChatWindow({ onBack }) {
  const { activeConversation } = useChat();
  const [showGroupInfo, setShowGroupInfo] = useState(false);

  if (!activeConversation) return <EmptyChat />;

  return (
    <div className="chat-window-wrapper">
      <div className="chat-window">
        <ChatHeader
          onBack={onBack}
          onGroupInfoToggle={() => setShowGroupInfo(!showGroupInfo)}
        />
        <MessageList />
        <MessageInput />
      </div>
      {showGroupInfo && activeConversation.type === "group" && (
        <GroupInfoPanel onClose={() => setShowGroupInfo(false)} />
      )}
    </div>
  );
}
