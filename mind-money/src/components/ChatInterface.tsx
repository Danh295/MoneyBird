'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BrainCircuit, X, Sparkles, LayoutDashboard, Menu } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';
import { ActionPlanCard } from './ActionPlanCard';
import { useFinancial } from '@/context/FinancialContext'; // Import context
import { useRouter } from 'next/navigation';

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

export default function ChatInterface() {
  const { addActionPlan } = useFinancial(); // Connection to the Dashboard
  const router = useRouter();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { 
      id: '1', 
      role: 'assistant', 
      content: 'Hello. I am MindMoney. I am here to optimize your financial life. How can I help you today?' 
    }
  ]);
  const [isThinking, setIsThinking] = useState(false);
  const [showAgentPanel, setShowAgentPanel] = useState(false);
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentLogs]);

  const handleSend = async () => {
    if (!input.trim()) return;

    // 1. Add User Message
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsThinking(true);
    setAgentLogs([]); 

    try {
      // 2. Call the API
      const res = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input.trim(),
          history: messages.map(m => ({ role: m.role, content: m.content })),
          session_id: 'chat-session'
        })
      });

      const data = await res.json();

      // 3. Agent Log Animation
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

      // 4. Final Response + Context Update
      const delay = (data.agent_logs?.length || 0) * 400 + 500;
      
      setTimeout(() => {
        setIsThinking(false);
        
        // CRITICAL: Save to Global Context (The Dashboard)
        if (data.action_plan && Object.keys(data.action_plan).length > 0) {
            addActionPlan(data.action_plan);
        }

        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.response,
          actionPlan: data.action_plan
        }]);
      }, delay);

    } catch (err) {
      console.error(err);
      setIsThinking(false);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: "I'm having trouble connecting to the financial brain. Please check the backend connection."
      }]);
    }
  };

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden relative">
      
      {/* MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full bg-white shadow-xl h-full relative">
        
        {/* Header */}
        <header className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-white z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowHistoryPanel(!showHistoryPanel)}
              className="p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
            >
              <Menu size={20} />
            </button>
            <div className="bg-indigo-600 p-2 rounded-lg">
              <Sparkles className="text-white w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-slate-800">MindMoney Architect</h1>
              <p className="text-xs text-slate-500">Orchestrated Financial Intelligence</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => router.push('/dashboard')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-emerald-600 text-white hover:bg-emerald-700"
            >
              <LayoutDashboard size={16} />
              Dashboard
            </button>
            <button
              onClick={() => setShowAgentPanel(!showAgentPanel)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                showAgentPanel 
                  ? "bg-slate-900 text-white" 
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              <BrainCircuit size={16} />
              {showAgentPanel ? "Hide Brain" : "View Brain"}
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8 bg-slate-50/50">
          {messages.map((msg) => (
            <div key={msg.id} className={clsx("flex gap-4 max-w-3xl mx-auto", msg.role === 'user' ? "flex-row-reverse" : "")}>
              
              {/* Avatar */}
              <div className={clsx(
                "w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm",
                msg.role === 'assistant' ? "bg-white border border-indigo-100" : "bg-indigo-600"
              )}>
                {msg.role === 'assistant' ? <Bot size={20} className="text-indigo-600" /> : <User size={20} className="text-white" />}
              </div>

              <div className="flex-1 space-y-4">
                {/* Message Bubble */}
                <div className={clsx(
                  "p-6 rounded-2xl shadow-sm text-sm leading-relaxed prose prose-slate max-w-none",
                  msg.role === 'assistant' 
                    ? "bg-white border border-slate-200 text-slate-700" 
                    : "bg-indigo-600 text-white prose-invert"
                )}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>

                {/* DYNAMIC ACTION PLAN WIDGET */}
                {msg.actionPlan && Object.keys(msg.actionPlan).length > 0 && (
                  <ActionPlanCard data={msg.actionPlan} />
                )}
              </div>
            </div>
          ))}
          
          {isThinking && (
             <div className="max-w-3xl mx-auto flex gap-4">
               <div className="w-10 h-10 rounded-full bg-white border border-indigo-100 flex items-center justify-center animate-pulse">
                 <Bot size={20} className="text-indigo-400"/>
               </div>
               <div className="text-slate-400 text-sm flex items-center gap-2">
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
              className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-6 pr-14 py-4 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm"
            />
            <button 
              onClick={handleSend}
              disabled={!input.trim() || isThinking}
              className="absolute right-3 top-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white p-2 rounded-lg transition-colors"
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
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
          <h3 className="text-slate-800 font-semibold text-sm uppercase tracking-wider">
            Chat History
          </h3>
          <button onClick={() => setShowHistoryPanel(false)} className="text-slate-500 hover:text-slate-800">
            <X size={16} />
          </button>
        </div>
        
        <div className="p-4 space-y-3 overflow-y-auto h-[calc(100vh-60px)]">
          {/* Hardcoded chat sessions for now - TODO: Make dynamic */}
          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 hover:bg-slate-100 cursor-pointer transition-colors">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="font-semibold text-sm text-slate-800">Today</span>
            </div>
            <p className="text-xs text-slate-600 line-clamp-2">
              Debt payoff strategy with travel savings
            </p>
            <span className="text-[10px] text-slate-400 mt-1 block">2 hours ago</span>
          </div>

          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 hover:bg-slate-100 cursor-pointer transition-colors">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-sm text-slate-800">Yesterday</span>
            </div>
            <p className="text-xs text-slate-600 line-clamp-2">
              Investment portfolio rebalancing advice
            </p>
            <span className="text-[10px] text-slate-400 mt-1 block">Jan 16, 2026</span>
          </div>

          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 hover:bg-slate-100 cursor-pointer transition-colors">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-sm text-slate-800">Last Week</span>
            </div>
            <p className="text-xs text-slate-600 line-clamp-2">
              Emergency fund setup and budgeting
            </p>
            <span className="text-[10px] text-slate-400 mt-1 block">Jan 10, 2026</span>
          </div>

          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 hover:bg-slate-100 cursor-pointer transition-colors">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-sm text-slate-800">Jan 5, 2026</span>
            </div>
            <p className="text-xs text-slate-600 line-clamp-2">
              Tax optimization strategies for 2026
            </p>
            <span className="text-[10px] text-slate-400 mt-1 block">12 days ago</span>
          </div>

          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 hover:bg-slate-100 cursor-pointer transition-colors">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-sm text-slate-800">Dec 2025</span>
            </div>
            <p className="text-xs text-slate-600 line-clamp-2">
              Retirement planning and 401k review
            </p>
            <span className="text-[10px] text-slate-400 mt-1 block">3 weeks ago</span>
          </div>
        </div>
      </div>

      {/* RIGHT: AGENT NERVE CENTER (Collapsible) */}
      <div className={clsx(
        "fixed inset-y-0 right-0 w-80 bg-slate-900 shadow-2xl transform transition-transform duration-300 ease-in-out border-l border-slate-800 z-50",
        showAgentPanel ? "translate-x-0" : "translate-x-full"
      )}>
        <div className="p-4 border-b border-slate-800 bg-slate-950 flex justify-between items-center">
          <h3 className="text-indigo-400 font-mono text-xs font-bold uppercase tracking-wider">
            Orchestration Log
          </h3>
          <button onClick={() => setShowAgentPanel(false)} className="text-slate-500 hover:text-white">
            <X size={16} />
          </button>
        </div>
        
        <div className="p-4 space-y-3 overflow-y-auto h-[calc(100vh-60px)]">
          {agentLogs.map((log, i) => (
            <div key={i} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50 text-xs animate-in fade-in slide-in-from-right-8">
              <div className="flex items-center gap-2 mb-2">
                <span className={clsx("w-2 h-2 rounded-full", log.status === 'failed' ? "bg-red-500" : "bg-emerald-400")} />
                <span className="font-bold text-slate-200">{log.agentName}</span>
              </div>
              <p className="text-slate-400 font-mono leading-relaxed opacity-80">
                {log.thought}
              </p>
              {log.output && (
                 <div className="mt-2 pt-2 border-t border-slate-700/50 text-[10px] text-indigo-300 font-mono truncate">
                   Output: {log.output}
                 </div>
              )}
            </div>
          ))}
          {agentLogs.length === 0 && (
            <div className="text-center text-slate-600 mt-10 text-xs">
              Systems Idle.<br/>Waiting for user input.
            </div>
          )}
        </div>
      </div>

    </div>
  );
}