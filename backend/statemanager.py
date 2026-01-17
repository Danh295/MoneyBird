"""
Redis State Management Service.
Handles session state persistence and retrieval.
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime
import redis.asyncio as redis

from config import get_settings


class RedisStateManager:
    """Manages session state in Redis."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
    
    def _state_key(self, session_id: str) -> str:
        """Generate Redis key for session state."""
        return f"mindmoney:state:{session_id}"
    
    def _history_key(self, session_id: str) -> str:
        """Generate Redis key for conversation history."""
        return f"mindmoney:history:{session_id}"
    
    async def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session state from Redis."""
        client = await self.get_client()
        data = await client.get(self._state_key(session_id))
        
        if data:
            return json.loads(data)
        return None
    
    async def save_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """Save session state to Redis."""
        client = await self.get_client()
        
        state["_last_updated"] = datetime.utcnow().isoformat()
        
        await client.setex(
            self._state_key(session_id),
            self.settings.state_ttl,
            json.dumps(state, default=str)
        )
        
        return True
    
    async def get_conversation_history(self, session_id: str) -> list:
        """Get conversation history for a session."""
        client = await self.get_client()
        data = await client.get(self._history_key(session_id))
        
        if data:
            return json.loads(data)
        return []
    
    async def append_to_history(
        self, 
        session_id: str, 
        user_message: str, 
        assistant_response: str
    ) -> bool:
        """Append a turn to conversation history."""
        client = await self.get_client()
        
        history = await self.get_conversation_history(session_id)
        history.append({
            "user": user_message,
            "assistant": assistant_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 20 turns
        if len(history) > 20:
            history = history[-20:]
        
        await client.setex(
            self._history_key(session_id),
            self.settings.state_ttl,
            json.dumps(history)
        )
        
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete all data for a session."""
        client = await self.get_client()
        
        await client.delete(self._state_key(session_id))
        await client.delete(self._history_key(session_id))
        
        return True
    
    async def health_check(self) -> bool:
        """Check if Redis is connected."""
        try:
            client = await self.get_client()
            await client.ping()
            return True
        except Exception:
            return False


# Singleton instance
_state_manager: Optional[RedisStateManager] = None


def get_state_manager() -> RedisStateManager:
    """Get or create state manager singleton."""
    global _state_manager
    if _state_manager is None:
        _state_manager = RedisStateManager()
    return _state_manager