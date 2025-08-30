# PitchPerfect AI 🚀


![status](https://img.shields.io/badge/status-in_development-yellow)

⚠️ This project is under active development and is **not production-ready**.

PitchPerfect is an AI-powered web application designed to automate lead generation research. It crawls a target company's website, uses a Large Language Model (Google's Gemini) to generate a detailed business analysis, and helps you craft personalized sales pitches, transforming a manual, time-consuming process into an efficient, data-driven workflow.

## ✨ Core Features

-   **Automated Lead Analysis**: Simply provide a company name and URL to kick off the process.
-   **Asynchronous Web Crawling**: Uses Celery and Redis to perform web crawling in the background without blocking the user interface.
-   **AI-Powered Insights**: Generates a concise business summary and 10 key bullet points on the company's offerings.
-   **On-Demand Pitch Generation**: Create custom, personalized pitches based on the AI analysis and your own product description.
-   **Modern & Responsive UI**: A clean dashboard built with React, Tailwind CSS, and DaisyUI provides a seamless user experience.
-   **Real-time Status Updates**: The frontend automatically polls for updates, so you can see a lead's status change from `PENDING` to `COMPLETED`.

---

## 🛠️ Tech Stack

| Category              | Technology                                                              |
| --------------------- | ----------------------------------------------------------------------- |
| **Frontend**          | React, TypeScript, Vite, React Query, Tailwind CSS, DaisyUI, Axios      |
| **Backend**           | Python, FastAPI, SQLAlchemy, Pydantic                                   |
| **AI Model**          | Google Generative AI (Gemini API via `google-genai` SDK)                |
| **Database**          | PostgreSQL                                                              |
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
    Connect to `psql` and run the following commands:
    ```sql
    CREATE DATABASE pitchperfect;
    CREATE USER "user" WITH PASSWORD 'password';
    GRANT ALL PRIVILEGES ON DATABASE pitchperfect TO "user";
    \q
    ```

5.  **Configure Environment Variables**
    Create a `.env` file in the `backend` directory and populate it with your credentials. You can copy the example file to get started:
    ```bash
    cp .env.example .env
    ```
    Now, edit the `.env` file with your `SECRET_KEY` and `GOOGLE_API_KEY`.

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
    Create a `.env` file in the `frontend` directory. It only needs one variable:
    ```ini
    VITE_API_BASE_URL=http://127.0.0.1:8000
    ```

4.  **Run the Development Server (in a third terminal)**
    ```bash
    npm run dev
    ```

You can now access the application at `http://localhost:5173` (or whatever URL your terminal shows).



## Status
This project is still in its early stages. Expect breaking changes.