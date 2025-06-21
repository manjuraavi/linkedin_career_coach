import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
import json

logger = logging.getLogger("profile_analyzer_agent")

class ProfileAnalyzerAgent:
    """Production-grade, GPT-powered LinkedIn Profile Analyzer Agent."""
    def __init__(self, openai_api_key: str):
        # Use LangChain's ChatOpenAI for LLM calls, passing the API key
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.2,
            openai_api_key=openai_api_key
        )

    def analyze(self, profile: Dict[str, Any], session_id: str = None, user_question: str = None, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Analyze LinkedIn profile and return strengths, weaknesses, and improvement suggestions."""
        about = profile.get("about", "")
        experience = profile.get("experience", [])
        skills = profile.get("skills", [])
        name = profile.get("name", "User")
        
        # If this is a chat interaction, provide a conversational response
        if user_question:
            return self._handle_chat_analysis(profile, user_question, session_id, chat_history)
        
        # Standard analysis
        prompt = (
            f"You are a world-class LinkedIn profile analyst.\n"
            f"Given the following profile, analyze strengths, weaknesses, and give 3-5 actionable suggestions.\n"
            f"\nProfile About: {about}\nExperience: {experience}\nSkills: {skills}\n"
            f"\nRespond in JSON with keys: strengths, weaknesses, suggestions."
        )
        try:
            response = self.llm.invoke([
                {"type": "system", "content": "You are a LinkedIn profile analysis expert."},
                {"type": "human", "content": prompt}
            ])
            result = response.content.strip()
            try:
                analysis = json.loads(result)
            except Exception:
                analysis = {"raw": result}
            logger.info(f"Profile analysis completed for session {session_id}")
            return analysis
        except Exception as e:
            logger.error(f"Error in profile analysis for session {session_id}: {str(e)}")
            return {
                "error": f"Profile analysis failed: {str(e)}",
                "strengths": [],
                "weaknesses": [],
                "suggestions": ["Unable to analyze profile due to an error"]
            }

    def _handle_chat_analysis(self, profile: Dict[str, Any], user_question: str, session_id: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Handle chat-based profile analysis requests."""
        about = profile.get("about", "")
        experience = profile.get("experience", [])
        skills = profile.get("skills", [])
        name = profile.get("name", "User")
        
        # Build conversation context from chat history
        context = self._build_conversation_context(chat_history or [])
        
        system_prompt = """You are an expert LinkedIn profile analyst. When users ask about their profile, provide detailed, actionable insights in a conversational tone. Use markdown formatting and be specific about their profile data. Consider the conversation history when providing analysis."""

        user_prompt = f"""**User Profile:**
- Name: {name}
- About: {about}
- Experience: {experience}
- Skills: {skills}

**Conversation History:** {context}

**User Question:** {user_question}

Please provide a detailed, helpful response that directly addresses their question about their profile. Be specific and actionable. Consider what was discussed previously in the conversation."""

        try:
            response = self.llm.invoke([
                {"type": "system", "content": system_prompt},
                {"type": "human", "content": user_prompt}
            ])
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "message": content.strip(),
                "type": "profile_analysis",
                "session_id": session_id,
                "user_question": user_question,  # Include user question for tracking
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in chat analysis for session {session_id}: {str(e)}")
            return {
                "message": "I apologize, but I encountered an issue analyzing your profile. Please try rephrasing your question.",
                "error": str(e),
                "type": "error",
                "session_id": session_id,
                "success": False
            }

    def _build_conversation_context(self, chat_history: List[Dict]) -> str:
        """Build conversation context from chat history."""
        if not chat_history:
            return "This is the beginning of our conversation."
        
        # Take last 3 exchanges to avoid token limits
        recent_messages = chat_history[-6:]  # 3 user + 3 assistant messages
        context_parts = []
        
        for msg in recent_messages:
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:150]  # Limit content length
                
                if role == "user":
                    context_parts.append(f"User: {content}")
                elif role == "assistant":
                    context_parts.append(f"Assistant: {content}")
            else:
                # Fallback for other formats
                content = str(msg)[:150]
                context_parts.append(f"Message: {content}")
        
        return " | ".join(context_parts) if context_parts else "This is the beginning of our conversation." 