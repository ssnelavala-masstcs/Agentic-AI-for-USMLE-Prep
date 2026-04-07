"""
Pydantic schemas for API request/response validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DiagnosticRequest(BaseModel):
    """Request to run diagnostic analysis."""
    student_id: str = Field(..., description="External student identifier")
    report_text: Optional[str] = Field(None, description="Raw NBME/UWorld performance report")


class PerformanceDataPoint(BaseModel):
    """Single session performance log entry."""
    subject: str
    topic: Optional[str] = None
    questions_attempted: int
    questions_correct: int
    avg_time_per_question_sec: Optional[int] = None
    confidence_score: Optional[float] = Field(None, ge=1.0, le=5.0)


class PlanGenerationRequest(BaseModel):
    """Request to generate a complete study plan."""
    student_id: str
    report_text: Optional[str] = None
    performance_data: Optional[List[PerformanceDataPoint]] = None
    plan_days: int = Field(7, ge=1, le=30, description="Number of days to plan")
    requires_review: bool = Field(False, description="Force human review routing")


class DiagnosticResponse(BaseModel):
    """Parsed diagnostic assessment."""
    student_id: str
    nbme_score: Optional[int]
    uworld_percentile: Optional[float]
    weak_areas: List[str]
    strong_areas: List[str]
    knowledge_gaps: List[Dict[str, Any]]
    recommended_focus: List[str]
    confidence_scores: Dict[str, float]


class KnowledgeStateResponse(BaseModel):
    """Current knowledge vector state."""
    student_id: str
    area_proficiency: Dict[str, float]
    predicted_score: float
    last_updated: str


class StudyBlockResponse(BaseModel):
    """Single study block in the plan."""
    day: int
    date: str
    area: str
    topic: str
    duration_hours: float
    practice_questions: int
    review_type: str
    resources: List[str]


class PlanResponse(BaseModel):
    """Generated study plan."""
    plan_id: str
    start_date: str
    end_date: str
    total_blocks: int
    blocks: List[StudyBlockResponse]
    rationale: str
    expected_improvement: float


class AssessmentResponse(BaseModel):
    """Complete assessment response."""
    student_id: str
    status: str
    diagnostic: Optional[DiagnosticResponse] = None
    knowledge_state: Optional[KnowledgeStateResponse] = None
    study_plan: Optional[PlanResponse] = None
    response_message: Optional[str] = None
    execution_log: List[Dict[str, Any]] = []
    errors: List[str] = []


class StudentProfile(BaseModel):
    """Student profile information."""
    student_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    target_exam_date: Optional[str] = None
    study_hours_per_day: Optional[float] = None
    baseline_nbme_score: Optional[int] = None
    baseline_uworld_percentile: Optional[float] = None
