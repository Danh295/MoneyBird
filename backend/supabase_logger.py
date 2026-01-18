"""
Supabase Logging Service.
Persists conversation logs and agent activity for analytics.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client

from config import get_settings


class SupabaseLogger:
    """Handles persistent logging to Supabase PostgreSQL."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[Client] = None
    
    def get_client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_key
            )
        return self._client
    
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
            
            turn_data = {
                "session_id": session_id,
                "turn_number": turn_number,
                "user_message": user_message,
                "assistant_response": assistant_response,
                "intake_anxiety": state_snapshot.get("intake_profile", {}).get("emotions", {}).get("anxiety"),
                "intake_shame": state_snapshot.get("intake_profile", {}).get("emotions", {}).get("shame"),
                "safety_flag": state_snapshot.get("intake_profile", {}).get("safety_flag", False),
                "strategy_mode": state_snapshot.get("strategy_decision", {}).get("mode"),
                "entities_count": len(state_snapshot.get("financial_profile", {}).get("entities", [])),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = client.table("conversation_turns").insert(turn_data).execute()
            turn_id = result.data[0]["id"] if result.data else None
            
            for log in agent_logs:
                log_data = {
                    "session_id": session_id,
                    "turn_id": turn_id,
                    "agent_name": log.get("agent_name"),
                    "input_summary": log.get("input_summary"),
                    "output_summary": log.get("output_summary"),
                    "duration_ms": log.get("duration_ms"),
                    "model_used": log.get("model_used"),
                    "decision_made": log.get("decision_made"),
                    "created_at": log.get("timestamp", datetime.utcnow().isoformat())
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
        """Retrieve conversation history from Supabase."""
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
    
    async def get_all_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve all chat sessions with metadata."""
        try:
            client = self.get_client()
            
            # Get unique sessions with their last message
            result = client.table("conversation_turns")\
                .select("session_id, user_message, created_at")\
                .order("created_at", desc=True)\
                .limit(limit * 2)\
                .execute()
            
            if not result.data:
                return []
            
            # Group by session_id and get the latest message for each
            sessions_map = {}
            for turn in result.data:
                session_id = turn["session_id"]
                if session_id not in sessions_map:
                    sessions_map[session_id] = {
                        "session_id": session_id,
                        "preview": turn["user_message"][:100],  # First 100 chars
                        "last_message_at": turn["created_at"],
                        "created_at": turn["created_at"]
                    }
            
            # Convert to list and sort by last message
            sessions = list(sessions_map.values())
            sessions.sort(key=lambda x: x["last_message_at"], reverse=True)
            
            return sessions[:limit]
            
        except Exception as e:
            print(f"Supabase sessions query error: {e}")
            return []
    
    async def create_or_update_session(self, session_id: str, user_message: str) -> bool:
        """Create or update session metadata."""
        try:
            client = self.get_client()
            
            # Check if session exists
            existing = client.table("sessions")\
                .select("id")\
                .eq("session_id", session_id)\
                .limit(1)\
                .execute()
            
            if existing.data:
                # Update existing session
                client.table("sessions")\
                    .update({"last_message_at": datetime.utcnow().isoformat()})\
                    .eq("session_id", session_id)\
                    .execute()
            else:
                # Create new session
                client.table("sessions")\
                    .insert({"session_id": session_id})\
                    .execute()
            
            return True
            
        except Exception as e:
            print(f"Session update error: {e}")
            return False


# Singleton instance
_logger: Optional[SupabaseLogger] = None


def get_supabase_logger() -> SupabaseLogger:
    """Get or create Supabase logger singleton."""
    global _logger
    if _logger is None:
        _logger = SupabaseLogger()
    return _logger