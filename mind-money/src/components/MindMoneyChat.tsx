"use client";
import { useState, useRef, useEffect } from "react";
import { Send, Terminal, User, Bot, Loader2, ChevronDown, ChevronUp } from "lucide-react";

// Types for our chat
type Log = { agent: string; thought: string };
type Message = { role: "user" | "ai"; text: string; logs?: Log[] };

export default function MindMoneyChat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [isDevMode, setIsDevMode] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg: Message = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setInput("");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg.text,
          history: [],
          session_id: "modern-ui-test",
        }),
      });

      const data = await res.json();
      
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: data.response, logs: data.agent_logs }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "⚠️ System unreachable. Is the backend running?" }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-140px)] gap-6 font-sans">
      
      {/* LEFT: MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden relative">
        
        {/* Chat Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-white/80 backdrop-blur-md sticky top-0 z-10">
          <div>
            <h2 className="font-bold text-slate-800">Financial Assistant</h2>
            <p className="text-xs text-slate-400">Powered by Multi-Agent Orchestration</p>
          </div>
          <button
            onClick={() => setIsDevMode(!isDevMode)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
              isDevMode 
                ? "bg-indigo-100 text-indigo-700 ring-2 ring-indigo-500 ring-offset-1" 
                : "bg-slate-100 text-slate-500 hover:bg-slate-200"
            }`}
          >
            <Terminal size={14} />
            {isDevMode ? "Dev Mode: ON" : "Dev Mode: OFF"}
          </button>
        </div>

        {/* Messages List */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-60">
              <Bot size={48} className="mb-4 text-indigo-200" />
              <p>Type a message to start the session...</p>
            </div>
          )}
          
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                msg.role === "user" ? "bg-indigo-600 text-white" : "bg-emerald-500 text-white"
              }`}>
                {msg.role === "user" ? <User size={16} /> : <Bot size={16} />}
              </div>

              {/* Bubble */}
              <div className={`max-w-[80%] space-y-2`}>
                <div className={`p-4 rounded-2xl shadow-sm text-sm leading-relaxed ${
                  msg.role === "user" 
                    ? "bg-indigo-600 text-white rounded-tr-none" 
                    : "bg-white text-slate-700 border border-slate-100 rounded-tl-none"
                }`}>
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                </div>

                {/* Agent Logs (Only visible in Dev Mode) */}
                {isDevMode && msg.logs && (
                  <div className="bg-slate-900 rounded-lg p-3 text-xs font-mono text-green-400 border border-slate-800 shadow-inner animate-in fade-in slide-in-from-top-2">
                    <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-800 text-slate-500">
                      <Terminal size={12} />
                      <span>Agent Execution Trace</span>
                    </div>
                    {msg.logs.map((log, j) => (
                      <div key={j} className="mb-1.5 last:mb-0">
                        <span className="text-yellow-500 font-bold">[{log.agent}]</span>
                        <span className="text-slate-300 mx-2">→</span>
                        <span>{log.thought}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 bg-emerald-500 rounded-full flex items-center justify-center shrink-0 animate-pulse">
                <Bot size={16} className="text-white" />
              </div>
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <Loader2 size={16} className="animate-spin text-indigo-500" />
                Thinking...
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-slate-100">
          <div className="relative flex items-center">
            <input
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-full pl-6 pr-14 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="I have $5,000 in credit card debt..."
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="absolute right-2 p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 disabled:opacity-50 disabled:hover:bg-indigo-600 transition-colors shadow-md"
            >
              <Send size={18} />
            </button>
          </div>
          <div className="text-center mt-2">
            <p className="text-[10px] text-slate-400">AI can make mistakes. Verify financial info.</p>
          </div>
        </div>
      </div>

    </div>
  );
}