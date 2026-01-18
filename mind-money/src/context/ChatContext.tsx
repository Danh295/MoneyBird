'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

// Define Types
export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  actionPlan?: any;
};

type AgentLog = {
  id: string;
  agentName: string;
  status: string;
  thought: string;
  output?: string;
};

type ChatContextType = {
  messages: Message[];
  addMessage: (msg: Message) => void;
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  agentLogs: AgentLog[];
  setAgentLogs: React.Dispatch<React.SetStateAction<AgentLog[]>>;
  isThinking: boolean;
  setIsThinking: React.Dispatch<React.SetStateAction<boolean>>;
  sessionId: string;
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  // Generate a consistent Session ID (or grab from URL/Auth)
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('mindmoney_session_id') || `sess-${Math.random().toString(36).substr(2, 9)}`;
    }
    return 'demo-session';
  });

  const [messages, setMessages] = useState<Message[]>([]);
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);
  const [isThinking, setIsThinking] = useState(false);

  // --- 1. LOAD HISTORY ON MOUNT ---
  useEffect(() => {
    if (typeof window !== 'undefined') {
        localStorage.setItem('mindmoney_session_id', sessionId);
    }

    const fetchHistory = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/history/${sessionId}`);
        const data = await res.json();
        
        if (data.history && data.history.length > 0) {
          setMessages(data.history);
        } else {
           // Default Welcome Message
           setMessages([{ 
             id: 'welcome', 
             role: 'assistant', 
             content: 'Hello. I am MindMoney. I am here to optimize your financial life. How can I help you today?' 
           }]);
        }
      } catch (err) {
        console.error("Failed to load history:", err);
      }
    };

    fetchHistory();
  }, [sessionId]);

  const addMessage = (msg: Message) => {
    setMessages(prev => [...prev, msg]);
  };

  return (
    <ChatContext.Provider value={{ 
      messages, 
      addMessage, 
      setMessages, 
      agentLogs, 
      setAgentLogs,
      isThinking, 
      setIsThinking,
      sessionId 
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within a ChatProvider');
  return context;
};