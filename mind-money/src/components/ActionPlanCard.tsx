import React from 'react';
import Link from 'next/link';
import { CheckCircle2, ArrowRight, Target, Clock, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

// This interface matches the JSON output from your Python ActionGenerator agent
interface ActionPlanData {
  financial_health_score?: number;
  financial_planning_form?: {
    title?: string;
    description?: string;
  };
  immediate_actions?: Array<{
    action: string;
    deadline: string;
    difficulty: 'easy' | 'medium' | 'hard';
    expected_impact: string;
  }>;
  quick_wins?: string[];
  next_steps?: {
    fill_form?: string;
    after_form?: string;
  };
}

export function ActionPlanCard({ data }: { data: ActionPlanData }) {
  // Guard clause: Don't render if there's no actionable data
  if (!data || (!data.immediate_actions && !data.quick_wins)) return null;

  return (
    <div className="mt-6 w-full bg-white rounded-xl border border-indigo-100 shadow-xl shadow-indigo-100/50 overflow-hidden animate-in slide-in-from-bottom-4 duration-500">
      
      {/* HEADER BANNER */}
      <div className="bg-linear-to-r from-indigo-600 to-violet-600 p-5 text-white flex justify-between items-center">
        <div>
          <div className="flex items-center gap-2 mb-1 opacity-90">
            <Target className="w-4 h-4 text-indigo-200" />
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-100">Strategic Roadmap</span>
          </div>
          <h3 className="font-bold text-xl tracking-tight">Your Action Plan</h3>
        </div>
        
        {/* Optional Health Score Badge */}
        {data.financial_health_score !== undefined && (
          <div className="text-center bg-white/10 backdrop-blur-md rounded-lg px-3 py-2 border border-white/20 shadow-inner">
            <div className="text-[10px] text-indigo-100 uppercase tracking-wide font-medium">Health Score</div>
            <div className="text-2xl font-bold leading-none">{data.financial_health_score}</div>
          </div>
        )}
      </div>

      <div className="p-6 space-y-8">
        
        {/* SECTION 1: QUICK WINS (High Dopamine) */}
        {data.quick_wins && data.quick_wins.length > 0 && (
          <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-5 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-emerald-100 rounded-bl-full -mr-8 -mt-8 opacity-50" />
            
            <h4 className="flex items-center gap-2 text-sm font-bold text-emerald-800 mb-4 relative z-10">
              <CheckCircle2 className="w-5 h-5" />
              Quick Wins (Do these today)
            </h4>
            
            <ul className="space-y-3 relative z-10">
              {data.quick_wins.map((win, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm text-emerald-900/80 bg-white/60 p-2 rounded-lg border border-emerald-100/50">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  <span className="leading-relaxed">{win}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* SECTION 2: PRIORITY ACTIONS TABLE */}
        {data.immediate_actions && data.immediate_actions.length > 0 && (
          <div>
            <h4 className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-500" />
              Priority Actions
            </h4>
            
            <div className="space-y-3">
              {data.immediate_actions.map((item, idx) => (
                <div 
                  key={idx} 
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all group"
                >
                  <div className="flex items-start gap-3 mb-3 sm:mb-0">
                    <div className={clsx(
                      "mt-1.5 w-2 h-2 rounded-full shrink-0",
                      item.difficulty === 'hard' ? 'bg-rose-400 shadow-[0_0_8px_rgba(251,113,133,0.6)]' : 
                      item.difficulty === 'medium' ? 'bg-amber-400' : 'bg-emerald-400'
                    )} />
                    <div>
                      <p className="text-sm font-semibold text-slate-800 group-hover:text-indigo-700 transition-colors">
                        {item.action}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5">{item.expected_impact}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between sm:justify-end gap-4 pl-5 sm:pl-0 border-l-2 border-slate-200 sm:border-l-0">
                    <span className={clsx(
                      "text-[10px] px-2 py-1 rounded font-medium uppercase tracking-wide",
                      item.difficulty === 'easy' ? "bg-emerald-100 text-emerald-700" :
                      item.difficulty === 'medium' ? "bg-amber-100 text-amber-700" :
                      "bg-rose-100 text-rose-700"
                    )}>
                      {item.difficulty}
                    </span>
                    <span className="text-xs font-mono text-slate-500 bg-white px-2 py-1 rounded border border-slate-200">
                      {item.deadline}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 3: CTA TO DASHBOARD */}
        <div className="pt-2">
           <Link href="/dashboard" className="block w-full group"> 
            <button className="w-full py-4 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-sm rounded-xl transition-all flex items-center justify-center gap-2 border border-indigo-200 hover:border-indigo-300 hover:shadow-lg hover:shadow-indigo-100/50">
              Open Full Financial Dashboard 
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </Link>
          <p className="text-center text-[10px] text-slate-400 mt-3 flex items-center justify-center gap-1.5">
            <AlertCircle size={10} />
            Data automatically saved to your dashboard
          </p>
        </div>

      </div>
    </div>
  );
}