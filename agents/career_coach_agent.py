# Enhanced Career Coach Agent with better chat handling

import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
import json
import re

logger = logging.getLogger("career_coach_agent")

class CareerCoachAgent:
    """Production-grade, GPT-powered LinkedIn Career Coach Agent with enhanced chat capabilities."""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.2,
            openai_api_key=openai_api_key
        )

    def coach(self, profile: Dict[str, Any], job_description: str, session_id: str = None, 
              missing_skills: list = None, user_question: str = None, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Enhanced career coaching with better chat support and context awareness."""
        
        # If this is a chat interaction, handle it with better context
        if user_question:
            return self._handle_chat_interaction(profile, job_description, user_question, chat_history or [], session_id)
        
        # Standard coaching analysis
        return self._provide_standard_coaching(profile, job_description, missing_skills, session_id)

    def _handle_chat_interaction(self, profile: Dict[str, Any], job_description: str, 
                                user_question: str, chat_history: List[Dict], session_id: str) -> Dict[str, Any]:
        """Handle chat interactions with improved context and response formatting."""
        
        # Extract profile information
        about = profile.get("about", "Not provided")
        experience = profile.get("experience", [])
        skills = profile.get("skills", [])
        education = profile.get("education", [])
        name = profile.get("name", "User")
        
        # Build conversation context
        context = self._build_conversation_context(chat_history)
        
        # Enhanced system prompt for better responses
        system_prompt = """You are an expert LinkedIn Career Coach and Personal Branding specialist. You have deep expertise in:

- LinkedIn profile optimization and ATS compatibility
- Career development and transition strategies  
- Industry trends and job market analysis
- Skill gap identification and learning paths
- Professional networking and personal branding
- Interview preparation and job search tactics

Key Guidelines:
- Always reference the user's actual profile data when giving advice
- Provide specific, actionable recommendations with clear next steps
- Be encouraging but honest about areas needing improvement
- Suggest concrete resources (courses, certifications, tools) when relevant
- Use a conversational, supportive tone like a professional mentor
- If asked about profile sections, provide specific improvement examples
- For job fit questions, give detailed analysis with reasoning
- Remember context from previous messages in this conversation

Response Format:
- Use markdown formatting for better readability
- Include bullet points for actionable items
- Add relevant emojis to make responses more engaging
- Structure longer responses with clear headings"""

        # Build comprehensive user context
        user_prompt = f"""**User Profile Context:**
- Name: {name}
- About: {about}
- Experience: {self._format_experience(experience)}
- Skills: {', '.join(skills) if skills else 'Not specified'}
- Education: {self._format_education(education)}

**Target Job:** {job_description}

**Conversation History:** {context}

**Current Question:** {user_question}

Please provide a helpful, detailed response that directly addresses their question while leveraging their profile data and career context. Be specific and actionable."""

        try:
            response = self.llm.invoke([
                {"type": "system", "content": system_prompt},
                {"type": "human", "content": user_prompt}
            ])
            
            # Handle different response formats
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            elif hasattr(response, 'message'):
                content = response.message.content
            else:
                content = str(response)
            
            return {
                "message": content.strip(),
                "answer": content.strip(),  # Fallback for different field names
                "type": "chat_response",
                "session_id": session_id,
                "user_question": user_question,  # Include user question for tracking
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in chat interaction for session {session_id}: {str(e)}")
            return {
                "message": "I apologize, but I encountered a technical issue. Please try rephrasing your question or ask something else about your career development.",
                "answer": "I apologize, but I encountered a technical issue. Please try rephrasing your question or ask something else about your career development.",
                "error": str(e),
                "type": "error",
                "session_id": session_id,
                "success": False
            }

    def _provide_standard_coaching(self, profile: Dict[str, Any], job_description: str, 
                                  missing_skills: list, session_id: str) -> Dict[str, Any]:
        """Provide standard coaching analysis when not in chat mode."""
        
        about = profile.get("about", "")
        experience = profile.get("experience", [])
        skills = profile.get("skills", [])
        
        if missing_skills is None:
            # Analyze missing skills first
            missing_skills_prompt = f"""Analyze the following profile against this job description and identify missing or weak skills.

Profile:
- About: {about}
- Experience: {self._format_experience(experience)}
- Skills: {', '.join(skills)}

Job Description: {job_description}

Return a JSON object with key 'missing_skills' containing an array of missing skills."""

            try:
                response = self.llm.invoke([
                    {"type": "system", "content": "You are a skill gap analysis expert."},
                    {"type": "human", "content": missing_skills_prompt}
                ])
                
                # Handle different response formats
                if hasattr(response, 'content'):
                    result = response.content.strip()
                elif hasattr(response, 'text'):
                    result = response.text.strip()
                elif hasattr(response, 'message'):
                    result = response.message.content.strip()
                else:
                    result = str(response).strip()
                
                # Try to extract JSON from the response
                try:
                    # Look for JSON in the response
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        parsed_result = json.loads(json_str)
                        missing_skills = parsed_result.get("missing_skills", [])
                    else:
                        # If no JSON found, try to parse the whole response
                        parsed_result = json.loads(result)
                        missing_skills = parsed_result.get("missing_skills", [])
                except json.JSONDecodeError:
                    # If JSON parsing fails, extract skills from text
                    missing_skills = self._extract_skills_from_text(result)
            except Exception as e:
                logger.warning(f"Failed to analyze missing skills: {e}")
                missing_skills = []

        # Provide comprehensive coaching
        coaching_prompt = f"""As an expert career coach, provide comprehensive career guidance based on this profile and job target.

Profile:
- About: {about}
- Experience: {self._format_experience(experience)}
- Skills: {', '.join(skills)}

Target Job: {job_description}
Missing Skills: {missing_skills}

Provide detailed guidance in JSON format with these keys:
- advice: Array of career advice points
- growth_areas: Array of key areas for development
- next_steps: Array of specific actionable steps
- resources: Object mapping each missing skill to array of learning resources with name, provider, and url
- career_paths: Array of suggested career progression paths"""

        try:
            response = self.llm.invoke([
                {"type": "system", "content": "You are an expert career coach providing comprehensive guidance."},
                {"type": "human", "content": coaching_prompt}
            ])
            
            # Handle different response formats
            if hasattr(response, 'content'):
                result = response.content.strip()
            elif hasattr(response, 'text'):
                result = response.text.strip()
            elif hasattr(response, 'message'):
                result = response.message.content.strip()
            else:
                result = str(response).strip()
            
            try:
                # Try to extract JSON from the response
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    coaching_data = json.loads(json_str)
                else:
                    # If no JSON found, try to parse the whole response
                    coaching_data = json.loads(result)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a fallback response
                coaching_data = {
                    "advice": ["Focus on developing your core skills and gaining relevant experience"],
                    "growth_areas": ["Continue building your professional network and staying updated with industry trends"],
                    "next_steps": ["Update your profile regularly and seek feedback from mentors"],
                    "resources": {},
                    "career_paths": ["Consider exploring different roles within your field"]
                }
            
            coaching_data["session_id"] = session_id
            coaching_data["success"] = True
            return coaching_data
            
        except Exception as e:
            logger.error(f"Error in standard coaching for session {session_id}: {str(e)}")
            return {
                "error": f"Career coaching analysis failed: {str(e)}",
                "advice": ["Unable to provide detailed analysis due to technical issues"],
                "growth_areas": ["Please try again or contact support"],
                "next_steps": ["Retry the analysis"],
                "resources": {},
                "career_paths": [],
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
                    context_parts.append(f"Coach: {content}")
            else:
                # Fallback for other formats
                content = str(msg)[:150]
                context_parts.append(f"Message: {content}")
        
        return " | ".join(context_parts) if context_parts else "This is the beginning of our conversation."

    def _format_experience(self, experience: List[Dict]) -> str:
        """Format experience data for prompts."""
        if not experience:
            return "No experience data provided"
        
        formatted = []
        for exp in experience[:3]:  # Limit to recent 3 positions
            if isinstance(exp, dict):
                title = exp.get("title", "Unknown Position")
                company = exp.get("company", "Unknown Company")
                formatted.append(f"{title} at {company}")
            else:
                formatted.append(str(exp))
        
        return "; ".join(formatted)

    def _format_education(self, education: List[Dict]) -> str:
        """Format education data for prompts."""
        if not education:
            return "No education data provided"
        
        formatted = []
        for edu in education:
            if isinstance(edu, dict):
                degree = edu.get("degree", "")
                school = edu.get("school", "")
                if degree or school:
                    formatted.append(f"{degree} from {school}".strip())
            else:
                formatted.append(str(edu))
        
        return "; ".join(formatted[:2])  # Limit to 2 entries

    def _extract_skills_from_text(self, text: str) -> list:
        """Extract skills from text."""
        # Implement your logic to extract skills from text here
        # This is a placeholder and should be replaced with actual implementation
        return []