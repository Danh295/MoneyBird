// src/components/ChatInterface.tsx
'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Activity, ShieldAlert, Calculator, BrainCircuit } from 'lucide-react';
import { Message, AgentLog } from '@/types';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';

export default function ChatInterface() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: 'Hello. I am MindMoney. I am here to help you navigate both your financial stress and your financial plan. How are you feeling about your money today?' }
  ]);
  const [isThinking, setIsThinking] = useState(false);
  
  // This state powers the "Winning Feature" - The Orchestration Log
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentLogs]);

  // HACKATHON DEMO: Simulates the orchestration delay so you can test the UI
  const handleSend = async () => {
    if (!input.trim()) return;

    // 1. Add User Message
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsThinking(true);
    setAgentLogs([]); // Clear previous logs for new turn

    // 2. Simulate Agent 1 (Intake) - The "Psychologist"
    setTimeout(() => {
      setAgentLogs(prev => [...prev, {
        id: 'log1', agentName: 'Intake Specialist', status: 'complete',
        thought: 'Analyzing sentiment. User seems anxious. Detected keyword: "Debt".',
        output: 'Anxiety Score: 8/10'
      }]);
    }, 800);

    // 3. Simulate Agent 2 (Wealth) - The "Calculater"
    setTimeout(() => {
      setAgentLogs(prev => [...prev, {
        id: 'log2', agentName: 'Wealth Architect', status: 'complete',
        thought: 'Scanning for entities. Found "$5000". Checking against debt-to-income ratio.',
        output: 'Strategy: Avalanche Method'
      }]);
    }, 1600);

    // 4. Simulate Agent 3 (Care Manager) - The "Synthesizer"
    setTimeout(() => {
      setAgentLogs(prev => [...prev, {
        id: 'log3', agentName: 'Care Manager', status: 'active',
        thought: 'Orchestration Logic: Anxiety is High (8/10). Suppressing complex math. Prioritizing validation.',
        output: 'Response generated.'
      }]);
    }, 2400);

    // 5. Final Output
    setTimeout(() => {
      setIsThinking(false);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: "I hear that this is weighing heavily on you right now. It makes sense that you're anxious.\n\nLet's pause the math for a second. We don't need to solve the whole $5,000 today. Can we just start by listing one small expense?"
      }]);
    }, 2800);
  };

  return (
    <div className="flex h-[calc(100vh-80px)] max-w-7xl mx-auto gap-6 p-4">
      
      {/* LEFT COLUMN: Main Chat */}
      <div className="flex-1 flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        
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

      {/* RIGHT COLUMN: The "Mind" (Orchestration Log) */}
      <div className="w-80 hidden lg:flex flex-col gap-4">
        <div className="bg-slate-900 text-slate-200 rounded-2xl p-4 h-full shadow-lg border border-slate-800 overflow-hidden flex flex-col">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-3">
            <BrainCircuit className="text-teal-400" size={20} />
            <h2 className="font-semibold text-sm tracking-wide text-teal-400 uppercase">Agent Orchestration</h2>
          </div>
          
          <div className="space-y-4 overflow-y-auto flex-1 pr-2">
            {agentLogs.length === 0 ? (
              <div className="text-slate-500 text-xs text-center mt-10 italic">
                Waiting for input...
                <br/>System ready.
              </div>
            ) : (
              agentLogs.map((log) => (
                <div key={log.id} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50 animate-in fade-in slide-in-from-left-4 duration-300">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-300 flex items-center gap-2">
                      {log.agentName === 'Intake Specialist' && <ShieldAlert size={14} className="text-amber-400"/>}
                      {log.agentName === 'Wealth Architect' && <Calculator size={14} className="text-blue-400"/>}
                      {log.agentName === 'Care Manager' && <Activity size={14} className="text-emerald-400"/>}
                      {log.agentName}
                    </span>
                    {log.status === 'active' && <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />}
                  </div>
                  <div className="text-xs text-slate-400 font-mono border-l-2 border-slate-600 pl-2 mb-2">
                    "{log.thought}"
                  </div>
                  {log.output && (
                    <div className="bg-slate-950/50 p-2 rounded text-[10px] text-teal-200/80 font-mono">
                      {`-> ${log.output}`}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

    </div>
  );
}