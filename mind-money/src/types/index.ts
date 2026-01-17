// src/types/index.ts
export type Role = 'user' | 'assistant';

export interface Message {
  id: string;
  role: Role;
  content: string;
}

export type AgentName = 'Intake Specialist' | 'Wealth Architect' | 'Care Manager';

export interface AgentLog {
  id: string;
  agentName: AgentName;
  status: 'active' | 'complete' | 'waiting';
  thought: string; // The "reasoning" text
  output?: string; // What they decided
}