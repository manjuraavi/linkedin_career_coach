import streamlit as st
import os
from dotenv import load_dotenv
from state import State
from graph import build_graph
from scraper.linkedin_scraper import fetch_linkedin_profile
import logging
import json
import uuid

# --- Basic Setup ---
load_dotenv()
st.set_page_config(page_title="LinkedIn Career Coach", layout="wide")

# --- Logging Configuration ---
# Helps in debugging by writing logs to a file.
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("app")

# --- Helper Functions ---
def normalize_chat_history(history):
    """
    Ensures that all messages in the chat history, regardless of their source
    (LangChain message objects or simple dicts), are converted to a consistent 
    dictionary format for reliable display in the UI.
    """
    normalized = []
    for msg in history:
        if isinstance(msg, dict):
            normalized.append(msg)
        elif hasattr(msg, 'content'):
            role = "user" if hasattr(msg, 'type') and msg.type == 'human' else "assistant"
            normalized.append({"role": role, "content": msg.content})
        else:
            normalized.append({"role": "assistant", "content": str(msg)})
    return normalized

# --- Main App UI ---
st.title("🤖 LinkedIn Career Coach (AI-powered Chat)")

# --- Session State Initialization ---
# Streamlit's session state is used to persist data across user interactions/reruns.
# We initialize all necessary keys here to prevent errors.
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "profile_loaded" not in st.session_state:
    st.session_state["profile_loaded"] = False
if "graph" not in st.session_state:
    st.session_state["graph"] = None
if "processing_prompt" not in st.session_state:
    # This key is crucial for the two-step chat processing logic.
    # It holds the user's message while the AI is "thinking".
    st.session_state.processing_prompt = None

# Memory keys to persist between turns
memory_keys = ["profile", "analysis", "job_fit", "enhanced_content", "coaching"]

# Sidebar for initial setup
with st.sidebar:
    st.header("📋 Profile Setup")
    
    profile_url = st.text_input(
        "LinkedIn Profile URL", 
        value=st.session_state.get("profile_url", ""),
        placeholder="https://www.linkedin.com/in/your-profile"
    )
    
    job_desc = st.text_input(
        "Target Job Title / Description", 
        value=st.session_state.get("job_desc", ""),
        placeholder="e.g., Senior Software Engineer at Google"
    )
    
    # This button triggers the one-time data loading process.
    if st.button("🚀 Load Profile & Start Chat", type="primary"):
        if profile_url and job_desc:
            st.session_state["profile_url"] = profile_url
            st.session_state["job_desc"] = job_desc
            
            with st.spinner("Scraping your LinkedIn profile... This may take a moment."):
                try:
                    # STAGE 1, STEP 1: Scrape profile data OUTSIDE the graph.
                    profile_data = fetch_linkedin_profile(profile_url)
                    if not profile_data or not profile_data.get("name"):
                         st.error("❌ Could not scrape the profile. Please check the URL and ensure the profile is public.")
                         st.stop()
                    
                    # STAGE 1, STEP 2: Store the loaded data in the session.
                    st.session_state["profile"] = profile_data
                    st.session_state["profile_loaded"] = True
                    
                    # STAGE 1, STEP 3: Build the conversational graph for the session.
                    st.session_state["graph"] = build_graph()
                    
                    # STAGE 1, STEP 4: Add a personalized welcome message to the chat.
                    welcome_msg = f"""👋 **Welcome, {profile_data.get('name', 'User')}!**

I've successfully loaded your LinkedIn profile. I'm ready to help you optimize your career path for the **{job_desc}** role.

Ask me anything about your profile, job fit, or career!"""

                    st.session_state["chat_history"].append({
                        "role": "assistant",
                        "content": welcome_msg
                    })
                    
                    st.success("✅ Profile loaded successfully! Start chatting below.")
                    # Rerun to immediately reflect the new state (e.g., show the main chat interface).
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ An error occurred while loading the profile: {str(e)}")
                    logger.error(f"Profile loading error: {e}")
        else:
            st.warning("⚠️ Please enter both LinkedIn URL and job description.")

