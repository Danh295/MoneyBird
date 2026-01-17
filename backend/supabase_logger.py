"""
Supabase Service - Session Management & Logging
Handles conversation persistence and retrieval for multi-turn agent context.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client

from config import get_settings


class SupabaseService:
    """Handles all Supabase operations for MindMoney."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[Client] = None
    
    def get_client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            if not self.settings.supabase_url or not self.settings.supabase_key:
                raise ValueError("Supabase URL and Key must be configured")
            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_key
            )
        return self._client
    
    # =========================================================================
    # SESSION LOADING - For Agents to Access Previous Context
    # =========================================================================
    
    async def load_session_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Load conversation history for a session.
        Returns format compatible with agent's conversation_history field.
        
        Args:
            session_id: The session to load
            limit: Max number of turns to retrieve (default 10)
            
        Returns:
            List of {"role": "user"|"assistant", "content": "message"}
        """
        try:
            client = self.get_client()
            
            result = client.table("conversation_turns")\
                .select("user_message, assistant_response, turn_number")\
                .eq("session_id", session_id)\
                .order("turn_number", desc=False)\
                .limit(limit)\
                .execute()
            
            if not result.data:
                return []
            
            # Convert to conversation history format
            history = []
            for turn in result.data:
                history.append({
                    "role": "user",
                    "content": turn["user_message"]
                })
                history.append({
                    "role": "assistant", 
                    "content": turn["assistant_response"]
                })
            
            return history
            
        except Exception as e:
            print(f"Error loading session history: {e}")
            return []
    
    async def load_session_context(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Load full session context including last state snapshots.
        Useful for resuming a session with full agent context.
        
        Returns:
            {
                "conversation_history": [...],
                "last_intake_profile": {...},
                "last_financial_profile": {...},
                "turn_count": int
            }
        """
        try:
            client = self.get_client()
            
            # Get conversation history
            history = await self.load_session_history(session_id, limit=20)
            
            # Get the most recent turn for state info
            latest = client.table("conversation_turns")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("turn_number", desc=True)\
                .limit(1)\
                .execute()
            
            context = {
                "conversation_history": history,
                "last_intake_profile": {},
                "last_financial_profile": {},
                "turn_count": 0
            }
            
            if latest.data:
                last_turn = latest.data[0]
                context["turn_count"] = last_turn.get("turn_number", 0)
                
                # If you store full state snapshots, you can retrieve them here
                # For now we just have the basic metrics
                context["last_intake_profile"] = {
                    "emotional_state": {
                        "anxiety": last_turn.get("intake_anxiety"),
                        "shame": last_turn.get("intake_shame")
                    },
                    "safety_concerns": {
                        "crisis_flag": last_turn.get("safety_flag", False)
                    }
                }
            
            return context
            
        except Exception as e:
            print(f"Error loading session context: {e}")
            return {
                "conversation_history": [],
                "last_intake_profile": {},
                "last_financial_profile": {},
                "turn_count": 0
            }
    
    async def get_all_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions (optionally filtered by user_id).
        Returns summary info for session list UI.
        """
        try:
            client = self.get_client()
            
            query = client.table("sessions")\
                .select("session_id, first_message_at, last_message_at, total_turns, had_safety_flag")\
                .order("last_message_at", desc=True)\
                .limit(limit)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting sessions: {e}")
            return []
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists in the database."""
        try:
            client = self.get_client()
            result = client.table("conversation_turns")\
                .select("id")\
                .eq("session_id", session_id)\
                .limit(1)\
                .execute()
            return len(result.data) > 0
        except Exception:
            return False
    
    # =========================================================================
    # LOGGING - Save Conversation Turns
    # =========================================================================
    
    async def log_conversation_turn(
        self,
        session_id: str,
        turn_number: int,
        user_message: str,
        assistant_response: str,
        state_snapshot: Dict[str, Any],
        agent_logs: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Log a complete conversation turn."""
        try:
            client = self.get_client()
            
            # Extract intake profile data
            intake = state_snapshot.get("intake_profile", {})
            emotions = intake.get("emotional_state", {})
            safety = intake.get("safety_concerns", {})
            
            turn_data = {
                "session_id": session_id,
                "turn_number": turn_number,
                "user_message": user_message,
                "assistant_response": assistant_response,
                "intake_anxiety": emotions.get("anxiety"),
                "intake_shame": emotions.get("shame"),
                "safety_flag": safety.get("crisis_flag", False),
                "strategy_mode": state_snapshot.get("strategy_decision", {}).get("mode"),
                "entities_count": len(state_snapshot.get("financial_profile", {}).get("debt_analysis", {}).get("debt_types", [])),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = client.table("conversation_turns").insert(turn_data).execute()
            turn_id = result.data[0]["id"] if result.data else None
            
            # Log each agent's activity
            for log in agent_logs:
                log_data = {
                    "session_id": session_id,
                    "turn_id": turn_id,
                    "agent_name": log.get("agent", "unknown"),
                    "input_summary": log.get("thought", ""),
                    "output_summary": log.get("status", ""),
                    "duration_ms": log.get("duration_ms"),
                    "model_used": self.settings.model_name,
                    "decision_made": log.get("thought", ""),
                    "created_at": datetime.utcnow().isoformat()
                }
                client.table("agent_logs").insert(log_data).execute()
            
            return turn_id
            
        except Exception as e:
            print(f"Supabase logging error: {e}")
            return None
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve full conversation history from Supabase."""
        try:
            client = self.get_client()
            
            result = client.table("conversation_turns")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("turn_number", desc=False)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Supabase query error: {e}")
            return []
    
    async def get_agent_logs(
        self,
        session_id: str,
        turn_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve agent logs for a session or specific turn."""
        try:
            client = self.get_client()
            
            query = client.table("agent_logs")\
                .select("*")\
                .eq("session_id", session_id)
            
            if turn_id:
                query = query.eq("turn_id", turn_id)
            
            result = query.order("created_at", desc=False).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Supabase query error: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Supabase is connected."""
        try:
            client = self.get_client()
            client.table("conversation_turns").select("id").limit(1).execute()
            return True
        except Exception:
            return False


# Singleton instance
_service: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    """Get or create Supabase service singleton."""
    global _service
    if _service is None:
        _service = SupabaseService()
    return _service


# Backwards compatibility alias
def get_supabase_logger() -> SupabaseService:
    """Alias for backwards compatibility."""
    return get_supabase_service()