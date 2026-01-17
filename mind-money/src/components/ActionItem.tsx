import React from 'react';
import { CheckCircle2, Circle, Clock, ArrowUpRight } from 'lucide-react';
import { ActionItem as ActionType } from '@/context/FinancialContext';
import clsx from 'clsx';

export const ActionItem = ({ item, onToggle }: { item: ActionType; onToggle: (id: string) => void }) => {
  return (
    <div 
      onClick={() => onToggle(item.id)}
      className={clsx(
        "group flex items-start gap-4 p-4 rounded-xl border transition-all cursor-pointer hover:shadow-md",
        item.isCompleted 
          ? "bg-slate-50 border-slate-100 opacity-60" 
          : "bg-white border-slate-200 hover:border-indigo-300"
      )}
    >
      {/* Checkbox */}
      <div className={clsx(
        "mt-1 transition-colors",
        item.isCompleted ? "text-emerald-500" : "text-slate-300 group-hover:text-indigo-400"
      )}>
        {item.isCompleted ? <CheckCircle2 size={24} /> : <Circle size={24} />}
      </div>

      <div className="flex-1">
        <div className="flex justify-between items-start">
          <h4 className={clsx(
            "font-semibold text-sm",
            item.isCompleted ? "text-slate-500 line-through" : "text-slate-800"
          )}>
            {item.action}
          </h4>
          
          {/* Difficulty Badge */}
          <span className={clsx(
            "text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wide",
            item.difficulty === 'easy' ? "bg-emerald-100 text-emerald-700" :
            item.difficulty === 'medium' ? "bg-amber-100 text-amber-700" :
            "bg-rose-100 text-rose-700"
          )}>
            {item.difficulty}
          </span>
        </div>

        <p className="text-xs text-slate-500 mt-1 mb-2">
          {item.expected_impact}
        </p>

        <div className="flex items-center gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-1">
            <Clock size={12} />
            {item.deadline}
          </div>
          {/* Priority Indicator */}
          {item.priorityScore >= 3 && !item.isCompleted && (
             <span className="text-rose-500 font-bold flex items-center gap-1">
               <ArrowUpRight size={12} /> High Priority
             </span>
          )}
        </div>
      </div>
    </div>
  );
};