# Main chat interface
if st.session_state.get("profile_loaded"):
    st.subheader("💬 Chat with Your AI Career Coach")
    
    # Display chat history
    for message in normalize_chat_history(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # STAGE 2, STEP 1: Handle user input.
    # The `st.chat_input` widget returns the user's message or None.
    if prompt := st.chat_input("Ask me anything about your career, profile, or job search..."):
        # Add the new user message to the history.
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        # Set the prompt as the one to be processed in the next rerun.
        st.session_state.processing_prompt = prompt
        # Rerun the script to immediately display the user's new message.
        st.rerun()

    # STAGE 2, STEP 2: Process the prompt if one is waiting.
    # This block executes after the rerun triggered by the user input.
    if st.session_state.processing_prompt:
        prompt_to_process = st.session_state.processing_prompt
        # Display the "Thinking..." spinner while the graph is invoked.
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    if st.session_state["graph"] is None:
                        st.session_state["graph"] = build_graph()
                    
                    # Prepare the state to be sent to the graph.
                    # This includes the session-specific data and the current turn's data.
                    chat_state = {
                        "command": "chat",
                        "user_question": prompt_to_process,
                        "session_id": st.session_state["session_id"],
                        "chat_history": normalize_chat_history(st.session_state["chat_history"]),
                        "job_description": st.session_state.get("job_desc", ""),
                        "profile": st.session_state.get("profile", {})
                    }
                                        
                    logger.info(f"Chat state prepared for session {st.session_state['session_id']}: {json.dumps(chat_state, default=str)[:500]}")
                    
                    # Invoke the conversational graph.
                    config = {"configurable": {"thread_id": st.session_state["session_id"]}}
                    result = st.session_state["graph"].invoke(chat_state, config=config)
                    
                    # STAGE 2, STEP 3: Extract the response.
                    if "error" in result:
                        response = f"❌ I encountered an error: {result['error']}"
                    else:
                        # This logic intelligently extracts the response from the correct agent's output,
                        # based on the intent classification from the current turn.
                        response = None
                        intent = result.get("intent_classification", {}).get("intent")
                        agent_output_map = {
                            "profile_analyzer_agent": "analysis", "job_fit_agent": "job_fit",
                            "content_enhancer_agent": "enhanced_content", "career_coach_agent": "coaching"
                        }
                        output_key = agent_output_map.get(intent)

                        if output_key and output_key in result:
                            agent_output = result.get(output_key, {})
                            # Ensure the response is for the *current* question to avoid showing stale data.
                            if agent_output.get("user_question") == prompt_to_process:
                                response = agent_output.get("message") or agent_output.get("answer")
                        
                        # Fallback in case the primary extraction fails.
                        if not response: 
                            response = (
                                result.get("coaching", {}).get("message") or result.get("coaching", {}).get("answer") or
                                result.get("analysis", {}).get("message") or result.get("job_fit", {}).get("message") or
                                result.get("enhanced_content", {}).get("message") or
                                "I understand. Let me provide some insights."
                            )
                            
                    # Add the final AI response to the chat history.
                    st.session_state["chat_history"].append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
                    st.session_state["chat_history"].append({"role": "assistant", "content": error_msg})
                    logger.error(f"Chat error for session {st.session_state['session_id']}: {e}")
                finally:
                    # STAGE 2, STEP 4: Clear the processed prompt and rerun.
                    # This final rerun displays the AI's response in the UI.
                    st.session_state.processing_prompt = None
                    st.rerun()
else:
    # Initial setup screen
    st.markdown("""
    ## 🎯 Welcome to LinkedIn Career Coach
    
    This AI-powered chat system will help you:
    
    - 📊 **Analyze your LinkedIn profile** for strengths and areas of improvement
    - 🎯 **Evaluate job fit** for your target positions
    - ✨ **Enhance your profile content** with AI-powered suggestions
    - 🚀 **Get personalized career guidance** and skill gap analysis
    - 💬 **Chat naturally** about your career goals and questions
    
    **To get started:**
    1. Enter your LinkedIn profile URL in the sidebar
    2. Specify your target job title or description
    3. Click "Load Profile & Start Chat"
    4. Begin your conversation with your AI career coach!
    
    ---
    
    **💡 Pro Tips:**
    - Make sure your LinkedIn profile is public or accessible
    - Be specific about your target job role for better analysis
    - Ask follow-up questions to dive deeper into any topic
    - The system remembers your context throughout the conversation
    """)
    
    # Example conversation preview
    with st.expander("💬 See what you can ask me"):
        st.markdown("""
        **Profile Analysis:**
        - "What are the strongest parts of my profile?"
        - "Which sections need the most improvement?"
        - "How does my experience section look?"
        
        **Job Fit Analysis:**
        - "How well do I match the job requirements?"
        - "What's my fit score for this role?"
        - "What skills am I missing for this position?"
        
        **Content Enhancement:**
        - "Can you rewrite my about section?"
        - "Improve my headline for this job"
        - "Make my experience descriptions more impactful"
        
        **Career Guidance:**
        - "What career path should I consider?"
        - "What skills should I develop next?"
        - "How can I transition to this field?"
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    Powered by LangGraph & OpenAI | Your AI Career Coach 🤖
</div>
""", unsafe_allow_html=True)