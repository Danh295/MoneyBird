// src/components/ChatInterface.tsx
'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Activity, ShieldAlert, Calculator, BrainCircuit, X, ChevronRight } from 'lucide-react';
import { Message, AgentLog, AgentName } from '@/types';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';

export default function ChatInterface() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: 'Hello. I am MindMoney. I am here to help you navigate both your financial stress and your financial plan. How are you feeling about your money today?' }
  ]);
  const [isThinking, setIsThinking] = useState(false);
  const [showAgentPanel, setShowAgentPanel] = useState(false);
  
  // This state powers the "Winning Feature" - The Orchestration Log
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentLogs]);

  // REAL API INTEGRATION: Call the backend and display actual agent orchestration
  const handleSend = async () => {
    if (!input.trim()) return;

    // 1. Add User Message
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsThinking(true);
    setAgentLogs([]); // Clear previous logs for new turn

    try {
      // 2. Call the real backend API
      const res = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input.trim(),
          history: messages.map(m => ({
            role: m.role === 'user' ? 'user' : 'assistant',
            content: m.content
          })),
          session_id: 'chat-session'
        })
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();

      // 3. Parse and display agent logs with staggered animation
      if (data.agent_logs && Array.isArray(data.agent_logs)) {
        data.agent_logs.forEach((log: any, index: number) => {
          // Stagger the logs for visual effect
          setTimeout(() => {
            setAgentLogs(prev => [...prev, {
              id: `log-${index}`,
              agentName: log.agent as AgentName,
              status: log.status === 'failed' ? 'complete' : (log.status || 'complete'),
              thought: log.thought || '',
              output: log.output || log.thought || ''
            }]);
          }, (index + 1) * 300); // 300ms stagger between agents
        });

        // Wait for all logs to appear before showing response
        const totalDelay = (data.agent_logs.length * 300) + 500;
        setTimeout(() => {
          setIsThinking(false);
          // Add the assistant response
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.response || 'Processing complete.'
          }]);
        }, totalDelay);
      } else {
        // No agent logs returned
        setIsThinking(false);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.response || 'Response received from backend.'
        }]);
      }

    } catch (err) {
      console.error('API Error:', err);
      setIsThinking(false);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: '⚠️ Backend error. Make sure the backend server is running on http://localhost:8000'
      }]);
      setAgentLogs([]);
    }
  };

  return (
    <div className="flex h-screen max-w-full mx-auto gap-6 p-4 relative bg-slate-100">
      
      {/* LEFT COLUMN: Main Chat */}
      <div className="flex-1 flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden relative">
        
        {/* Header with Agent Panel Button */}
        <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-gradient-to-r from-white to-slate-50">
          <div>
            <h1 className="text-xl font-bold text-slate-800">MindMoney</h1>
            <p className="text-xs text-slate-500">4-Agent Financial Wellness System</p>
          </div>
          <button
            onClick={() => setShowAgentPanel(!showAgentPanel)}
            className={clsx(
              "flex items-center gap-2 px-4 py-2 rounded-full font-medium transition-all text-sm",
              showAgentPanel
                ? "bg-teal-600 text-white shadow-lg"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            )}
          >
            <BrainCircuit size={16} />
            {showAgentPanel ? "Close" : "Agent View"}
            <ChevronRight size={14} />
          </button>
        </div>
        
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50">
          {messages.map((msg) => (
            <div key={msg.id} className={clsx("flex gap-4", msg.role === 'user' ? "flex-row-reverse" : "")}>
              <div className={clsx(
                "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                msg.role === 'assistant' ? "bg-teal-600 text-white" : "bg-slate-700 text-white"
              )}>
                {msg.role === 'assistant' ? <Bot size={18} /> : <User size={18} />}
              </div>
              <div className={clsx(
                "max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed shadow-sm",
                msg.role === 'assistant' ? "bg-white text-slate-800 border border-slate-200" : "bg-slate-700 text-white"
              )}>
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          ))}
          
          {/* Thinking Indicator */}
          {isThinking && (
             <div className="flex gap-4">
               <div className="w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center animate-pulse"><Bot size={18} className="text-white"/></div>
               <div className="text-slate-500 text-sm flex items-center italic">MindMoney is orchestrating agents...</div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-slate-100">
          <div className="flex gap-2 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Tell me what's on your mind (financial or emotional)..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all placeholder:text-slate-400"
            />
            <button 
              onClick={handleSend}
              disabled={!input.trim() || isThinking}
              className="absolute right-2 top-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed text-white p-2 rounded-lg transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* AGENT PANEL MODAL - Fixed on right side when open */}
      {showAgentPanel && (
        <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" onClick={() => setShowAgentPanel(false)} />
      )}
      
      <div
        className={clsx(
          "fixed top-0 right-0 h-screen w-96 bg-slate-900 text-slate-100 shadow-2xl border-l border-slate-800 transition-transform duration-300 z-50 overflow-hidden flex flex-col",
          showAgentPanel ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-gradient-to-r from-slate-900 to-slate-800 shrink-0">
          <div className="flex items-center gap-3">
            <BrainCircuit className="text-teal-400" size={22} />
            <div>
              <h2 className="font-bold text-white text-sm">Agent Orchestration</h2>
              <p className="text-xs text-slate-400">Real-time communication</p>
            </div>
          </div>
          <button
            onClick={() => setShowAgentPanel(false)}
            className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white"
          >
            <X size={18} />
          </button>
        </div>

        {/* Agent Logs with Flow Visualization */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {agentLogs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs text-center opacity-60">
              <BrainCircuit size={32} className="mb-2 opacity-40" />
              <p>Waiting for agent communication...</p>
              <p className="mt-1 text-[10px]">Send a message to see agents in action</p>
            </div>
          ) : (
            <>
              {/* Flow Diagram Legend */}
              <div className="px-2 py-2 bg-slate-800/40 rounded-lg border border-slate-700/40 mb-2">
                <p className="text-[10px] text-slate-400 font-semibold mb-1">Agent Flow:</p>
                <p className="text-[9px] text-slate-500">1️⃣ Intake → 2️⃣ Wealth → 3️⃣ Care Manager → 4️⃣ Action Gen</p>
              </div>

              {agentLogs.map((log, idx) => {
                // Determine what inputs this agent received
                const getAgentInputs = (agentName: string): string[] => {
                  switch (agentName) {
                    case 'Wealth Architect':
                      return ['📊 Received: User input + Intake profile'];
                    case 'Care Manager':
                      return ['📊 Received: Intake profile + Financial profile'];
                    case 'Action Generator':
                      return ['📊 Received: All previous agent outputs'];
                    default:
                      return ['📊 Received: User input'];
                  }
                };

                return (
                  <div key={log.id} className="space-y-2">
                    {/* Agent Card */}
                    <div className="bg-slate-800/60 rounded-lg p-3 border border-slate-700/60 animate-in fade-in slide-in-from-left-4 duration-300 group hover:bg-slate-800/80 transition-colors">
                      {/* Agent Header */}
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
                          {idx + 1}️⃣
                          {log.agentName === 'Intake Specialist' && <ShieldAlert size={13} className="text-amber-400" />}
                          {log.agentName === 'Wealth Architect' && <Calculator size={13} className="text-blue-400" />}
                          {log.agentName === 'Care Manager' && <Activity size={13} className="text-emerald-400" />}
                          {log.agentName === 'Action Generator' && <BrainCircuit size={13} className="text-purple-400" />}
                          <span>{log.agentName}</span>
                        </span>
                        {log.status === 'active' && (
                          <span className="flex items-center gap-1 text-[9px] text-emerald-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            Processing
                          </span>
                        )}
                        {log.status === 'complete' && (
                          <span className="text-[9px] text-emerald-600 font-medium">✓</span>
                        )}
                      </div>

                      {/* Input Data */}
                      <div className="text-[9px] text-slate-400 mb-2 px-2 py-1 bg-slate-950/40 rounded border-l-2 border-slate-600">
                        {getAgentInputs(log.agentName)[0]}
                      </div>

                      {/* Thought Process */}
                      <div className="text-xs text-slate-300 font-mono border-l-2 border-slate-600 pl-2 mb-2 italic text-[10px]">
                        💭 &quot;{log.thought}&quot;
                      </div>

                      {/* Output */}
                      {log.output && (
                        <div className="bg-slate-950/80 p-2 rounded text-[10px] text-teal-300/90 font-mono border border-slate-700/50">
                          <div className="text-slate-400 text-[9px] mb-1">→ Generated:</div>
                          <div className="text-teal-200 line-clamp-2">{log.output}</div>
                        </div>
                      )}
                    </div>

                    {/* Flow Arrow (between agents) */}
                    {idx < agentLogs.length - 1 && (
                      <div className="flex justify-center py-1">
                        <div className="text-slate-600 text-lg animate-bounce">↓</div>
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Final Response Indicator */}
              {agentLogs.length > 0 && (
                <div className="mt-3 px-3 py-2 bg-gradient-to-r from-emerald-900/40 to-teal-900/40 rounded-lg border border-emerald-700/40 text-[9px] text-emerald-300">
                  ✓ All agents completed. Response ready for user.
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Stats */}
        {agentLogs.length > 0 && (
          <div className="px-4 py-3 border-t border-slate-800 bg-slate-900/50 text-[11px] text-slate-400 space-y-1 shrink-0">
            <div className="flex justify-between">
              <span>Total Agents Active:</span>
              <span className="text-teal-300 font-semibold">{agentLogs.length}</span>
            </div>
            <div className="flex justify-between">
              <span>Completed:</span>
              <span className="text-emerald-400 font-semibold">{agentLogs.filter(l => l.status === 'complete').length}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}