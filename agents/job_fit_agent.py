import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
import json

logger = logging.getLogger("job_fit_agent")

class JobFitAgent:
    """Production-grade, GPT-powered Job Fit Analysis Agent."""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.2,
            openai_api_key=openai_api_key
        )

    def analyze(self, profile: Dict[str, Any], job_description: str, session_id: str = None, user_question: str = None, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Analyze job fit and return match score and recommendations."""
        about = profile.get("about", "")
        experience = profile.get("experience", [])
        skills = profile.get("skills", [])
        name = profile.get("name", "User")
        
        # If this is a chat interaction, provide a conversational response
        if user_question:
            return self._handle_chat_job_fit(profile, job_description, user_question, session_id, chat_history)
        
        # Standard job fit analysis
        prompt = f"""Analyze the fit between this profile and job description.

Profile:
- About: {about}
- Experience: {experience}
- Skills: {skills}

Job Description: {job_description}

Provide analysis in JSON format with:
- match_score: 0-100 score
- strengths: array of matching strengths
- gaps: array of skill/experience gaps
- recommendations: array of improvement suggestions"""

        try:
            response = self.llm.invoke([
                {"type": "system", "content": "You are a job fit analysis expert."},
                {"type": "human", "content": prompt}
            ])
            
            result = response.content.strip()
            try:
                analysis = json.loads(result)
            except Exception:
                analysis = {"raw": result}
            
            logger.info(f"Job fit analysis completed for session {session_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in job fit analysis for session {session_id}: {str(e)}")
            return {
                "error": f"Job fit analysis failed: {str(e)}",
                "match_score": 0,
                "strengths": [],
                "gaps": [],
                "recommendations": ["Unable to analyze job fit due to an error"]
            }

    def _handle_chat_job_fit(self, profile: Dict[str, Any], job_description: str, user_question: str, session_id: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Handle chat-based job fit analysis requests."""
        about = profile.get("about", "")
        experience = profile.get("experience", [])
        skills = profile.get("skills", [])
        name = profile.get("name", "User")
        
        # Build conversation context from chat history
        context = self._build_conversation_context(chat_history or [])
        
        system_prompt = """You are an expert job fit analyst. When users ask about their job fit, provide detailed analysis with specific insights about their match with the target role. 

Key Requirements:
- Always provide a match score (0-100) at the beginning
- Use clear markdown formatting with headers and bullet points
- Be specific about strengths and areas for improvement
- Include actionable recommendations
- Be encouraging but honest about gaps
- Consider the conversation history when providing analysis

Response Format:
1. Start with a clear match score and overall assessment
2. List specific strengths that match the role
3. Identify key gaps or areas for improvement
4. Provide actionable recommendations
5. End with a summary of fit potential"""

        user_prompt = f"""**User Profile:**
- Name: {name}
- About: {about}
- Experience: {experience}
- Skills: {skills}

**Target Job:** {job_description}

**Conversation History:** {context}

**User Question:** {user_question}

Please provide a detailed job fit analysis following the specified format. Include a clear match score and be specific about how well they match the role requirements."""

        try:
            response = self.llm.invoke([
                {"type": "system", "content": system_prompt},
                {"type": "human", "content": user_prompt}
            ])
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "message": content.strip(),
                "type": "job_fit_analysis",
                "session_id": session_id,
                "user_question": user_question,  # Include user question for tracking
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in chat job fit analysis for session {session_id}: {str(e)}")
            return {
                "message": "I apologize, but I encountered an issue analyzing your job fit. Please try rephrasing your question.",
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