# PitchPerfect AI 🚀

[![Status](https://img.shields.io/badge/status-beta-blue)](https://github.com/your-username/pitchperfect)


PitchPerfect is a comprehensive business intelligence tool designed to automate lead generation research. Go from a simple company URL to a full-funnel analysis in minutes. The application uses a configurable deep-crawling engine and direct third-party data fetching to gather intelligence. It then leverages a multi-call AI architecture with Google's Gemini to generate a detailed report, including a **Growth & Stability Analysis**, a **SWOT Analysis**, a **Tech & Trends report**, and identification of **Key C-suite Personnel**.

This project is under active development.

---

### ✨ Core Features

PitchPerfect transforms raw data into actionable intelligence with a suite of powerful, AI-driven features presented in a clean, tabbed interface.

#### 1. Intelligent Data Gathering
-   **Configurable Deep Crawl:** Performs a breadth-first search of the target website. Crawl limits (`MAX_PAGES`, `MAX_DEPTH`) are fully configurable via the `.env` file to balance speed and thoroughness.
-   **Third-Party Data Aggregation:** Fetches data directly from public financial sources (like Crunchbase, Growjo, Owler, and Yahoo Finance) to build a profile of the company's financial health and growth trajectory.
-   **Smart Text Prioritization:** Intelligently identifies and prioritizes content from "About," "Team," "Leadership," and "Blog/News" pages to feed the most relevant data to the AI for each specific analysis.

#### 2. Multi-Faceted AI Analysis Suite
-   **Overview:** A quick, scannable summary and 10 key business bullet points.
-   **Growth Analysis:** A detailed report on the company's financial stability, including:
    -   Funding Summary
    -   Estimated Revenue
    -   A 1-10 Stability Rating with a visual progress bar.
    -   Insights on team growth, market position, and future outlook.
-   **Detailed Analysis:** An in-depth report on the company's business model, target audience, value proposition, and potential pain points.
-   **SWOT Analysis:** Automatically generated Strengths, Weaknesses, Opportunities, and Threats.
-   **Key Persons:** Identifies C-suite executives and other high-level management from the crawled text to pinpoint decision-makers.
-   **Tech & Trend Analysis:** Analyzes the company's blog and news content to identify:
    -   Strategic Focus & Keywords
    -   Key Market Trends they are focused on.
    -   Their public-facing Thought Leadership Position.

#### 3. Actionable Outputs & Modern UI
-   **On-Demand Pitch Generation:** Generate unlimited, personalized sales pitches based on the AI analysis and your own product description.
-   **Full Lead Management:** A clean dashboard to add, view, and delete leads.
-   **Real-time Status Updates:** The frontend automatically polls the backend while analysis is in progress, providing live status changes from `PENDING` to `COMPLETED` or `FAILED`.

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
    Edit the `.env` file to add your `SECRET_KEY`, `GOOGLE_API_KEY`, and optionally adjust the `CRAWLER_` and `AI_` settings.

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
    VITE_API_BASE_URL=http://127.0.0.1:8000
    ```

4.  **Run the Development Server (in a third terminal)**
    ```bash
    npm run dev
    ```

You can now access the application at `http://localhost:5173` (or whatever URL your terminal shows).

---

### 🗺️ Future Roadmap

-   [ ] **Competitive Landscape Analysis**: Analyze multiple competitors side-by-side.
-   [ ] **Pitch History & Templates**: Save all generated pitches and allow users to create their own templates.
-   [ ] **Email Integration**: Add a "Send Pitch" button to open a pre-filled `mailto:` link.
-   [ ] **Lead Tagging & Filtering**: Organize and filter the lead dashboard.
-   [ ] **Database Migrations**: Implement Alembic to manage schema changes without data loss.