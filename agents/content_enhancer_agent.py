import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
import json

logger = logging.getLogger("content_enhancer_agent")

class ContentEnhancerAgent:
    """Production-grade, GPT-powered LinkedIn Content Enhancement Agent."""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.2,
            openai_api_key=openai_api_key
        )

    def enhance(self, profile: Dict[str, Any], session_id: str = None, user_question: str = None, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Enhance LinkedIn profile content and return improved versions."""
        about = profile.get("about", "")
        experience = profile.get("experience", [])
        skills = profile.get("skills", [])
        name = profile.get("name", "User")
        
        # If this is a chat interaction, provide a conversational response
        if user_question:
            return self._handle_chat_enhancement(profile, user_question, session_id, chat_history)
        
        # Standard content enhancement
        prompt = f"""Enhance this LinkedIn profile content to be more compelling and ATS-friendly.

Profile:
- About: {about}
- Experience: {experience}
- Skills: {skills}

Provide enhanced versions in JSON format with:
- enhanced_about: improved about section
- enhanced_experience: improved experience descriptions
- enhanced_headline: suggested headline
- tips: array of improvement tips"""

        try:
            response = self.llm.invoke([
                {"type": "system", "content": "You are a LinkedIn content enhancement expert."},
                {"type": "human", "content": prompt}
            ])
            
            result = response.content.strip()
            try:
                enhanced = json.loads(result)
            except Exception:
                enhanced = {"raw": result}
            
            logger.info(f"Content enhancement completed for session {session_id}")
            return enhanced
            
        except Exception as e:
            logger.error(f"Error in content enhancement for session {session_id}: {str(e)}")
            return {
                "error": f"Content enhancement failed: {str(e)}",
                "enhanced_about": "",
                "enhanced_experience": [],
                "enhanced_headline": "",
                "tips": ["Unable to enhance content due to an error"]
            }

    def _handle_chat_enhancement(self, profile: Dict[str, Any], user_question: str, session_id: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Handle chat-based content enhancement requests."""
        about = profile.get("about", "")
        experience = profile.get("experience", [])
        skills = profile.get("skills", [])
        name = profile.get("name", "User")
        
        # Build conversation context from chat history
        context = self._build_conversation_context(chat_history or [])
        
        system_prompt = """You are an expert LinkedIn content enhancer specializing in profile optimization and ATS (Applicant Tracking System) compatibility.

Key Requirements:
- Provide specific, actionable content improvements
- Include relevant keywords for the target role
- Use clear markdown formatting with headers and bullet points
- Explain why each change improves the content
- Focus on ATS optimization and readability
- Be specific about the requested content section

Response Format:
1. **Current Content Analysis** - Brief assessment of existing content
2. **Enhanced Version** - Improved content with keywords
3. **Key Improvements** - Specific changes made and why
4. **ATS Optimization Tips** - Additional suggestions for better visibility
5. **Keywords Added** - List of relevant keywords incorporated

When rewriting about sections, focus on:
- Professional summary with key achievements
- Relevant keywords for the target role
- Clear value proposition
- Call-to-action elements
- Professional tone and readability"""

        user_prompt = f"""**User Profile:**
- Name: {name}
- About: {about}
- Experience: {experience}
- Skills: {skills}

**Conversation History:** {context}

**User Question:** {user_question}

Please provide specific content improvements that directly address their request. Focus on the about section rewrite with relevant keywords for their target role. Include enhanced versions and explain why the changes are better."""

        try:
            response = self.llm.invoke([
                {"type": "system", "content": system_prompt},
                {"type": "human", "content": user_prompt}
            ])
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "message": content.strip(),
                "type": "content_enhancement",
                "session_id": session_id,
                "user_question": user_question,  # Include user question for tracking
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in chat content enhancement for session {session_id}: {str(e)}")
            return {
                "message": "I apologize, but I encountered an issue enhancing your content. Please try rephrasing your question.",
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