# Quick Start Guide

Get the Agentic USMLE system running in 5 minutes.

## Prerequisites

Complete the [Installation Guide](installation.md) first.

## Running the API Server

```bash
uvicorn src.api.app:app --reload --port 8000
```

The server will start at `http://localhost:8000`.

Access interactive API docs at: `http://localhost:8000/docs`

## Running Your First Assessment

### Method 1: Via API

```bash
curl -X POST http://localhost:8000/api/v1/assess \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "IMG001",
    "report_text": "Student scored 185 on NBME 25, 45th percentile on UWorld. Weak in Cardiology and Biochemistry.",
    "plan_days": 7
  }'
```

### Method 2: Via Python

```python
from src.agents.main import run_sync

result = run_sync(
    student_id="IMG001",
    report_text="NBME 185, UWorld 45th percentile. Weak: Cardiology, Biochemistry",
    requires_review=False
)

print(result["response"])
print(result["study_plan"])
```

### Method 3: Via CLI

```bash
python -m src.agents.main --student-id IMG001 --report data/sample_report.csv
```

## Understanding the Output

The assessment returns three main components:

### 1. Diagnostic Assessment

```json
{
  "nbme_score": 185,
  "uworld_percentile": 45.0,
  "weak_areas": ["Cardiology", "Biochemistry"],
  "strong_areas": ["Anatomy"],
  "recommended_focus": ["Cardiology - Heart Failure", "Biochemistry - Enzymes"]
}
```

### 2. Knowledge State

```json
{
  "predicted_score": 182.5,
  "area_proficiency": {
    "Cardiology": 35.0,
    "Biochemistry": 40.0,
    "Anatomy": 75.0
  }
}
```

### 3. Study Plan

```json
{
  "plan_id": "plan_IMG001_1234567890",
  "total_blocks": 18,
  "expected_improvement": 15.0,
  "blocks": [
    {
      "day": 1,
      "area": "Cardiology",
      "topic": "Heart Failure",
      "duration_hours": 2.5,
      "practice_questions": 30
    }
  ]
}
```

## Loading Sample Data

The `data/` directory includes sample CSV files:

- `sample_report.csv` - Student profiles with NBME/UWorld scores
- `sample_performance.csv` - Session-level performance logs

Load them into your system:

```python
import pandas as pd
from src.database.client import supabase

# Load student profiles
students = pd.read_csv("data/sample_report.csv")
# Insert into Supabase (see database schema for structure)
```

## Next Steps

- Review the [Architecture Overview](../architecture/overview.md)
- Explore the [API Endpoints](../api/endpoints.md)
- Read the [Student Onboarding Guide](../students/onboarding.md)
