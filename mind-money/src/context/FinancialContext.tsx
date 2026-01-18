'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

// Define the shape of an Action Item
export type ActionItem = {
  id: string;
  action: string;
  deadline: string;
  difficulty: 'easy' | 'medium' | 'hard';
  expected_impact: string;
  isCompleted: boolean;
  priorityScore: number; // 3 for High, 2 for Medium, 1 for Low
};

type FinancialContextType = {
  actions: ActionItem[];
  addActionPlan: (rawJson: any) => void;
  toggleAction: (id: string) => void;
  financialFormSchema: any | null; // Stores the form structure from AI
};

const FinancialContext = createContext<FinancialContextType | undefined>(undefined);

export function FinancialProvider({ children }: { children: React.ReactNode }) {
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [financialFormSchema, setFinancialFormSchema] = useState<any>(null);


  useEffect(() => {
    const saved = localStorage.getItem('moneybird_actions');
    if (saved) setActions(JSON.parse(saved));
  }, []);

  // Save to local storage whenever actions change
  useEffect(() => {
    localStorage.setItem('moneybird_actions', JSON.stringify(actions));
  }, [actions]);

  const addActionPlan = (rawJson: any) => {
    // 1. Save the Form Schema
    if (rawJson.financial_planning_form) {
      setFinancialFormSchema(rawJson.financial_planning_form);
    }

    // 2. Parse and Merge Actions
    if (rawJson.immediate_actions) {
      const newActions: ActionItem[] = rawJson.immediate_actions.map((item: any) => ({
        id: Math.random().toString(36).substr(2, 9),
        action: item.action,
        deadline: item.deadline,
        difficulty: item.difficulty,
        expected_impact: item.expected_impact,
        isCompleted: false,
        // Assign numeric score for sorting
        priorityScore: item.deadline.includes('week') ? 3 : item.deadline.includes('month') ? 2 : 1
      }));
      
      // Add new actions to the top of the list
      setActions(prev => [...newActions, ...prev]);
    }
  };

  const toggleAction = (id: string) => {
    setActions(prev => prev.map(a => 
      a.id === id ? { ...a, isCompleted: !a.isCompleted } : a
    ));
  };

  return (
    <FinancialContext.Provider value={{ actions, addActionPlan, toggleAction, financialFormSchema }}>
      {children}
    </FinancialContext.Provider>
  );
}

export const useFinancial = () => {
  const context = useContext(FinancialContext);
  if (!context) throw new Error('useFinancial must be used within a FinancialProvider');
  return context;
};