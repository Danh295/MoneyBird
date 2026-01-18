'use client';

import React, { useState } from 'react';
import { useFinancial } from '@/context/FinancialContext';
import { ActionItem } from '@/components/ActionItem';
import { PieChart, ListTodo, Save, Loader2, ArrowLeft, Target, Sparkles, LogIn, LogOut } from 'lucide-react';
import Link from 'next/link';
import clsx from 'clsx';
import { useAuth } from '@/contexts/AuthContext';
import AuthModal from '@/components/AuthModal';

export default function DashboardPage() {
  const { actions, toggleAction, financialFormSchema } = useFinancial();
  const { user, signOut } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'form'>('overview');
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Sort: Uncompleted High Priority first
  const sortedActions = [...actions].sort((a, b) => {
    if (a.isCompleted === b.isCompleted) return b.priorityScore - a.priorityScore;
    return a.isCompleted ? 1 : -1;
  });

  const completedCount = actions.filter(a => a.isCompleted).length;
  const progress = actions.length > 0 ? (completedCount / actions.length) * 100 : 0;

  return (
    <div className="min-h-screen bg-[var(--background)] flex flex-col">
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />

      {/* Dashboard Header */}
      <div className="bg-white border-b border-[var(--border)] px-8 py-6 sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto">
          
          <div className="flex justify-between items-center mb-6">
            <Link href="/" className="inline-flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--primary)] transition-colors text-sm font-medium">
              <ArrowLeft size={16} />
              Back to Conversation
            </Link>

            {/* Auth Button */}
            {user ? (
              <button 
                onClick={() => signOut()} 
                className="flex items-center gap-2 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--danger)] transition-colors"
              >
                <LogOut size={14} />
                Sign Out ({user.email})
              </button>
            ) : (
              <button 
                onClick={() => setShowAuthModal(true)} 
                className="flex items-center gap-2 text-sm font-medium text-[var(--primary)] hover:text-[var(--primary-dark)] transition-colors"
              >
                <LogIn size={16} /> Sign In to Save
              </button>
            )}
          </div>

          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Target className="w-5 h-5 text-[var(--primary)]" />
                <h1 className="text-2xl font-bold text-[var(--text-primary)]">Financial Command Center</h1>
              </div>
              <p className="text-[var(--text-secondary)] text-sm ml-7">Track your progress and update your financial profile</p>
            </div>
            
            <div className="flex p-1 bg-[var(--neutral)] rounded-xl border border-[var(--border)]">
              <button 
                onClick={() => setActiveTab('overview')}
                className={clsx(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                  activeTab === 'overview' 
                    ? "bg-white text-[var(--primary)] shadow-sm" 
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                )}
              >
                <ListTodo size={16} /> Action Plan
              </button>
              <button 
                onClick={() => setActiveTab('form')}
                className={clsx(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                  activeTab === 'form' 
                    ? "bg-white text-[var(--primary)] shadow-sm" 
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                )}
              >
                <PieChart size={16} /> Financial Profile
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          
          {/* TAB 1: ACTION CENTER */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-4">
              {/* Left Column: Progress & Stats */}
              <div className="space-y-6">
                <div className="bg-white p-6 rounded-2xl border border-[var(--border)] shadow-sm">
                  <h3 className="font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[var(--accent)]" />
                    Completion Status
                  </h3>
                  <div className="relative pt-1">
                    <div className="flex mb-2 items-center justify-between">
                      <div>
                        <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-[var(--primary)] bg-[var(--neutral)]">
                          Progress
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-semibold inline-block text-[var(--primary)]">
                          {Math.round(progress)}%
                        </span>
                      </div>
                    </div>
                    <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-[var(--neutral)]">
                      <div style={{ width: `${progress}%` }} className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] transition-all duration-1000 ease-out"></div>
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] text-center">
                      {completedCount} of {actions.length} tasks completed
                    </p>
                  </div>
                </div>
              </div>

              {/* Right Column: The Action List */}
              <div className="lg:col-span-2 space-y-4">
                 <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4">Priority Actions</h2>
                 {sortedActions.length === 0 ? (
                   <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-[var(--border)]">
                     <ListTodo className="w-12 h-12 text-[var(--text-light)] mx-auto mb-3" />
                     <p className="text-[var(--text-secondary)]">No actions generated yet.</p>
                     <p className="text-xs text-[var(--text-light)] mt-1">Chat with MindMoney to build your plan.</p>
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
            <div className="bg-white rounded-2xl border border-[var(--border)] shadow-sm p-8 max-w-3xl mx-auto animate-in fade-in slide-in-from-bottom-4">
              {!financialFormSchema ? (
                 <div className="text-center py-16">
                   <Loader2 className="w-12 h-12 text-[var(--primary)]/30 animate-spin mx-auto mb-4" />
                   <p className="text-[var(--text-secondary)]">No form schema available yet.</p>
                   <p className="text-xs text-[var(--text-light)] mt-1">Chat with MindMoney to generate your intake form.</p>
                 </div>
              ) : (
                <form className="space-y-8">
                  <div className="border-b border-[var(--border)] pb-6">
                    <h2 className="text-2xl font-bold text-[var(--text-primary)]">{financialFormSchema.title}</h2>
                    <p className="text-[var(--text-secondary)]">{financialFormSchema.description}</p>
                  </div>

                  {/* Dynamically Render Sections */}
                  {Object.entries(financialFormSchema).map(([key, section]: [string, any]) => {
                    if (key === 'title' || key === 'description') return null;
                    
                    return (
                      <div key={key} className="space-y-4">
                        <h3 className="text-lg font-bold text-[var(--primary-dark)] border-l-4 border-[var(--primary)] pl-3">
                          {section.title}
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {section.fields?.map((field: any, idx: number) => (
                            <div key={idx} className={field.type === 'text' || field.type === 'select' ? "md:col-span-2" : ""}>
                              <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
                                {field.label} {field.required && <span className="text-[var(--danger)]">*</span>}
                              </label>
                              
                              {field.type === 'select' ? (
                                <select className="w-full p-3 bg-[var(--neutral)] border border-[var(--border)] rounded-lg focus:ring-2 focus:ring-[var(--primary)] outline-none transition text-[var(--text-primary)]">
                                  {field.options.map((opt: string) => <option key={opt}>{opt}</option>)}
                                </select>
                              ) : (
                                <div className="relative">
                                  {field.unit && <span className="absolute left-3 top-3 text-[var(--text-light)] text-sm">{field.unit === 'USD' ? '$' : field.unit}</span>}
                                  <input 
                                    type={field.type} 
                                    placeholder={field.placeholder}
                                    className={`w-full p-3 bg-[var(--neutral)] border border-[var(--border)] rounded-lg focus:ring-2 focus:ring-[var(--primary)] outline-none transition text-[var(--text-primary)] ${field.unit ? 'pl-8' : ''}`}
                                  />
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}

                  <div className="pt-6 border-t border-[var(--border)]">
                    <button type="button" className="w-full py-4 bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] hover:shadow-lg text-white font-bold rounded-xl flex items-center justify-center gap-2 transition-all">
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