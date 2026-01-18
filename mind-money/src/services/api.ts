// src/services/api.ts

import { 
  Session, 
  SessionContext, 
  ChatRequest, 
  ChatResponse, 
  ConversationMessage,
  AgentLog 
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // =========================================================================
  // SESSION MANAGEMENT
  // =========================================================================

  /**
   * Get all available sessions
   */
  async getSessions(userId?: string): Promise<Session[]> {
    try {
      const url = userId 
        ? `${this.baseUrl}/api/sessions?user_id=${userId}`
        : `${this.baseUrl}/api/sessions`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch sessions: ${response.status}`);
      }
      
      const data = await response.json();
      return data.sessions || [];
    } catch (error) {
      console.error('Error fetching sessions:', error);
      return [];
    }
  }

  /**
   * Load a specific session's full context
   */
  async loadSession(sessionId: string): Promise<SessionContext | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/sessions/${sessionId}`);
      
      if (response.status === 404) {
        return null; // Session doesn't exist yet
      }
      
      if (!response.ok) {
        throw new Error(`Failed to load session: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error loading session:', error);
      return null;
    }
  }

  /**
   * Get conversation history for a session
   */
  async getSessionHistory(sessionId: string, limit: number = 50): Promise<ConversationMessage[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/sessions/${sessionId}/history?limit=${limit}`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch history: ${response.status}`);
      }
      
      const data = await response.json();
      return data.history || [];
    } catch (error) {
      console.error('Error fetching session history:', error);
      return [];
    }
  }

  /**
   * Get agent logs for a session
   */
  async getSessionLogs(sessionId: string): Promise<AgentLog[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/sessions/${sessionId}/logs`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch logs: ${response.status}`);
      }
      
      const data = await response.json();
      return data.logs || [];
    } catch (error) {
      console.error('Error fetching session logs:', error);
      return [];
    }
  }

  // =========================================================================
  // CHAT
  // =========================================================================

  /**
   * Send a chat message
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chat API error: ${response.status} - ${errorText}`);
    }

    return await response.json();
  }

  // =========================================================================
  // HEALTH CHECK
  // =========================================================================

  /**
   * Check if the backend is healthy
   */
  async healthCheck(): Promise<{ status: string; supabase_connected: boolean }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return await response.json();
    } catch (error) {
      return { status: 'unhealthy', supabase_connected: false };
    }
  }
}

// Export singleton instance
export const api = new ApiService();

// Export class for custom instances
export { ApiService };