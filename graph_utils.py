import logging
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from state import State, memory_saver
from agents.profile_analyzer_agent import ProfileAnalyzerAgent
from agents.job_fit_agent import JobFitAgent
from agents.content_enhancer_agent import ContentEnhancerAgent
from agents.career_coach_agent import CareerCoachAgent
from agents.intent_classifier_agent import IntentClassifierAgent
from routing import router
import os
from dotenv import load_dotenv
import streamlit as st

# --- Basic Setup ---
logger = logging.getLogger("graph")
load_dotenv()

# --- Agent Initialization ---
# We'll initialize agents inside the build_graph function to avoid st.secrets issues during import
profile_agent = None
job_fit_agent = None
content_enhancer_agent = None
career_coach_agent = None
intent_classifier_agent = None


def _initialize_agents():
    """Initialize agents with proper API key handling."""
    global profile_agent, job_fit_agent, content_enhancer_agent, career_coach_agent, intent_classifier_agent
    
    # Try Streamlit secrets first (deployment)
    OPENAI_API_KEY = None
    try:
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    except (KeyError, AttributeError, Exception):
        # Fall back to environment variable (local development)
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in secrets or environment variables")

    profile_agent = ProfileAnalyzerAgent(OPENAI_API_KEY)
    job_fit_agent = JobFitAgent(OPENAI_API_KEY)
    content_enhancer_agent = ContentEnhancerAgent(OPENAI_API_KEY)
    career_coach_agent = CareerCoachAgent(OPENAI_API_KEY)
    intent_classifier_agent = IntentClassifierAgent(OPENAI_API_KEY)


# --- Agent Node Definitions ---
# Each of these functions defines a "node" in our graph. A node is a unit of work.
# It takes the current state, performs an action, and returns a dictionary of
# results to be merged back into the state.

def profile_analyzer_node(state: State) -> State:
    """Invokes the Profile Analyzer agent and returns its analysis."""
    global profile_agent
    if profile_agent is None:
        _initialize_agents()
        
    profile = state.get("profile", {})
    session_id = state.get("session_id", "")
    user_question = state.get("user_question", "")
    chat_history = state.get("chat_history", [])
    try:
        result = profile_agent.analyze(profile, session_id, user_question, chat_history)
        return {"analysis": result}
    except Exception as e:
        logger.error(f"Profile analyzer error for session {session_id}: {e}")
        return {"error": str(e)}


def job_fit_node(state: State) -> State:
    """Invokes the Job Fit agent and returns its analysis."""
    global job_fit_agent
    if job_fit_agent is None:
        _initialize_agents()
        
    profile = state.get("profile", {})
    job_desc = state.get("job_description", "")
    session_id = state.get("session_id", "")
    user_question = state.get("user_question", "")
    chat_history = state.get("chat_history", [])
    try:
        result = job_fit_agent.analyze(profile, job_desc, session_id, user_question, chat_history)
        return {"job_fit": result}
    except Exception as e:
        logger.error(f"Job fit error for session {session_id}: {e}")
        return {"error": str(e)}


def content_enhancer_node(state: State) -> State:
    """Invokes the Content Enhancer agent and returns its suggestions."""
    global content_enhancer_agent
    if content_enhancer_agent is None:
        _initialize_agents()
        
    profile = state.get("profile", {})
    session_id = state.get("session_id", "")
    user_question = state.get("user_question", "")
    chat_history = state.get("chat_history", [])
    try:
        result = content_enhancer_agent.enhance(profile, session_id, user_question, chat_history)
        return {"enhanced_content": result}
    except Exception as e:
        logger.error(f"Content enhancer error for session {session_id}: {e}")
        return {"error": str(e)}


def career_coach_node(state: State) -> State:
    """Invokes the Career Coach agent and returns its advice."""
    global career_coach_agent
    if career_coach_agent is None:
        _initialize_agents()
        
    profile = state.get("profile", {})
    job_desc = state.get("job_description", "")
    session_id = state.get("session_id", "")
    user_question = state.get("user_question", "")
    chat_history = state.get("chat_history", [])
    try:
        result = career_coach_agent.coach(
            profile=profile,
            job_description=job_desc,
            session_id=session_id,
            user_question=user_question,
            chat_history=chat_history
        )
        return {"coaching": result}
    except Exception as e:
        logger.error(f"Career coach error for session {session_id}: {e}")
        return {"error": str(e)}


def intent_classifier_node(state: State) -> State:
    """
    Invokes the Intent Classifier agent to determine which agent should handle
    the user's request. This is the entry point of our conversational graph.
    """
    global intent_classifier_agent
    if intent_classifier_agent is None:
        _initialize_agents()
        
    user_question = state.get("user_question", "")
    session_id = state.get("session_id", "")
    try:
        result = intent_classifier_agent.classify_intent(user_question, session_id)
        logger.info(f"Intent classified for session {session_id}: {result.get('intent')}")
        return {"intent_classification": result}
    except Exception as e:
        logger.error(f"Intent classifier error for session {session_id}: {e}")
        return {"error": str(e)}


# --- Graph Construction ---
def build_graph():
    """
    Builds the conversational multi-agent graph using LangGraph.
    This graph is now purely for orchestrating the conversation flow.
    """
    graph = StateGraph(State)

    # Add each agent function as a node in the graph.
    graph.add_node("intent_classifier_agent", intent_classifier_node)
    graph.add_node("profile_analyzer_agent", profile_analyzer_node)
    graph.add_node("job_fit_agent", job_fit_node)
    graph.add_node("content_enhancer_agent", content_enhancer_node)
    graph.add_node("career_coach_agent", career_coach_node)

    # The entry point for any new conversational turn is the intent classifier.
    graph.set_entry_point("intent_classifier_agent")

    # Add conditional edges. After each node runs, the `router` function
    # will be called to determine the next step in the graph based on the
    # current state. This creates a dynamic, non-linear flow.
    graph.add_conditional_edges("intent_classifier_agent", router)
    graph.add_conditional_edges("profile_analyzer_agent", router)
    graph.add_conditional_edges("job_fit_agent", router)
    graph.add_conditional_edges("content_enhancer_agent", router)
    graph.add_conditional_edges("career_coach_agent", router)

    # Compile the graph, including a memory saver to persist state.
    return graph.compile() 
