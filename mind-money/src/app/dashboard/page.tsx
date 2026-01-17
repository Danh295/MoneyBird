'use client';

import React, { useState } from 'react';
import { useFinancial } from '@/context/FinancialContext';
import { ActionItem } from '@/components/ActionItem';
import { PieChart, ListTodo, Save, Loader2 } from 'lucide-react';

export default function DashboardPage() {
  const { actions, toggleAction, financialFormSchema } = useFinancial();
  const [activeTab, setActiveTab] = useState<'overview' | 'form'>('overview');

  // Sort: Uncompleted High Priority first, then others, then completed at bottom
  const sortedActions = [...actions].sort((a, b) => {
    if (a.isCompleted === b.isCompleted) return b.priorityScore - a.priorityScore;
    return a.isCompleted ? 1 : -1;
  });

  const completedCount = actions.filter(a => a.isCompleted).length;
  const progress = actions.length > 0 ? (completedCount / actions.length) * 100 : 0;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Dashboard Header */}
      <div className="bg-white border-b border-slate-200 px-8 py-6">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Financial Command Center</h1>
            <p className="text-slate-500 text-sm">Track your progress and update your profile</p>
          </div>
          
          <div className="flex gap-2">
            <button 
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'overview' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'}`}
            >
              <ListTodo size={16} /> Action Plan
            </button>
            <button 
              onClick={() => setActiveTab('form')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'form' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'}`}
            >
              <PieChart size={16} /> Financial Profile
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          
          {/* TAB 1: ACTION CENTER */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left Column: Progress & Stats */}
              <div className="space-y-6">
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                  <h3 className="font-bold text-slate-700 mb-4">Completion Status</h3>
                  <div className="relative pt-1">
                    <div className="flex mb-2 items-center justify-between">
                      <div>
                        <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-indigo-600 bg-indigo-200">
                          Progress
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-semibold inline-block text-indigo-600">
                          {Math.round(progress)}%
                        </span>
                      </div>
                    </div>
                    <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-indigo-200">
                      <div style={{ width: `${progress}%` }} className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-indigo-600 transition-all duration-500"></div>
                    </div>
                    <p className="text-xs text-slate-500 text-center">
                      {completedCount} of {actions.length} tasks completed
                    </p>
                  </div>
                </div>
              </div>

              {/* Right Column: The Action List */}
              <div className="lg:col-span-2 space-y-4">
                 <h2 className="text-lg font-bold text-slate-800 mb-4">Priority Actions</h2>
                 {sortedActions.length === 0 ? (
                   <div className="text-center py-12 bg-white rounded-2xl border border-dashed border-slate-300">
                     <p className="text-slate-400">No actions generated yet. Chat with the AI to build your plan.</p>
                   </div>
                 ) : (
                   sortedActions.map(action => (
                     <ActionItem key={action.id} item={action} onToggle={toggleAction} />
                   ))
                 )}
              </div>
            </div>
          )}

          {/* TAB 2: DYNAMIC FINANCIAL FORM */}
          {activeTab === 'form' && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 max-w-3xl mx-auto animate-in fade-in slide-in-from-bottom-4">
              {!financialFormSchema ? (
                 <div className="text-center py-12">
                   <Loader2 className="w-12 h-12 text-indigo-200 animate-spin mx-auto mb-4" />
                   <p className="text-slate-500">No form schema available yet.</p>
                   <p className="text-xs text-slate-400">Chat with MindMoney to generate your intake form.</p>
                 </div>
              ) : (
                <form className="space-y-8">
                  <div className="border-b border-slate-100 pb-6">
                    <h2 className="text-2xl font-bold text-slate-800">{financialFormSchema.title}</h2>
                    <p className="text-slate-500">{financialFormSchema.description}</p>
                  </div>

                  {/* Dynamically Render Sections */}
                  {Object.entries(financialFormSchema).map(([key, section]: [string, any]) => {
                    if (key === 'title' || key === 'description') return null;
                    
                    return (
                      <div key={key} className="space-y-4">
                        <h3 className="text-lg font-bold text-indigo-900 border-l-4 border-indigo-500 pl-3">
                          {section.title}
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {section.fields?.map((field: any, idx: number) => (
                            <div key={idx} className={field.type === 'text' || field.type === 'select' ? "md:col-span-2" : ""}>
                              <label className="block text-sm font-medium text-slate-700 mb-1">
                                {field.label} {field.required && <span className="text-rose-500">*</span>}
                              </label>
                              
                              {field.type === 'select' ? (
                                <select className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition">
                                  {field.options.map((opt: string) => <option key={opt}>{opt}</option>)}
                                </select>
                              ) : (
                                <div className="relative">
                                  {field.unit && <span className="absolute left-3 top-3 text-slate-400 text-sm">{field.unit === 'USD' ? '$' : field.unit}</span>}
                                  <input 
                                    type={field.type} 
                                    placeholder={field.placeholder}
                                    className={`w-full p-3 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition ${field.unit ? 'pl-8' : ''}`}
                                  />
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}

                  <div className="pt-6 border-t border-slate-100">
                    <button type="button" className="w-full py-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-indigo-200">
                      <Save size={20} />
                      Save Financial Profile
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}