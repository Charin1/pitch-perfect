# PitchPerfect AI 🚀

[![Status](https://img.shields.io/badge/status-in_development-yellow)](https://github.com/your-username/pitchperfect)

PitchPerfect is a comprehensive business intelligence tool designed to automate lead generation research. Go from a simple company URL to a full-funnel analysis in minutes. The application uses a configurable deep-crawling engine to gather website data and leverages Google's Gemini AI to generate a multi-faceted report, including a SWOT analysis, a detailed business model breakdown, and identification of key C-suite personnel.

This project is under active development.

---

### ✨ Core Features

PitchPerfect transforms raw website data into actionable intelligence with a suite of powerful features:

-   **Configurable Deep Crawl:**
    -   Performs a breadth-first search of the target website to gather comprehensive data.
    -   Crawl limits (`MAX_PAGES`, `MAX_DEPTH`) are fully configurable via the `.env` file to balance speed and thoroughness.
    -   Intelligently prioritizes content from pages with keywords like "about," "team," and "leadership" to feed the most relevant data to the AI.

-   **Comprehensive AI Analysis:**
    -   The lead detail page features a clean, tabbed interface to organize the generated insights:
        -   **Overview:** A quick, scannable summary and 10 key business bullet points.
        -   **Detailed Analysis:** An in-depth report on the company's business model, target audience, value proposition, and potential pain points.
        -   **SWOT Analysis:** Automatically generated Strengths, Weaknesses, Opportunities, and Threats.
        -   **Key Persons:** Identifies C-suite executives and other high-level management from the crawled text to pinpoint decision-makers.

-   **Modern UI & UX:**
    -   A clean, professional dashboard built with React, TypeScript, and Tailwind CSS.
    -   Real-time status updates on the lead detail page, which automatically polls the backend while analysis is in progress.
    -   Full lead management, including creating new leads and deleting old ones.

-   **On-Demand Pitch Generation:**
    -   Generate unlimited, personalized sales pitches based on the AI analysis and your own product description.

---

### 🛠️ Tech Stack

| Category                | Technology                                                              |
| ----------------------- | ----------------------------------------------------------------------- |
| **Frontend**            | React, TypeScript, Vite, React Query, Tailwind CSS, DaisyUI, Axios      |
| **Backend**             | Python, FastAPI, SQLAlchemy, Pydantic                                   |
| **AI Model**            | Google Generative AI (Gemini API via `google-genai` SDK)                |
| **Database**            | PostgreSQL                                                              |
| **Task Queue & Broker** | Celery & Redis                                                          |

---

## 🏁 Getting Started

Follow these instructions to get a local copy up and running.

### Prerequisites

You must have the following software installed on your machine:
-   [Node.js](https://nodejs.org/) (v18+)
-   [Python](https://www.python.org/) (v3.10+)
-   [PostgreSQL](https://www.postgresql.org/download/)
-   [Redis](https://redis.io/docs/getting-started/installation/)

### ⚙️ Backend Setup

1.  **Navigate to the Backend Directory**
    ```bash
    cd backend
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up PostgreSQL Database**
    Connect to `psql` and run the following commands. **Note:** If you are updating the application, you may need to drop the old database first (`DROP DATABASE pitchperfect;`) to apply new schema changes.
    ```sql
    CREATE DATABASE pitchperfect;
    CREATE USER "user" WITH PASSWORD 'password';
    GRANT ALL PRIVILEGES ON DATABASE pitchperfect TO "user";
    \q
    ```

5.  **Configure Environment Variables**
    Copy the example `.env` file and fill in your details:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file to add your `SECRET_KEY`, `GOOGLE_API_KEY`, and optionally adjust the `CRAWLER_` settings.

6.  **Run the Servers (in two separate terminals)**
    -   **Terminal 1: Start the Celery Worker**
        ```bash
        # Make sure your venv is active
        celery -A app.workers.tasks.celery worker --loglevel=info
        ```
    -   **Terminal 2: Start the FastAPI Server**
        ```bash
        # Make sure your venv is active
        uvicorn app.main:app --reload
        ```

### 🎨 Frontend Setup

1.  **Navigate to the Frontend Directory**
    ```bash
    cd frontend
    ```

2.  **Install Dependencies**
    ```bash
    npm install
    ```

3.  **Configure Environment Variables**
    Create a `.env` file in the `frontend` directory with the following content:
    ```ini
    VITE_API_BASE_URL=http://120.0.0.1:8000
    ```

4.  **Run the Development Server (in a third terminal)**
    ```bash
    npm run dev
    ```

You can now access the application at `http://localhost:5173` (or whatever URL your terminal shows).

---

### 🗺️ Future Roadmap

-   [ ] **Pitch History & Templates**: Save all generated pitches and allow users to create their own templates.
-   [ ] **Email Integration**: Add a "Send Pitch" button to open a pre-filled `mailto:` link.
-   [ ] **Lead Tagging & Filtering**: Organize and filter the lead dashboard.
-   [ ] **Database Migrations**: Implement Alembic to manage schema changes without data loss.