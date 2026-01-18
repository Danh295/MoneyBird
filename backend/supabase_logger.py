"""
Supabase Service - Session Management & Logging with User Auth
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
    # USER PROFILE MANAGEMENT
    # =========================================================================
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID."""
        try:
            client = self.get_client()
            result = client.table("user_profiles")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    async def update_user_profile(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update user profile."""
        try:
            client = self.get_client()
            updates["updated_at"] = datetime.utcnow().isoformat()
            client.table("user_profiles")\
                .update(updates)\
                .eq("id", user_id)\
                .execute()
            return True
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    # =========================================================================
    # SESSION LOADING
    # =========================================================================
    
    async def load_session_history(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Load conversation history for a session.
        """
        try:
            client = self.get_client()
            
            query = client.table("conversation_turns")\
                .select("user_message, assistant_response, turn_number")\
                .eq("session_id", session_id)\
                .order("turn_number", desc=False)\
                .limit(limit)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            
            if not result.data:
                return []
            
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
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load full session context including last state snapshots.
        """
        try:
            client = self.get_client()
            
            history = await self.load_session_history(session_id, user_id, limit=20)
            
            query = client.table("conversation_turns")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("turn_number", desc=True)\
                .limit(1)
            
            if user_id:
                query = query.eq("user_id", user_id)
                
            latest = query.execute()
            
            context = {
                "conversation_history": history,
                "last_intake_profile": {},
                "last_financial_profile": {},
                "turn_count": 0
            }
            
            if latest.data:
                last_turn = latest.data[0]
                context["turn_count"] = last_turn.get("turn_number", 0)
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
    
    # --- FIXED METHOD NAME & FILTERING ---
    async def get_user_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.
        """
        try:
            client = self.get_client()
            
            query = client.table("sessions")\
                .select("session_id, first_message_at, last_message_at, preview, total_turns, had_safety_flag, user_id")\
                .order("last_message_at", desc=True)\
                .limit(limit)
            
            # STRICT FILTERING: Only return sessions belonging to this user
            if user_id:
                query = query.eq("user_id", user_id)
            else:
                pass 
            
            result = query.execute()
            
            # Additional safety: If user_id was requested, double check the results
            if user_id and result.data:
                return [s for s in result.data if s.get('user_id') == user_id]
                
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting sessions: {e}")
            return []
    
    # =========================================================================
    # LOGGING
    # =========================================================================
    
    async def log_conversation_turn(
        self,
        session_id: str,
        turn_number: int,
        user_message: str,
        assistant_response: str,
        state_snapshot: Dict[str, Any],
        agent_logs: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """Log a complete conversation turn."""
        try:
            # 1. Update Session Metadata
            await self.create_or_update_session(session_id, user_message, user_id)
            
            client = self.get_client()
            
            intake = state_snapshot.get("intake_profile", {})
            emotions = intake.get("emotional_state", {})
            safety = intake.get("safety_concerns", {})
            
            # 2. Log Turn
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
            
            if user_id:
                turn_data["user_id"] = user_id
            
            result = client.table("conversation_turns").insert(turn_data).execute()
            turn_id = result.data[0]["id"] if result.data else None
            
            # 3. Log Agent Activity
            if agent_logs:
                logs_to_insert = []
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
                    if user_id:
                        log_data["user_id"] = user_id
                    logs_to_insert.append(log_data)
                    
                if logs_to_insert:
                    client.table("agent_logs").insert(logs_to_insert).execute()
            
            return turn_id
            
        except Exception as e:
            print(f"Supabase logging error: {e}")
            return None
    
    async def get_session_history(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve full conversation history from Supabase."""
        try:
            client = self.get_client()
            
            query = client.table("conversation_turns")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("turn_number", desc=False)\
                .limit(limit)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Supabase query error: {e}")
            return []
    
    async def create_or_update_session(self, session_id: str, user_message: str, user_id: Optional[str] = None) -> bool:
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
                update_data = {"last_message_at": datetime.utcnow().isoformat()}
                if user_id:
                    update_data["user_id"] = user_id # Ensure ownership is claimed if previously anon
                    
                client.table("sessions")\
                    .update(update_data)\
                    .eq("session_id", session_id)\
                    .execute()
            else:
                # Create new session
                preview = user_message[:100] + "..." if len(user_message) > 100 else user_message
                session_data = {
                    "session_id": session_id,
                    "preview": preview,
                    "first_message_at": datetime.utcnow().isoformat(),
                    "last_message_at": datetime.utcnow().isoformat()
                }
                if user_id:
                    session_data["user_id"] = user_id
                    
                client.table("sessions")\
                    .insert(session_data)\
                    .execute()
            
            return True
            
        except Exception as e:
            print(f"Session update error: {e}")
            return False


_service: Optional[SupabaseService] = None

def get_supabase_service() -> SupabaseService:
    global _service
    if _service is None:
        _service = SupabaseService()
    return _service

def get_supabase_logger() -> SupabaseService:
    return get_supabase_service()