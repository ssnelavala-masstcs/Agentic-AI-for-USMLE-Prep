"""
Knowledge Manager Agent - Node B in the LangGraph.

Responsibilities:
1. Maintain a persistent "Knowledge Vector" for each student in Supabase
2. Update proficiency scores based on diagnostic results and performance logs
3. Calculate predicted readiness and score trajectories
4. Provide the scheduler with current knowledge state

This agent acts as the memory system - it reads from and writes to Supabase
to ensure student progress persists across sessions.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.agents.state import AgentState, KnowledgeState, DiagnosticResult
from src.database.client import supabase

logger = logging.getLogger(__name__)

# Proficiency update parameters
LEARNING_RATE = 0.15  # How quickly new performance updates the model
RETENTION_DECAY = 0.02  # Daily decay factor for unreviewed topics
COMPETENCY_THRESHOLD = 60.0  # Minimum proficiency for "mastered" status


def get_student_knowledge(student_id: str) -> Dict[str, float]:
    """Retrieve current knowledge state from Supabase."""
    try:
        # Get student record
        student_response = supabase.table("students").select("*").eq("external_id", student_id).execute()
        
        if not student_response.data:
            logger.warning(f"Student {student_id} not found in database")
            return {}
        
        student_uuid = student_response.data[0]["id"]
        
        # Get knowledge areas with proficiency
        knowledge_response = supabase.table("student_knowledge").select(
            "*, knowledge_areas(name)"
        ).eq("student_id", student_uuid).execute()
        
        proficiency = {}
        for record in knowledge_response.data or []:
            area_name = record.get("knowledge_areas", {}).get("name", "Unknown")
            proficiency[area_name] = record.get("proficiency_score", 0.0)
        
        return proficiency
        
    except Exception as e:
        logger.error(f"Failed to retrieve knowledge state: {e}")
        return {}


def update_knowledge_state(
    student_id: str,
    diagnostic: DiagnosticResult,
    performance_data: Optional[List[Dict[str, Any]]] = None
) -> KnowledgeState:
    """
    Update student knowledge vector based on new diagnostic and performance data.
    
    Args:
        student_id: External student identifier
        diagnostic: Output from Diagnostician agent
        performance_data: Optional session-level performance logs
        
    Returns:
        Updated KnowledgeState
    """
    # Get current state
    current_proficiency = get_student_knowledge(student_id)
    
    # If no existing data, initialize from diagnostic
    if not current_proficiency:
        current_proficiency = _initialize_from_diagnostic(diagnostic)
    
    # Update based on diagnostic findings
    updated_proficiency = current_proficiency.copy()
    
    # Decrease proficiency for weak areas
    for area in diagnostic.get("weak_areas", []):
        current = current_proficiency.get(area, 50.0)
        updated_proficiency[area] = max(0, current - 10)
    
    # Increase proficiency for strong areas
    for area in diagnostic.get("strong_areas", []):
        current = current_proficiency.get(area, 50.0)
        updated_proficiency[area] = min(100, current + 5)
    
    # Apply performance data updates if available
    if performance_data:
        updated_proficiency = _apply_performance_updates(updated_proficiency, performance_data)
    
    # Calculate predicted score
    predicted_score = _calculate_predicted_score(updated_proficiency)
    
    knowledge_state = KnowledgeState(
        student_id=student_id,
        area_proficiency=updated_proficiency,
        last_updated=datetime.now().isoformat(),
        embedding_version=1,
        predicted_score=predicted_score,
        readiness_by_date=None  # Will be set by scheduler
    )
    
    # Persist to Supabase
    _persist_knowledge_state(student_id, knowledge_state)
    
    return knowledge_state


def _initialize_from_diagnostic(diagnostic: DiagnosticResult) -> Dict[str, float]:
    """Initialize knowledge state from diagnostic results."""
    proficiency = {}
    
    # Set weak areas below threshold
    for area in diagnostic.get("weak_areas", []):
        proficiency[area] = 35.0
    
    # Set strong areas above threshold
    for area in diagnostic.get("strong_areas", []):
        proficiency[area] = 78.0
    
    # Use confidence scores if available
    for area, confidence in diagnostic.get("confidence_scores", {}).items():
        # Convert 1-5 confidence to 0-100 proficiency
        proficiency[area] = (confidence / 5.0) * 100
    
    return proficiency


def _apply_performance_updates(
    current_proficiency: Dict[str, float],
    performance_data: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Update proficiency based on recent performance logs."""
    updated = current_proficiency.copy()
    
    for session in performance_data:
        area = session.get("knowledge_area") or session.get("subject")
        if not area:
            continue
        
        attempted = session.get("questions_attempted", 0)
        correct = session.get("questions_correct", 0)
        
        if attempted == 0:
            continue
        
        session_accuracy = correct / attempted
        current = current_proficiency.get(area, 50.0)
        
        # Exponential moving average update
        new_proficiency = (1 - LEARNING_RATE) * current + LEARNING_RATE * (session_accuracy * 100)
        updated[area] = min(100, max(0, new_proficiency))
    
    return updated


