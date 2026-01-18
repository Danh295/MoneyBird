'use client';

import React from 'react';
import Link from 'next/link';
import { CheckCircle2, Target, Clock, AlertCircle, ArrowRight, LayoutDashboard } from 'lucide-react';
import clsx from 'clsx';

interface ActionPlanData {
  financial_health_score?: number;
  financial_planning_form?: { title?: string; description?: string; };
  immediate_actions?: Array<{ action: string; deadline: string; difficulty: 'easy' | 'medium' | 'hard'; expected_impact: string; }>;
  quick_wins?: string[];
}

export function ActionPlanCard({ data }: { data: ActionPlanData }) {
  if (!data || (!data.immediate_actions && !data.quick_wins)) return null;

  return (
    <div className="mt-6 w-full bg-white rounded-xl border border-[var(--border)] shadow-xl shadow-[var(--shadow-lg)] overflow-hidden animate-in slide-in-from-bottom-4 duration-500">
      
      {/* HEADER */}
      <div className="bg-[var(--primary)] p-5 text-white flex justify-between items-center">
        <div>
          <div className="flex items-center gap-2 mb-1 opacity-90">
            <Target className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-wider">Strategic Blueprint</span>
          </div>
          <h3 className="font-bold text-lg">Financial Action Plan</h3>
        </div>
        {data.financial_health_score && (
          <div className="text-center bg-white/20 p-2 rounded-lg backdrop-blur-sm">
            <div className="text-xs opacity-80">Health Score</div>
            <div className="text-2xl font-bold">{data.financial_health_score}</div>
          </div>
        )}
      </div>

      <div className="p-5 space-y-6">
        {/* SECTION 1: QUICK WINS */}
        {data.quick_wins && data.quick_wins.length > 0 && (
          <div className="space-y-3">
             <h4 className="text-[var(--success)] text-xs font-bold uppercase tracking-wider flex items-center gap-2">
               <CheckCircle2 size={14} /> Quick Wins (Do these now)
             </h4>
             <div className="grid gap-2">
               {data.quick_wins.map((win, i) => (
                 <div key={i} className="flex items-center gap-3 p-3 bg-[var(--neutral)] rounded-lg text-sm text-[var(--text-primary)]">
                   <div className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
                   {win}
                 </div>
               ))}
             </div>
          </div>
        )}

        {/* SECTION 2: IMMEDIATE ACTIONS */}
        {data.immediate_actions && data.immediate_actions.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-[var(--primary)] text-xs font-bold uppercase tracking-wider flex items-center gap-2">
               <Clock size={14} /> Core Actions
            </h4>
            <div className="space-y-3">
              {data.immediate_actions.map((item, i) => (
                <div key={i} className="border border-[var(--border)] rounded-xl p-4 hover:border-[var(--primary)] transition-colors group">
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-semibold text-[var(--text-primary)]">{item.action}</span>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] mb-3">{item.expected_impact}</p>
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      "text-[10px] px-2 py-0.5 rounded-full font-bold uppercase",
                      item.difficulty === 'easy' ? "bg-[var(--success)] text-white" :
                      item.difficulty === 'medium' ? "bg-[var(--secondary)] text-[var(--text-primary)]" :
                      "bg-[var(--danger)] text-white"
                    )}>
                      {item.difficulty}
                    </span>
                    <span className="text-xs font-mono text-[var(--text-secondary)] bg-[var(--neutral)] px-2 py-1 rounded">
                      {item.deadline}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 3: DASHBOARD LINK (Restored) */}
        <div className="pt-2 border-t border-[var(--border)] mt-4">
           <Link href="/dashboard" className="block w-full group"> 
            <button className="w-full py-3 bg-[var(--neutral)] hover:bg-[var(--border)] text-[var(--text-primary)] font-bold text-sm rounded-xl transition-all flex items-center justify-center gap-2">
              <LayoutDashboard size={16} />
              Open Full Financial Dashboard 
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </Link>
          <p className="text-center text-[10px] text-[var(--text-light)] mt-3 flex items-center justify-center gap-1.5">
            <AlertCircle size={10} />
            Data automatically saved to your dashboard
          </p>
        </div>

      </div>
    </div>
  );
}