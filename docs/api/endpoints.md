# API Endpoints

Complete REST API reference for the Agentic USMLE system.

**Base URL**: `http://localhost:8000/api/v1`

## Authentication

Currently, the API does not enforce authentication. For production, implement:

- JWT tokens via Supabase Auth
- API keys for service-to-service calls
- Rate limiting per student/client

## Endpoints

### 1. Generate Assessment

```
POST /assess
```

Run the complete agentic pipeline for a student.

**Request Body:**

```json
{
  "student_id": "IMG001",
  "report_text": "NBME 185, UWorld 45th percentile",
  "performance_data": [
    {
      "subject": "Cardiology",
      "topic": "Heart Failure",
      "questions_attempted": 25,
      "questions_correct": 15,
      "avg_time_per_question_sec": 90,
      "confidence_score": 3.2
    }
  ],
  "plan_days": 7,
  "requires_review": false
}
```

**Response:** `AssessmentResponse`

```json
{
  "student_id": "IMG001",
  "status": "success",
  "diagnostic": { ... },
  "knowledge_state": { ... },
  "study_plan": { ... },
  "response_message": "Generated 18-block study plan...",
  "execution_log": [...],
  "errors": []
}
```

**Errors:**
- `400` - Invalid request body
- `404` - Student not found
- `500` - Pipeline execution failed

---

### 2. Get Student Profile

```
GET /students/{student_id}/profile
```

Retrieve student demographic and baseline data.

**Response:** `StudentProfile`

```json
{
  "student_id": "IMG001",
  "name": "John Doe",
  "email": "john@example.com",
  "target_exam_date": "2026-09-15",
  "study_hours_per_day": 6.0,
  "baseline_nbme_score": 185,
  "baseline_uworld_percentile": 45.0
}
```

---

### 3. Get Knowledge State

```
GET /students/{student_id}/knowledge
```

Retrieve current knowledge vector and predicted score.

**Response:** `KnowledgeStateResponse`

```json
{
  "student_id": "IMG001",
  "area_proficiency": {
    "Cardiology": 35.0,
    "Biochemistry": 40.0,
    "Anatomy": 75.0
  },
  "predicted_score": 182.5,
  "last_updated": "2026-04-07T10:30:00"
}
```

---

### 4. Get Study Plans

```
GET /students/{student_id}/plans?limit=5
```

Retrieve recent study plans for a student.

**Query Parameters:**
- `limit` (int, default 5): Number of plans to return

**Response:** `List[PlanResponse]`

---

### 5. Health Check

```
GET /health
```

System health and database connectivity.

**Response:**

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-04-07T10:30:00"
}
```

---

### 6. Root

```
GET /
```

Service information.

**Response:**

```json
{
  "name": "USMLE Agentic AI System",
  "version": "1.0.0",
  "docs": "/docs",
  "status": "running"
}
```

## Interactive Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400` - Bad Request (validation error)
- `404` - Not Found (student/data doesn't exist)
- `422` - Unprocessable Entity (schema validation)
- `500` - Internal Server Error (pipeline failure)
