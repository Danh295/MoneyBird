'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BrainCircuit, X, Sparkles, LayoutDashboard, History } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';
import { ActionPlanCard } from './ActionPlanCard';
import { useRouter } from 'next/navigation';
import { useFinancial } from '@/context/FinancialContext'; 
import { useChat } from '@/context/ChatContext'; 

// Types
type AgentLog = {
  id: string;
  agentName: string;
  status: string;
  thought: string;
  output?: string;
};

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  actionPlan?: any;
};

type ChatSession = {
  session_id: string;
  preview: string;
  last_message_at: string;
  created_at: string;
};

export default function ChatInterface() {
  const { addActionPlan } = useFinancial(); 
  const { messages, addMessage, setMessages, isThinking, setIsThinking } = useChat();
  const router = useRouter();
  const [sessionId, setSessionId] = useState(`session-${Date.now()}`);
  const [input, setInput] = useState('');
  const [showAgentPanel, setShowAgentPanel] = useState(false);
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentLogs]);

  // Fetch chat sessions when history panel is opened
  useEffect(() => {
    if (showHistoryPanel && chatSessions.length === 0) {
      fetchChatSessions();
    }
  }, [showHistoryPanel]);

  const fetchChatSessions = async () => {
    setIsLoadingSessions(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/sessions');
      const data = await res.json();
      setChatSessions(data.sessions || []);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const loadChatHistory = async (selectedSessionId: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/history/${selectedSessionId}`);
      const data = await res.json();
      
      if (data.history && data.history.length > 0) {
        setMessages(data.history);
        setSessionId(selectedSessionId);
        setShowHistoryPanel(false);
      }
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  };

  const startNewChat = () => {
    setMessages([
      { 
        id: '1', 
        role: 'assistant', 
        content: 'Hello. I am MindMoney. I am here to optimize your financial life. How can I help you today?' 
      }
    ]);
    setSessionId(`session-${Date.now()}`);
    setShowHistoryPanel(false);
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { id: Date.now().toString(), role: 'user' as const, content: input };
    addMessage(userMsg);
    setInput('');
    setIsThinking(true);
    setAgentLogs([]); 

    try {
      const res = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg.content,
          history: messages.map((m: Message) => ({ role: m.role, content: m.content })),
          session_id: sessionId
        })
      });

      const data = await res.json();

      if (data.agent_logs) {
        data.agent_logs.forEach((log: any, index: number) => {
          setTimeout(() => {
            setAgentLogs(prev => [...prev, {
              id: `log-${index}`,
              agentName: log.agent,
              status: log.status,
              thought: log.thought,
              output: log.output
            }]);
          }, index * 400);
        });
      }

      const delay = (data.agent_logs?.length || 0) * 400 + 500;
      
      setTimeout(() => {
        setIsThinking(false);
        
        if (data.action_plan && Object.keys(data.action_plan).length > 0) {
            addActionPlan(data.action_plan);
        }

        addMessage({
          id: Date.now().toString(),
          role: 'assistant',
          content: data.response,
          actionPlan: data.action_plan
        });
      }, delay);

    } catch (err) {
      console.error(err);
      setIsThinking(false);
      addMessage({
        id: Date.now().toString(),
        role: 'assistant',
        content: "⚠️ I'm having trouble reaching the brain. Ensure the backend is running on port 8000."
      });
    }
  };

  return (
    <div className="flex h-screen bg-[var(--background)] overflow-hidden relative">
      
      {/* MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full bg-white shadow-xl h-full relative">
        
        {/* Header */}
        {/* FIX 2: Removed 'pt-20' since the floating nav is gone */}
        <header className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-white z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowHistoryPanel(!showHistoryPanel)}
              className="p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--neutral)] transition-colors"
            >
              <History size={20} />
            </button>
            <div className="bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] p-2 rounded-lg shadow-md">
              <Sparkles className="text-white w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-[var(--text-primary)]">MindMoney Architect</h1>
              <p className="text-xs text-[var(--text-secondary)]">Orchestrated Financial Intelligence</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => router.push('/dashboard')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] text-white hover:shadow-md"
            >
              <LayoutDashboard size={16} />
              Dashboard
            </button>
            <button
              onClick={() => setShowAgentPanel(!showAgentPanel)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                showAgentPanel 
                  ? "bg-[var(--primary-dark)] text-white" 
                  : "bg-[var(--neutral)] text-[var(--text-primary)] hover:bg-[var(--neutral-dark)]"
              }`}
            >
              <BrainCircuit size={16} />
              {showAgentPanel ? "Hide Brain" : "View Brain"}
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8 bg-gradient-to-b from-[var(--background)] to-[var(--neutral)]">
          {messages.map((msg: Message) => (
            <div key={msg.id} className={clsx("flex gap-4 max-w-3xl mx-auto", msg.role === 'user' ? "flex-row-reverse" : "")}>
              
              <div className={clsx(
                "w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm",
                msg.role === 'assistant' ? "bg-white border border-[var(--border)]" : "bg-gradient-to-br from-[var(--primary)] to-[var(--accent)]"
              )}>
                {msg.role === 'assistant' ? <Bot size={20} className="text-[var(--primary)]" /> : <User size={20} className="text-white" />}
              </div>

              <div className="flex-1 space-y-4">
                <div className={clsx(
                  "p-6 rounded-2xl shadow-sm text-sm leading-relaxed prose prose-slate max-w-none",
                  msg.role === 'assistant' 
                    ? "bg-white border border-[var(--border)] text-[var(--text-primary)]" 
                    : "bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] text-white prose-invert"
                )}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>

                {msg.actionPlan && Object.keys(msg.actionPlan).length > 0 && (
                  <ActionPlanCard data={msg.actionPlan} />
                )}
              </div>
            </div>
          ))}
          
          {isThinking && (
             <div className="max-w-3xl mx-auto flex gap-4">
               <div className="w-10 h-10 rounded-full bg-white border border-[var(--border)] flex items-center justify-center animate-pulse">
                 <Bot size={20} className="text-[var(--primary)]"/>
               </div>
               <div className="text-[var(--text-secondary)] text-sm flex items-center gap-2">
                 <BrainCircuit size={14} className="animate-spin" />
                 Analyzing financial context...
               </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-6 bg-white border-t border-slate-100">
          <div className="max-w-3xl mx-auto relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="E.g., I want to pay off my $5k debt but also save for a trip to Japan..."
              className="w-full bg-[var(--neutral)] border border-[var(--border)] rounded-xl pl-6 pr-14 py-4 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20 focus:border-[var(--primary)] transition-all shadow-sm"
            />
            <button 
              onClick={handleSend}
              disabled={!input.trim() || isThinking}
              className="absolute right-3 top-3 bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] hover:shadow-md disabled:opacity-50 text-white p-2 rounded-lg transition-all"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* LEFT: CHAT HISTORY PANEL (Collapsible) */}
      <div className={clsx(
        "fixed inset-y-0 left-0 w-80 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out border-r border-slate-200 z-50",
        showHistoryPanel ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="p-4 border-b border-[var(--border)] bg-gradient-to-r from-[var(--neutral)] to-[var(--secondary-light)] flex justify-between items-center">
          <h3 className="text-[var(--text-primary)] font-semibold text-sm uppercase tracking-wider">
            Chat History
          </h3>
          <button onClick={() => setShowHistoryPanel(false)} className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
            <X size={16} />
          </button>
        </div>
        
        <div className="p-4 space-y-3 overflow-y-auto h-[calc(100vh-120px)]">
          {/* New Chat Button */}
          <button
            onClick={startNewChat}
            className="w-full bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] hover:shadow-md text-white rounded-lg p-3 text-sm font-medium transition-all flex items-center justify-center gap-2"
          >
            <Sparkles size={16} />
            Start New Chat
          </button>

          {/* Loading State */}
          {isLoadingSessions && (
            <div className="text-center text-slate-400 text-sm py-4">
              Loading sessions...
            </div>
          )}

          {/* Chat Sessions */}
          {!isLoadingSessions && chatSessions.length === 0 && (
            <div className="text-center text-slate-400 text-xs mt-10">
              No chat history yet.<br/>Start a conversation to see it here.
            </div>
          )}

          {chatSessions.map((session, index) => {
            const date = new Date(session.last_message_at);
            const isToday = date.toDateString() === new Date().toDateString();
            const isYesterday = date.toDateString() === new Date(Date.now() - 86400000).toDateString();
            
            let timeLabel = '';
            if (isToday) {
              timeLabel = 'Today';
            } else if (isYesterday) {
              timeLabel = 'Yesterday';
            } else {
              timeLabel = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }

            return (
              <div
                key={session.session_id}
                onClick={() => loadChatHistory(session.session_id)}
                className={clsx(
                  "bg-[var(--neutral)] rounded-lg p-3 border border-[var(--border)] hover:bg-[var(--neutral-dark)] cursor-pointer transition-colors",
                  session.session_id === sessionId && "bg-[var(--secondary-light)] border-[var(--primary)]"
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  {index === 0 && <div className="w-2 h-2 rounded-full bg-[var(--success)]" />}
                  <span className="font-semibold text-sm text-[var(--text-primary)]">{timeLabel}</span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] line-clamp-2">
                  {session.preview}
                </p>
                <span className="text-[10px] text-[var(--text-light)] mt-1 block">
                  {date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* RIGHT: AGENT NERVE CENTER (Collapsible) */}
      <div className={clsx(
        "fixed inset-y-0 right-0 w-80 bg-[var(--primary-dark)] shadow-2xl transform transition-transform duration-300 ease-in-out border-l border-[var(--primary)] z-50",
        showAgentPanel ? "translate-x-0" : "translate-x-full"
      )}>
        <div className="p-4 border-b border-[var(--primary)] bg-gradient-to-r from-[var(--primary-dark)] to-[var(--primary)] flex justify-between items-center">
          <h3 className="text-white font-mono text-xs font-bold uppercase tracking-wider">
            Orchestration Log
          </h3>
          <button onClick={() => setShowAgentPanel(false)} className="text-white/70 hover:text-white">
            <X size={16} />
          </button>
        </div>
        
        <div className="p-4 space-y-3 overflow-y-auto h-[calc(100vh-60px)]">
          {agentLogs.map((log, i) => (
            <div key={i} className="bg-white/10 rounded-lg p-3 border border-white/20 text-xs animate-in fade-in slide-in-from-right-8">
              <div className="flex items-center gap-2 mb-2">
                <span className={clsx("w-2 h-2 rounded-full", log.status === 'failed' ? "bg-[var(--danger)]" : "bg-[var(--success)]")} />
                <span className="font-bold text-white">{log.agentName}</span>
              </div>
              <p className="text-white/80 font-mono leading-relaxed opacity-80">
                {log.thought}
              </p>
              {log.output && (
                 <div className="mt-2 pt-2 border-t border-white/20 text-[10px] text-[var(--secondary-light)] font-mono truncate">
                   Output: {log.output}
                 </div>
              )}
            </div>
          ))}
          {agentLogs.length === 0 && (
            <div className="text-center text-white/50 mt-10 text-xs">
              Systems Idle.<br/>Waiting for user input.
            </div>
          )}
        </div>
      </div>

    </div>
  );
}