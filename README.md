# 🌱 GreenOps-as-a-Service

A sustainability optimisation tool that analyses Python code for efficiency and estimates environmental impact.

## Features
- AI-powered code optimisation (Gemini API)
- AST fallback for reliability
- Green score and efficiency metrics
- Estimated vCPU hours saved and CO₂ reduction
- Research Library for anonymised audit results

## Tech Stack
- Backend: Flask
- Frontend: Streamlit
- AI: Gemini API
- Analysis: Python AST

## How to Run

### 1. Set API Key
```powershell
$env:GEMINI_API_KEY="your_key_here"
```

### 2. Start Backend
```bash
python app.py
```

### 2. Start Frontend
```bash
streamlit run app_ui.py
```
## Endpoints
- /audit → Analyse submited Python code
- /library → View stored results
- /health → Service status

## Purpose
To promote green coding practices, reduce computational energy emission and improve code efficiency via an X-as-a-Service approach.