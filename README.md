# 🤖 AI-Powered LinkedIn Career Coach

This project is a sophisticated, AI-powered career coaching chat system built with Python, Streamlit, and LangGraph. It provides personalized career advice by analyzing a user's LinkedIn profile against a target job description.

For a deep dive into the project's architecture, challenges, and solutions, please see the full **[Project Documentation](DOCUMENTATION.md)**.

## 🌟 Key Features

-   **Multi-Agent Architecture**: Uses specialized AI agents for tasks like intent classification, profile analysis, and job fit evaluation.
-   **Interactive Chat UI**: A user-friendly, real-time chat interface built with Streamlit.
-   **Dynamic Routing**: Employs LangGraph to manage the conversation and route user queries to the most appropriate AI agent.
-   **Efficient, One-Time Scraping**: Scrapes the user's public LinkedIn profile once per session for use as a persistent context.

---

## 🔧 Setup and Installation

### Prerequisites

-   Python 3.8+
-   An OpenAI API Key

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/manjuraavi/linkedin_career_coach.git
    cd linkedin_career_coach
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv env
    .\env\Scripts\activate

    # For macOS/Linux
    python3 -m venv env
    source env/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    -   Create a new file named `.env` in the root of the project directory.
    -   Add your API keys to the file:
        ```
        OPENAI_API_KEY="your-openai-api-key-here"
        APIFY_API_TOKEN="your-apify-api-token-here"
        ```

### How to Run the Application

With your virtual environment activated, run the following command in your terminal:

```bash
streamlit run app.py
```

The application will open in your default web browser.

---

## 📂 Project Structure

-   `app.py`: The main Streamlit application file.
-   `graph.py`: Defines the LangGraph multi-agent structure.
-   `routing.py`: Contains the core routing logic for the graph.
-   `DOCUMENTATION.md`: Contains detailed documentation about the project's architecture and development.
-   `agents/`: Contains all the specialized AI agents.
-   `scraper/`: Contains the simple LinkedIn scraping utility.
-   `requirements.txt`: Lists all Python dependencies.

---

## 💬 How to Use

1. **Enter your LinkedIn profile URL** (must be public) and target job description in the sidebar
2. **Click "Load Profile & Start Chat"** to initialize the system
3. **Start chatting** with your AI career coach about your profile, job fit, or career goals

---

## 📚 Documentation

For detailed information about:
- System architecture and design decisions
- Technical challenges and solutions
- Code structure and implementation details
- Development history and evolution

Please see **[DOCUMENTATION.md](DOCUMENTATION.md)**. 