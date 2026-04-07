"""
State definitions for the USMLE Agentic Graph.

This module defines the TypedDict state that flows through the LangGraph.
The state captures:
- Student identification and profile
- Diagnostic assessment results
- Knowledge graph updates
- Generated study plan
- Execution metadata
"""

from typing import Optional, List, Dict, Any, Literal
from typing_extensions import TypedDict


class DiagnosticResult(TypedDict):
    """Output from the Diagnostician agent."""
    student_id: str
    nbme_score: Optional[int]
    uworld_percentile: Optional[float]
    weak_areas: List[str]
    strong_areas: List[str]
    knowledge_gaps: List[Dict[str, Any]]  # topic -> severity (0-1)
    recommended_focus: List[str]
    confidence_scores: Dict[str, float]
    raw_report: str


class KnowledgeState(TypedDict):
    """Student knowledge vector maintained by Knowledge Manager."""
    student_id: str
    area_proficiency: Dict[str, float]  # area_name -> proficiency (0-100)
    last_updated: str
    embedding_version: int
    predicted_score: float
    readiness_by_date: Optional[str]  # ISO date


class StudyBlock(TypedDict):
    """A single study block in the schedule."""
    day: int
    date: str  # ISO date
    area: str
    topic: str
    duration_hours: float
    practice_questions: int
    review_type: Literal["active_recall", "spaced_repetition", "interleaved", "full_review"]
    resources: List[str]
    # Multimodal fields (added by Resource Optimizer)
    resource_details: Optional[Dict[str, Any]]  # modality -> resource list
    resource_summary: Optional[str]  # Human-readable summary
    resource_modalities: Optional[List[str]]  # ['text', 'image', 'video']
    is_img_optimized: Optional[bool]


class StudyPlan(TypedDict):
    """Output from the Adaptive Scheduler."""
    student_id: str
    plan_id: str
    start_date: str
    end_date: str
    blocks: List[StudyBlock]
    rationale: str
    interleaving_strategy: str
    expected_score_improvement: float


class AgentState(TypedDict):
    """
    Complete state for the USMLE Agentic Graph.
    
    This state flows through all nodes in the LangGraph:
    Diagnostician -> KnowledgeManager -> AdaptiveScheduler -> [HumanReview] -> Persist
    """
    # Input
    student_external_id: str
    input_report: Optional[str]  # Raw NBME/UWorld report text
    new_performance_data: Optional[List[Dict[str, Any]]]  # Session-level data
    
    # Agent outputs
    diagnostic: Optional[DiagnosticResult]
    knowledge_state: Optional[KnowledgeState]
    study_plan: Optional[StudyPlan]
    
    # Control flow
    requires_human_review: bool
    human_feedback: Optional[Dict[str, Any]]
    iteration_count: int
    
    # Metadata
    errors: List[str]
    execution_log: List[Dict[str, Any]]
    
    # Response
    response_message: str
    plan_json: Optional[Dict[str, Any]]  # Serialized plan for API response
