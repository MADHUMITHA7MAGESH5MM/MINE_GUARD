```markdown
# MINEGUARD 🛡️
### AI-Powered Safety Intelligence & SIF Risk Prediction System for Mining Operations
*Developed for the IBM Datathon*

---

## Overview
**MINEGUARD** is an enterprise-grade safety intelligence and predictive analytics platform engineered to identify, assess, and mitigate **Serious Injury or Fatality (SIF)** precursors in underground and surface mining operations. Aligned with Directorate General of Mines Safety (DGMS) guidelines, MINEGUARD ingests unstructured safety narratives—via text entry or voice dictation—and leverages a hybrid Natural Language Processing (NLP) and Machine Learning pipeline to evaluate hazard exposure, track barrier failures, and compute real-time risk scores.

---

## Key Features
- **AI Incident Analysis Engine**: Instant NLP extraction of mining hazards (e.g., *roof fall, methane accumulation, strata spalling*), barrier breakdowns, and automated DGMS guideline matching.
- **Dynamic SIF Risk Scoring**: Real-time evaluation yielding high, borderline, or low SIF potential verdicts with automated probability calculation.
- **Safety Command Center**: Live operational overview tracking rolling precursor trends, active alert streams, and regional field network risk mapping.
- **Site Digital Twin**: Spatial visualization tracking multi-zone risk distribution and safety density across operational coal and metal mines.
- **Fatality Simulator**: Interactive safety control toggles allowing safety officers to simulate the protective impact of engineering and administrative barriers in real-time.
- **Human-in-the-Loop Review**: Dedicated workflow for safety managers to confirm, audit, or override borderline AI predictions.

---

## Technology Stack
- **Backend**: Python, FastAPI, SQLAlchemy, SQLite, Pandas, PyPDF2
- **ML / NLP**: Scikit-learn, XGBoost, spaCy, MiniLM Sentence Transformers
- **Frontend**: React, TypeScript, Tailwind CSS, Recharts, Vite
- **Infrastructure**: WebSocket Real-Time Broadcasting

---

## Project Structure
```text
Sifora/
├── backend/
│   ├── main.py             # FastAPI application entry point & WebSockets
│   ├── model_service.py    # ML inference & NLP entity wrapper
│   ├── schemas.py          # Pydantic data validation schemas
│   └── routers/            # API endpoints (incidents, analytics, bulk upload)
├── frontend/
│   └── src/
│       ├── components/     # Reusable UI components (Sidebar, VoiceRecorder)
│       └── pages/          # Dashboard views (CommandCenter, AIAnalysis, DigitalTwin, etc.)
├── models/                 # Pre-trained ML weights & vectorizers (.pkl, .json)
├── src/                    # Core engine scripts & datasets
│   ├── database/           # SQLAlchemy database models and CRUD operations
│   ├── mining_incidents.csv# DGMS-aligned mining safety dataset
│   ├── build_mining_dataset.py # Pipeline script for processing mining data
│   ├── pipeline.py         # End-to-end NLP & prediction pipeline
│   └── train_model.py      # Model training scripts
├── safety_app.db           # SQLite local operational database
├── requirements.txt        # Python backend dependencies
└── README.md

```

---

## Getting Started & Local Development

### 1. Run the FastAPI Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

```

### 2. Run the React Frontend

```bash
cd frontend
npm install
npm run dev

```

Open your browser and navigate to `http://localhost:5173`.

```

```