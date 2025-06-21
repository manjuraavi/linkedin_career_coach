# Project Documentation: AI-Powered LinkedIn Career Coach

## 1. Project Approach & Architecture

This project was developed to create a sophisticated, AI-powered career coaching chat system. The core approach is centered around a **multi-agent architecture**, where different, specialized AI agents handle distinct tasks. This modular design makes the system more robust, maintainable, and effective.

### Core Technologies

-   **Backend**: Python
-   **AI Orchestration**: LangChain & LangGraph
-   **LLM**: OpenAI (specifically, GPT-3.5-Turbo for its balance of speed and capability)
-   **Web Framework**: Streamlit for creating a real-time, interactive user interface.

### Final System Architecture

The final architecture is a clean, two-stage process that separates the initial, one-time data loading from the ongoing, dynamic conversational loop.

**Stage 1: Profile Loading & Initialization (Once per Session)**

1.  **User Input**: The process begins when the user provides their public LinkedIn Profile URL and a target job description in the Streamlit sidebar.
2.  **Direct Scraping**: When the "Load Profile & Start Chat" button is clicked, a simple Python function (`fetch_linkedin_profile`) is called directly. This function scrapes the necessary data from the user's public LinkedIn profile.
3.  **Session State Management**: The scraped profile data is immediately saved into the Streamlit session state (`st.session_state`). This ensures the data persists throughout the user's session but is isolated from other sessions.
4.  **Graph Compilation**: With the data loaded, the conversational `LangGraph` is compiled. This graph contains all the conversational agents (like the Profile Analyzer, Job Fit Agent, etc.) but *not* the scraper. This compiled graph is also stored in the session state.

**Stage 2: The Conversational Loop (Repeated for each User Message)**

1.  **Intent Classification**: When the user sends a message, it enters the `LangGraph`. The graph's entry point is always the `IntentClassifierAgent`. This agent's sole purpose is to analyze the natural language of the user's question and determine which specialized agent is best suited to answer it.
2.  **Dynamic Routing**: The output of the intent classifier (e.g., `"job_fit_agent"`) is fed to a central `router` function. This router acts as a switchboard, directing the workflow to the appropriate agent node within the graph.
3.  **Specialized Agent Execution**: The chosen agent (e.g., `JobFitAgent`) then executes. It pulls the necessary context from the application state—such as the user's profile data, the target job description, and the recent chat history—and uses this to formulate a high-quality, relevant response.
4.  **UI Rendering**: The agent's response is passed back to the Streamlit UI. The application logic ensures that the chat view updates and automatically scrolls down to display the new message, providing a seamless user experience.

This refined architecture is highly efficient because the expensive data scraping operation is performed only once, and the powerful `LangGraph` is used exclusively for what it does best: managing a dynamic, stateful, multi-turn conversation.

---

## 2. Challenges & Solutions

The development process involved overcoming several key architectural and logical challenges.

### Challenge 1: Inefficient Graph & Repeated Scraping

-   **The Problem**: The initial design included the LinkedIn scraper as a node within the LangGraph. This was a significant design flaw because the entire graph was invoked on every conversational turn. As a result, the system was re-scraping the user's LinkedIn profile for every single question asked, which was slow, inefficient, and unnecessary.
-   **The Solution**: We implemented a clear separation of concerns.
    -   The scraper was completely removed from the graph. It is now a standalone Python function that is called *only once* at the beginning of the session.
    -   The scraped data is stored in Streamlit's session state, making it a persistent resource for the duration of the chat.
    -   The graph's responsibility was narrowed to only managing the conversation, which is its core strength. This change dramatically improved the application's performance and logical flow.

### Challenge 2: Incorrect Routing & Stale Responses

-   **The Problem**: The system was struggling with two related issues. First, it would sometimes display a response from a previous turn instead of answering the user's current question. Second, the intent classification was not precise enough. For example, it would confuse a request to analyze a user's fit for a *specific target job* with an exploratory question about *potential new career paths*.
-   **The Solution**: This required a two-pronged approach.
    1.  **Refined Intent Classification**: We made the `IntentClassifierAgent` much smarter by providing it with a more detailed and nuanced system prompt. We gave it clear definitions and contrasting examples to help it distinguish between the responsibilities of the `JobFitAgent` (for a single, target role) and the `CareerCoachAgent` (for broader, exploratory career guidance).
    2.  **Intelligent State Management**: We refactored the response-handling logic in `app.py`. The system now explicitly checks that the response it's about to display was generated for the *current* user question. It prioritizes the output from the agent that was chosen by the intent classifier for the active turn, which prevents stale data from being shown.

### Challenge 3: A Clunky and Unintuitive User Interface

-   **The Problem**: The user experience was not smooth. When a user sent a message, the chat window would not scroll down automatically. This meant the user often missed the "Thinking..." indicator and had to manually scroll to find the new response, which made the application feel broken and static.
-   **The Solution**: We restructured the UI rendering logic in `app.py` by leveraging Streamlit's `st.rerun()` command. This created a clean, predictable, multi-step rendering cycle. Now, when a message is sent, the app immediately re-renders to show the user's message, then re-renders again to show the "Thinking..." spinner, and finally re-renders to display the AI's response. This approach ensures the UI is always in a correct state and naturally keeps the latest message in view.

--- 