def _calculate_predicted_score(proficiency: Dict[str, float]) -> float:
    """
    Predict USMLE score based on current knowledge state.
    
    Uses weighted average of proficiencies mapped to 3-digit score scale (1-300).
    """
    if not proficiency:
        return 180.0  # Baseline
    
    # USMLE passing score is typically 196-200
    # Map average proficiency to score range 140-260
    avg_proficiency = sum(proficiency.values()) / len(proficiency)
    predicted = 140 + (avg_proficiency / 100) * 120
    
    return round(predicted, 1)


def _persist_knowledge_state(student_id: str, state: KnowledgeState):
    """Save updated knowledge state to Supabase."""
    try:
        # Get student UUID
        student_response = supabase.table("students").select("id").eq(
            "external_id", student_id
        ).execute()
        
        if not student_response.data:
            logger.warning(f"Cannot persist: student {student_id} not found")
            return
        
        student_uuid = student_response.data[0]["id"]
        
        # Upsert knowledge areas
        for area_name, proficiency in state["area_proficiency"].items():
            # Get knowledge area UUID
            area_response = supabase.table("knowledge_areas").select("id").eq(
                "name", area_name
            ).execute()
            
            if not area_response.data:
                continue
            
            area_uuid = area_response.data[0]["id"]
            
            # Upsert
            supabase.table("student_knowledge").upsert({
                "student_id": student_uuid,
                "knowledge_area_id": area_uuid,
                "proficiency_score": proficiency,
                "last_assessed": datetime.now().isoformat()
            }, on_conflict="student_id,knowledge_area_id").execute()
        
        logger.info(f"Knowledge state persisted for {student_id}")
        
    except Exception as e:
        logger.error(f"Failed to persist knowledge state: {e}")


def knowledge_manager_node(state: AgentState) -> AgentState:
    """LangGraph node wrapper for the Knowledge Manager agent."""
    student_id = state["student_external_id"]
    diagnostic = state.get("diagnostic")
    performance_data = state.get("new_performance_data")
    
    if not diagnostic:
        logger.warning("[KnowledgeManager] No diagnostic data available, using existing knowledge")
        knowledge_state = KnowledgeState(
            student_id=student_id,
            area_proficiency=get_student_knowledge(student_id),
            last_updated=datetime.now().isoformat(),
            embedding_version=1,
            predicted_score=180.0,
            readiness_by_date=None
        )
    else:
        logger.info(f"[KnowledgeManager] Updating knowledge state for {student_id}")
        knowledge_state = update_knowledge_state(student_id, diagnostic, performance_data)
    
    execution_log_entry = {
        "agent": "KnowledgeManager",
        "action": "update_knowledge_vector",
        "student_id": student_id,
        "areas_tracked": len(knowledge_state["area_proficiency"]),
        "predicted_score": knowledge_state["predicted_score"],
        "timestamp": time.time()
    }
    
    return {
        **state,
        "knowledge_state": knowledge_state,
        "execution_log": state.get("execution_log", []) + [execution_log_entry]
    }
