# API Schemas

Pydantic models for request/response validation.

## Request Schemas

### PlanGenerationRequest

```python
class PlanGenerationRequest(BaseModel):
    student_id: str
    report_text: Optional[str] = None
    performance_data: Optional[List[PerformanceDataPoint]] = None
    plan_days: int = Field(7, ge=1, le=30)
    requires_review: bool = False
```

**Validation:**
- `plan_days`: Must be between 1 and 30
- `performance_data`: Each point must have valid accuracy (correct <= attempted)

### PerformanceDataPoint

```python
class PerformanceDataPoint(BaseModel):
    subject: str
    topic: Optional[str] = None
    questions_attempted: int
    questions_correct: int
    avg_time_per_question_sec: Optional[int] = None
    confidence_score: Optional[float] = Field(None, ge=1.0, le=5.0)
```

**Validation:**
- `confidence_score`: Must be between 1.0 and 5.0 (if provided)

## Response Schemas

### AssessmentResponse

```python
class AssessmentResponse(BaseModel):
    student_id: str
    status: str
    diagnostic: Optional[DiagnosticResponse] = None
    knowledge_state: Optional[KnowledgeStateResponse] = None
    study_plan: Optional[PlanResponse] = None
    response_message: Optional[str] = None
    execution_log: List[Dict[str, Any]] = []
    errors: List[str] = []
```

### DiagnosticResponse

```python
class DiagnosticResponse(BaseModel):
    student_id: str
    nbme_score: Optional[int]
    uworld_percentile: Optional[float]
    weak_areas: List[str]
    strong_areas: List[str]
    knowledge_gaps: List[Dict[str, Any]]
    recommended_focus: List[str]
    confidence_scores: Dict[str, float]
```

### KnowledgeStateResponse

```python
class KnowledgeStateResponse(BaseModel):
    student_id: str
    area_proficiency: Dict[str, float]
    predicted_score: float
    last_updated: str
```

### PlanResponse

```python
class PlanResponse(BaseModel):
    plan_id: str
    start_date: str
    end_date: str
    total_blocks: int
    blocks: List[StudyBlockResponse]
    rationale: str
    expected_improvement: float
```

### StudyBlockResponse

```python
class StudyBlockResponse(BaseModel):
    day: int
    date: str
    area: str
    topic: str
    duration_hours: float
    practice_questions: int
    review_type: str
    resources: List[str]
```

### StudentProfile

```python
class StudentProfile(BaseModel):
    student_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    target_exam_date: Optional[str] = None
    study_hours_per_day: Optional[float] = None
    baseline_nbme_score: Optional[int] = None
    baseline_uworld_percentile: Optional[float] = None
```

## Type Mappings

| Python Type | JSON Type | Example |
|------------|-----------|---------|
| `str` | string | `"IMG001"` |
| `int` | number | `185` |
| `float` | number | `45.0` |
| `Optional[T]` | T or null | `null` or `185` |
| `List[T]` | array | `["Cardiology", "Biochem"]` |
| `Dict[str, float]` | object | `{"Cardio": 35.0}` |
| `datetime` | string (ISO) | `"2026-04-07T10:30:00"` |
