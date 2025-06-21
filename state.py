from typing import TypedDict, Optional, Dict, Any, List
from langgraph.checkpoint.memory import MemorySaver

def chat_history_reducer(old_history: List[Dict], new_history: List[Dict]) -> List[Dict]:
    """Custom reducer to keep chat history as simple dictionaries."""
    if not old_history:
        return new_history
    if not new_history:
        return old_history
    
    # Combine histories, ensuring they remain as dictionaries
    combined = old_history.copy()
    for msg in new_history:
        if isinstance(msg, dict):
            combined.append(msg)
        else:
            # Convert LangChain message objects to dicts if needed
            if hasattr(msg, 'content'):
                role = "user" if hasattr(msg, 'type') and msg.type == 'human' else "assistant"
                combined.append({"role": role, "content": msg.content})
            else:
                combined.append({"role": "assistant", "content": str(msg)})
    
    return combined

class State(TypedDict):
    # Inputs
    profile_url: str
    session_id: str
    command: str
    user_question: Optional[str]
    job_description: Optional[str]

    # Outputs / Agent data
    profile: Optional[Dict[str, Any]]
    analysis: Optional[Dict[str, Any]]
    job_fit: Optional[Dict[str, Any]]
    enhanced_content: Optional[Dict[str, Any]]
    coaching: Optional[Dict[str, Any]]

    # Conversation context - simple list of dictionaries with custom reducer
    chat_history: List[Dict[str, str]]

    # Error handling
    error: Optional[str]

# Create memory saver instance
memory_saver = MemorySaver()