## README.md 

````md
### AI-First CRM — HCP Interaction Logger (LangGraph + Groq)
````
This project is an AI-first CRM workflow for logging HCP (Health Care Professional) interactions.
The UI is chat-driven: the rep types a conversational note, the agent extracts structured fields,
suggests follow-ups, runs compliance checks, and logs/edits interactions in the database.
````

### Key Requirement
````
- Left "Structured Interaction Form" is **read-only/locked**
- Rep does **not** manually fill form fields
- Rep does **not** provide interaction_id for edits (backend resolves automatically)
````

---

### Tech Stack
````
- Frontend: React + Redux + Vite
- Backend: FastAPI + SQLAlchemy + SQLite
- Agent: LangGraph + Groq LLM
````

---

### Features
### Chat → Draft Autofill
````
- Extracts HCP name, interaction details, sentiment, topics, materials, samples, follow-ups, etc.
- Populates the locked form automatically
````

### 5 Sales Tools (LangGraph Agent Tools)
````
1. **Log Interaction (required)**
   - Validates required data and writes an Interaction to DB
2. **Edit Interaction (required, no interaction_id in UI)**
   - User sends correction in chat (e.g., "Sorry sentiment is negative")
   - Backend edits the **latest interaction for that HCP**
3. **Retrieve HCP Context**
   - Returns HCP profile + recent interactions to support sales follow-ups
4. **Follow-up Suggestions**
   - Generates actionable next steps based on the draft/context
5. **Compliance Check**
   - Flags consent/risky claims and marks status `ok` or `review`
````

---

### Run Locally

````
### Backend (FastAPI)
1. Go to backend:
   ```bash
   cd backend
````

2. Create env + install deps:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```
3. Start server:

   ```bash
   uvicorn app.main:app --reload
   ```

Backend runs on:

* [http://localhost:8000](http://localhost:8000)
  Swagger:
* [http://localhost:8000/docs](http://localhost:8000/docs)

> Note: Set your Groq API key in environment (do not commit it).

### Frontend (React)

1. Go to frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Frontend runs on:

* [http://localhost:5173](http://localhost:5173)

---

## Demo Flow (How to Test)

### 1) Draft Autofill (Chat-only)

Paste into chat:

> Met Dr. Asha Sharma today at 16:30. Attendees: Dr. Asha, Nurse Anita. Topics: dosing and efficacy of CardioPlus. Shared CardioPlus Brochure. Gave CardioPlus 10 tabs. Sentiment positive. Follow-up: schedule revisit in 2 weeks.

Expected:

* Left form auto-fills
* AI Suggestions appear
* Compliance shows status

### 2) Log Interaction

Click **Log**
Expected:

* "Logged successfully" message

### 3) Edit Interaction (no ID)

Send in chat:

> Sorry, for Dr. Asha Sharma sentiment is negative and follow-up should be send updated brochure tomorrow.

Expected:

* Backend edits latest interaction for that HCP
* Form updates to reflect new values

### 4) Retrieve Context (Swagger)

GET:
`/agent/tools/hcp-context?hcp_name=Dr.%20Asha%20Sharma`
Expected:

* recent interactions list

---

## Project Notes

* Interaction IDs are managed internally in backend; UI remains conversational.
* SQLite DB file is not committed. HCP seeding is handled by backend.

````

---

### Push to GitHub (commands)
From the repo root:
```bash
git init
git add .
git commit -m "Initial commit: AI-first CRM HCP logger"
git branch -M main
git remote add origin <your_repo_url>
git push -u origin main
````

---

## One important warning

Before you push:

* remove any hardcoded API keys
* ensure `.env` is ignored
* don’t commit `*.db`

Author: Rashi Gupta (github@rxz33)