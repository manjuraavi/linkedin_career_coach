from typing import Dict, Any, Literal
from langgraph.graph import END
import logging
logger = logging.getLogger("router")

def router(state: Dict[str, Any]) -> Literal[
    "intent_classifier_agent",
    "profile_analyzer_agent",
    "job_fit_agent",
    "content_enhancer_agent",
    "career_coach_agent"
] | type(END):
    """
    This is the central router function for the conversational graph.
    Its primary job is to decide which node (or agent) to execute next based
    on the current state of the application.

    Args:
        state (Dict[str, Any]): The current state of the graph.

    Returns:
        The string name of the next node to execute, or `END` to terminate the graph run.
    """
    logger.info(f"Routing state: {state}")

    # --- Termination Conditions ---
    # If the state contains an error or an explicit end command, we terminate the flow.
    if "error" in state or state.get("force_end"):
        return END

    # If an agent has just run and produced a response for the current user question,
    # the turn is considered complete, and the graph should finish its run.
    if state.get("command") == "chat":
        if (
            ("coaching" in state and state["coaching"] and state["coaching"].get("user_question") == state.get("user_question")) or
            ("analysis" in state and state["analysis"] and state["analysis"].get("user_question") == state.get("user_question")) or
            ("job_fit" in state and state["job_fit"] and state["job_fit"].get("user_question") == state.get("user_question")) or
            ("enhanced_content" in state and state["enhanced_content"] and state["enhanced_content"].get("user_question") == state.get("user_question"))
        ):
            return END
            
    # --- Intent-Based Routing ---
    # The graph's entry point is the intent classifier. After it runs, this router
    # uses its classification to direct the flow to the correct specialized agent.
    if "intent_classification" in state and state["intent_classification"]:
        intent = state["intent_classification"].get("intent")
        if intent:
            logger.info(f"Routing to {intent} based on intent classification")
            return intent

    # --- Fallback Route ---
    # If for any reason the intent is not classified correctly, we default to the
    # general-purpose career coach agent to handle the query.
    logger.warning("Intent not found or unclear, defaulting to career_coach_agent")
    return "career_coach_agent"