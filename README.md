# LinkedIn Career Coach (AI-Powered Chat Assistant)

A multi-agent, interactive AI assistant to optimize LinkedIn profiles, analyze job fit, and guide career decisions through natural chat. Built with **Streamlit**, **LangGraph**, and **OpenAI**, this app uses real LinkedIn profile data (via Apify) to deliver personalized insights and suggestions.

---

## 🌐 Live App

[🔗 Visit the app](https://linkedincareercoach.streamlit.app/)

---

## 📌 Features

### ✅ Chat-Based Career Assistant

* Fully interactive chat UI powered by `st.chat_message` and `st.chat_input`
* Remembers session state (chat history, profile, job goals)
* Intelligent conversation flow using LangGraph

### ✅ LinkedIn Profile Scraper

* Enter a public LinkedIn profile URL
* Automatically fetches Name, Headline, About, Experience, Skills
* Uses Apify API (free credits included)

### ✅ AI-Driven Insights

* **Profile Analyzer Agent**: Highlights strengths, flags weak sections
* **Job Fit Agent**: Matches your profile against target job roles and computes a fit score
* **Content Enhancer Agent**: Rewrites About/Experience to better match role
* **Career Coach Agent**: Provides skill gap analysis, suggestions, and growth tips

### ✅ Intent-Based Routing (LangGraph)

* Uses `IntentClassifierAgent` to decide next step
* Dynamic node transitions handled via `router()` logic

---

## 🧠 Memory Handling

* Session-level memory with `st.session_state` (for local state retention)
* **Persistent memory checkpointer planned** using `langgraph.checkpoint.memory.MemorySaver` with `session_id` as key

---

## 📐 Architecture Overview

```
          +--------------------------+
          | LinkedIn Profile Scraper |
          +-----------+--------------+
                      |
                      v
           +----------+-----------+
           | Intent Classifier    |
           +----------+-----------+
                      |
        +-------------+--------------+
        |      Router (Dynamic)       |
        +------+----------+----------+
               |          |          |
     +---------+   +------+--+  +----+-----+
     | Profile  |   | Job Fit |  | Enhancer |
     | Analyzer |   | Agent   |  | Agent    |
     +----------+   +---------+  +----------+

```

---

## 🚀 How to Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/manjuraavi/linkedin_career_coach
cd linkedin_career_coach
```

### 2. Set Up Environment

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Add API Keys

Create `.env` file:

```
OPENAI_API_KEY=sk-...
APIFY_API_KEY=apify_api_...
```

Or use `.streamlit/secrets.toml` if deploying:

```toml
OPENAI_API_KEY = "sk-..."
APIFY_API_KEY = "apify_api_..."
```

### 4. Run the App

```bash
streamlit run app.py
```

---

## 📁 File Structure

```
├── app.py                    # Streamlit entry point
├── graph_utils.py           # LangGraph orchestration
├── agents/                  # All agent classes
├── scraper/                 # LinkedIn scraper
├── routing.py               # Router function
├── state.py                 # LangGraph state
├── requirements.txt         # Dependencies
├── .env / secrets.toml      # API Keys
└── README.md
```

---

## 📄 Documentation

### Agents:

* `ProfileAnalyzerAgent`: Analyzes key sections and reports gaps
* `JobFitAgent`: Compares resume with target job (via Jaccard or semantic match)
* `ContentEnhancerAgent`: Suggests improved headlines, about section, etc.
* `CareerCoachAgent`: Offers guidance, role change suggestions, skill development
* `IntentClassifierAgent`: Determines which agent to invoke using prompts

### LangGraph Design:

* State is a dictionary-like model tracking `session_id`, `user_question`, `profile`, `chat_history`
* Each LangGraph node is an async/def function returning a partial state
* Routing logic drives edge decisions after each node

---

## ✅ To-Do / Planned Improvements

* [ ] Enable persistent memory using `MemorySaver()`
* [ ] Add fit score visualizations (e.g., donut chart)
* [ ] Improve fallback handling for edge-case prompts
* [ ] Add resume download option (PDF generation)
* [ ] Add automated tests

---

## 🤝 Credits

* Built by [Manjusha Raavi](https://github.com/manjuraavi)
* Powered by: [LangGraph](https://github.com/langchain-ai/langgraph), [Streamlit](https://streamlit.io/), [OpenAI](https://platform.openai.com/), [Apify](https://apify.com/)

---

## 📬 Contact

For questions, issues or collaborations, please open an issue or message [@manjuraavi](https://github.com/manjuraavi).
