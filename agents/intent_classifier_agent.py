import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
import json
import re

logger = logging.getLogger("intent_classifier_agent")

class IntentClassifierAgent:
    """Production-grade, GPT-powered Intent Classification Agent."""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,  # Lower temperature for more consistent classification
            openai_api_key=openai_api_key
        )

    def classify_intent(self, user_question: str, session_id: str = None) -> Dict[str, Any]:
        """Classify the user's intent and return the appropriate agent to handle it."""
        
        system_prompt = """You are an expert intent classifier for a LinkedIn Career Coach system. 

Your job is to analyze user questions and classify them into one of these categories:

1.  **profile_analyzer_agent** - Questions about analyzing profile strengths, weaknesses, or general profile assessment.
    -   Examples: "What are my profile's biggest strengths?", "Analyze my profile", "What are my weaknesses?"

2.  **job_fit_agent** - Questions about how well a user's profile matches a *specific, pre-defined target job*. This is for direct comparison against one role.
    -   Examples: "How well do I match the job requirements?", "What's my fit score for this role?", "Do I qualify for the job I entered?"

3.  **content_enhancer_agent** - Questions about rewriting, improving, or enhancing specific parts of a user's profile content.
    -   Examples: "Can you rewrite my about section?", "Improve my headline", "Make my experience descriptions better"

4.  **career_coach_agent** - Broad, exploratory questions about career paths, potential roles, skill development, and general career advice. This is for when the user is asking "what could I do?" or "how can I get better?".
    -   Examples: "What skills should I develop?", "What other roles can I aim for?", "Suggest some career paths for me.", "Give me career advice."

Respond with ONLY a JSON object containing:
{
    "intent": "agent_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this agent was chosen"
}

Be precise. If the user is asking about their fit for the *target job*, use `job_fit_agent`. If they are asking about *other potential roles* or general guidance, use `career_coach_agent`."""

        user_prompt = f"""Classify this user question: "{user_question}"

Return only the JSON response."""

        try:
            response = self.llm.invoke([
                {"type": "system", "content": system_prompt},
                {"type": "human", "content": user_prompt}
            ])
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse JSON from the response
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)
                else:
                    # If no JSON found, try to parse the whole response
                    result = json.loads(content)
                
                # Validate the intent
                valid_intents = [
                    "profile_analyzer_agent", 
                    "job_fit_agent", 
                    "content_enhancer_agent", 
                    "career_coach_agent"
                ]
                
                if result.get("intent") not in valid_intents:
                    logger.warning(f"Invalid intent '{result.get('intent')}' for session {session_id}, defaulting to career_coach_agent")
                    result["intent"] = "career_coach_agent"
                    result["confidence"] = 0.5
                    result["reasoning"] = "Defaulted to career coach due to unclear intent"
                
                logger.info(f"Intent classified for session {session_id}: {result['intent']} (confidence: {result.get('confidence', 0)})")
                
                return {
                    "intent": result["intent"],
                    "confidence": result.get("confidence", 0.8),
                    "reasoning": result.get("reasoning", "Classified based on question content"),
                    "session_id": session_id,
                    "success": True
                }
                
            except json.JSONDecodeError:
                # Fallback classification based on keywords
                logger.warning(f"JSON parsing failed for session {session_id}, using keyword fallback")
                return self._fallback_classification(user_question, session_id)
            
        except Exception as e:
            logger.error(f"Error in intent classification for session {session_id}: {str(e)}")
            return self._fallback_classification(user_question, session_id)

    def _fallback_classification(self, user_question: str, session_id: str) -> Dict[str, Any]:
        """Fallback classification using keyword matching when LLM fails."""
        question = user_question.lower()
        
        # Profile analysis keywords
        if any(word in question for word in ["analyze", "strengths", "weaknesses", "profile analysis", "what are my"]):
            return {
                "intent": "profile_analyzer_agent",
                "confidence": 0.7,
                "reasoning": "Fallback: Contains profile analysis keywords",
                "session_id": session_id,
                "success": True
            }
        
        # Job fit keywords
        if any(word in question for word in ["job fit", "match", "requirements", "score", "how well", "fit for", "qualify"]):
            return {
                "intent": "job_fit_agent",
                "confidence": 0.7,
                "reasoning": "Fallback: Contains job fit keywords",
                "session_id": session_id,
                "success": True
            }
        
        # Content enhancement keywords
        if any(word in question for word in ["rewrite", "enhance", "improve", "about section", "headline", "experience", "make my", "better"]):
            return {
                "intent": "content_enhancer_agent",
                "confidence": 0.7,
                "reasoning": "Fallback: Contains content enhancement keywords",
                "session_id": session_id,
                "success": True
            }
        
        # Default to career coach
        return {
            "intent": "career_coach_agent",
            "confidence": 0.5,
            "reasoning": "Fallback: Defaulted to career coach",
            "session_id": session_id,
            "success": True
        } 