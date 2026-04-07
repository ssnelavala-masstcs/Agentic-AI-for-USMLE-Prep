"""
Adaptive Scheduler Agent - Node C in the LangGraph.

Responsibilities:
1. Generate a 7-day (or configurable) study block schedule
2. Apply interleaved practice principles for optimal retention
3. Prioritize weak areas while maintaining strong areas
4. Adapt to student's available study hours per day
5. Incorporate spaced repetition timing

This is the core planning agent that uses the diagnostic and knowledge state
to create personalized, adaptive study plans.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from groq import Groq
from dotenv import load_dotenv
import os

from src.agents.state import AgentState, StudyPlan, StudyBlock, KnowledgeState, DiagnosticResult
from src.database.client import supabase

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Study plan configuration
DEFAULT_PLAN_DAYS = 7
MAX_DAILY_HOURS = 12
MIN_DAILY_HOURS = 2
BREAK_INTERVAL_MINUTES = 50  # Study 50 min, break 10 min

SCHEDULER_SYSTEM_PROMPT = """You are an expert USMLE Adaptive Scheduler AI that creates optimized study plans for International Medical Graduates (IMGs).

PRINCIPLES OF EFFECTIVE USMLE STUDY PLANNING:

1. INTERLEAVED PRACTICE: Mix different subjects/topics within a day rather than blocking one topic all day. This improves long-term retention and transfer.

2. SPACED REPETITION: Schedule review sessions at increasing intervals (1 day, 3 days, 7 days, 14 days) for previously studied material.

3. WEAKNESS PRIORITIZATION: Allocate more time to weak areas (proficiency < 50%) while maintaining strong areas with brief review sessions.

4. ACTIVE RECALL: Prioritize practice questions over passive reading. Each block should include 20-40 practice questions.

5. PROGRESSIVE DIFFICULTY: Start with foundational concepts and progress to complex clinical scenarios.

6. IMG-SPECIFIC CONSIDERATIONS:
   - US healthcare system and ethics need dedicated time
   - Clinical vignette practice is essential
   - Focus on high-yield topics that appear frequently

PLAN STRUCTURE:
- Each day has 2-4 study blocks
- Blocks alternate between weak and strong areas (interleaving)
- Every 3rd day includes a comprehensive review block
- Weekend days include practice question marathons (40-60 questions)

OUTPUT SCHEMA (JSON only):
{
    "student_id": "string",
    "plan_id": "unique-plan-id",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "blocks": [
        {
            "day": 1,
            "date": "YYYY-MM-DD",
            "area": "Subject area",
            "topic": "Specific topic",
            "duration_hours": 2.5,
            "practice_questions": 30,
            "review_type": "active_recall|spaced_repetition|interleaved|full_review",
            "resources": ["UWorld", "First Aid", "Pathoma", etc.]
        }
    ],
    "rationale": "Explanation of plan strategy",
    "interleaving_strategy": "Description of how topics are interleaved",
    "expected_score_improvement": 15.0
}"""


def generate_study_plan(
    student_id: str,
    diagnostic: Optional[DiagnosticResult],
    knowledge_state: KnowledgeState,
    plan_days: int = DEFAULT_PLAN_DAYS
) -> StudyPlan:
    """
    Generate an adaptive study plan using LLM + heuristic optimization.
    
    Args:
        student_id: Student identifier
        diagnostic: Diagnostic assessment results
        knowledge_state: Current knowledge vector
        plan_days: Number of days to plan for
        
    Returns:
        Complete StudyPlan
    """
    # Get student profile
    student_profile = _get_student_profile(student_id)
    daily_hours = student_profile.get("study_hours_per_day", 6.0)
    target_date = student_profile.get("target_exam_date")
    
    # Build plan context for LLM
    context = _build_plan_context(diagnostic, knowledge_state, plan_days, daily_hours)
    
    if groq_client:
        try:
            plan = _generate_plan_llm(context, student_id, plan_days)
            logger.info(f"LLM-generated plan created for {student_id}")
            return plan
        except Exception as e:
            logger.warning(f"LLM plan generation failed, using heuristic: {e}")
    
    # Fallback to heuristic-based plan
    return _generate_plan_heuristic(diagnostic, knowledge_state, student_id, plan_days, daily_hours)


def _generate_plan_llm(
    context: str,
    student_id: str,
    plan_days: int
) -> StudyPlan:
    """Generate plan using LLM."""
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SCHEDULER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Create a {plan_days}-day study plan:\n\n{context}"}
        ],
        temperature=0.3,
        max_tokens=4000,
        response_format={"type": "json_object"}
    )
    
    plan_data = json.loads(response.choices[0].message.content)
    plan_data["student_id"] = student_id
    plan_data["plan_id"] = f"plan_{student_id}_{int(time.time())}"
    
    return StudyPlan(**plan_data)


def _generate_plan_heuristic(
    diagnostic: Optional[DiagnosticResult],
    knowledge_state: KnowledgeState,
    student_id: str,
    plan_days: int,
    daily_hours: float
) -> StudyPlan:
    """
    Generate plan using rule-based heuristic when LLM is unavailable.
    
    This implements evidence-based study strategies:
    - Interleaved practice (Rohrer & Taylor, 2007)
    - Spaced repetition (Cepeda et al., 2008)
    - Active recall (Karpicke & Roediger, 2008)
    """
    start_date = datetime.now()
    proficiency = knowledge_state.get("area_proficiency", {})
    
    # Sort areas by proficiency (weakest first)
    sorted_areas = sorted(proficiency.items(), key=lambda x: x[1])
    weak_areas = [area for area, score in sorted_areas if score < 60]
    strong_areas = [area for area, score in sorted_areas if score >= 60]
    
    if diagnostic:
        weak_areas = diagnostic.get("weak_areas", weak_areas)
        strong_areas = diagnostic.get("strong_areas", strong_areas)
    
    blocks = []
    current_date = start_date
    
    for day in range(1, plan_days + 1):
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Determine block structure based on day pattern
        if day % 3 == 0:  # Every 3rd day: review day
            blocks.extend(_create_review_blocks(day, date_str, weak_areas, strong_areas, daily_hours))
        else:  # Regular learning day
            blocks.extend(_create_learning_blocks(
                day, date_str, weak_areas, strong_areas, daily_hours, knowledge_state
            ))
        
        current_date += timedelta(days=1)
    
    # Calculate expected improvement based on weak area focus
    avg_proficiency = sum(proficiency.values()) / len(proficiency) if proficiency else 50
    expected_improvement = max(5, min(30, (100 - avg_proficiency) * 0.3))
    
    plan = StudyPlan(
        student_id=student_id,
        plan_id=f"plan_{student_id}_{int(time.time())}",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=(start_date + timedelta(days=plan_days-1)).strftime("%Y-%m-%d"),
        blocks=blocks,
        rationale=f"Plan prioritizes {len(weak_areas)} weak areas with interleaved practice. "
                  f"Review blocks scheduled every 3rd day for spaced repetition.",
        interleaving_strategy="Alternating weak and strong areas within days, with comprehensive review every 3rd day",
        expected_score_improvement=round(expected_improvement, 1)
    )
    
    return plan


def _create_learning_blocks(
    day: int,
    date_str: str,
    weak_areas: List[str],
    strong_areas: List[str],
    daily_hours: float,
    knowledge_state: KnowledgeState
) -> List[StudyBlock]:
    """Create study blocks for a regular learning day."""
    blocks = []
    hours_allocated = 0
    
    # Block 1: Primary weak area (largest block)
    if weak_areas:
        area = weak_areas[(day - 1) % len(weak_areas)]
        topic = _get_priority_topic(area, knowledge_state)
        duration = min(3.0, daily_hours * 0.4)
        
        blocks.append(StudyBlock(
            day=day,
            date=date_str,
            area=area,
            topic=topic,
            duration_hours=duration,
            practice_questions=int(duration * 12),
            review_type="active_recall",
            resources=["UWorld Question Bank", "First Aid for USMLE", "Pathoma"]
        ))
        hours_allocated += duration
    
    # Block 2: Secondary area (interleaving)
    remaining_areas = strong_areas if weak_areas else weak_areas
    if remaining_areas or len(weak_areas) > 1:
        area = remaining_areas[(day - 1) % len(remaining_areas)] if remaining_areas else weak_areas[day % len(weak_areas)]
        topic = _get_priority_topic(area, knowledge_state)
        duration = min(2.0, daily_hours * 0.3)
        
        blocks.append(StudyBlock(
            day=day,
            date=date_str,
            area=area,
            topic=topic,
            duration_hours=duration,
            practice_questions=int(duration * 10),
            review_type="interleaved",
            resources=["UWorld Question Bank", "Amboss Library"]
        ))
        hours_allocated += duration
    
    # Block 3: Quick review of strong area (spaced repetition)
    if strong_areas and hours_allocated < daily_hours:
        area = strong_areas[(day - 1) % len(strong_areas)]
        duration = min(1.5, daily_hours - hours_allocated)
        
        blocks.append(StudyBlock(
            day=day,
            date=date_str,
            area=area,
            topic="High-yield review",
            duration_hours=duration,
            practice_questions=int(duration * 8),
            review_type="spaced_repetition",
            resources=["Anki Deck - USMLE-Rx", "First Aid Rapid Review"]
        ))
    
    return blocks


def _create_review_blocks(
    day: int,
    date_str: str,
    weak_areas: List[str],
    strong_areas: List[str],
    daily_hours: float
) -> List[StudyBlock]:
    """Create comprehensive review blocks for every 3rd day."""
    blocks = []
    
    # Morning: Weak area intensive review
    if weak_areas:
        area = weak_areas[0]
        duration = daily_hours * 0.4
        
        blocks.append(StudyBlock(
            day=day,
            date=date_str,
            area=area,
            topic="Comprehensive review",
            duration_hours=duration,
            practice_questions=int(duration * 15),
            review_type="full_review",
            resources=["UWorld Incorrects", "First Aid Annotations", "NBME Practice"]
        ))
    
    # Afternoon: Mixed practice (simulates exam conditions)
    remaining_hours = daily_hours - sum(b["duration_hours"] for b in blocks)
    if remaining_hours > 1:
        blocks.append(StudyBlock(
            day=day,
            date=date_str,
            area="Mixed",
            topic="Interleaved practice test",
            duration_hours=remaining_hours,
            practice_questions=int(remaining_hours * 20),
            review_type="interleaved",
            resources=["UWorld Self-Assessment", "NBME Practice Questions"]
        ))
    
    return blocks


def _get_priority_topic(area: str, knowledge_state: KnowledgeState) -> str:
    """Get the highest-priority topic within an area."""
    # Topic prioritization map for common USMLE areas
    topic_map = {
        "Cardiology": "Heart Failure",
        "Biochemistry": "Enzyme Kinetics",
        "Pharmacology": "Autonomic Drugs",
        "Neurology": "Stroke Syndromes",
        "Pathology": "Inflammation and Repair",
        "Microbiology": "Bacteriology",
        "Physiology": "Cardiovascular Physiology",
        "Anatomy": "Thorax"
    }
    return topic_map.get(area, "High-yield concepts")


def _build_plan_context(
    diagnostic: Optional[DiagnosticResult],
    knowledge_state: KnowledgeState,
    plan_days: int,
    daily_hours: float
) -> str:
    """Build context string for LLM plan generation."""
    context = f"Plan Duration: {plan_days} days\n"
    context += f"Daily Study Hours: {daily_hours}\n"
    context += f"Current Predicted Score: {knowledge_state.get('predicted_score', 'N/A')}\n\n"
    
    if diagnostic:
        context += "WEAK AREAS (need immediate focus):\n"
        for area in diagnostic.get("weak_areas", []):
            context += f"- {area}\n"
        
        context += "\nSTRONG AREAS (maintain with review):\n"
        for area in diagnostic.get("strong_areas", []):
            context += f"- {area}\n"
        
        if diagnostic.get("knowledge_gaps"):
            context += "\nSPECIFIC KNOWLEDGE GAPS:\n"
            for gap in diagnostic["knowledge_gaps"]:
                context += f"- {gap['topic']} (severity: {gap['severity']})\n"
    
    context += "\nPROFICIENCY BY AREA:\n"
    for area, score in knowledge_state.get("area_proficiency", {}).items():
        context += f"- {area}: {score:.1f}%\n"
    
    return context


def _get_student_profile(student_id: str) -> Dict[str, Any]:
    """Retrieve student profile from Supabase."""
    try:
        response = supabase.table("students").select("*").eq(
            "external_id", student_id
        ).execute()
        
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.error(f"Failed to retrieve student profile: {e}")
    
    return {"study_hours_per_day": 6.0, "target_exam_date": None}


def scheduler_node(state: AgentState) -> AgentState:
    """LangGraph node wrapper for the Adaptive Scheduler agent."""
    student_id = state["student_external_id"]
    diagnostic = state.get("diagnostic")
    knowledge_state = state.get("knowledge_state")
    
    if not knowledge_state:
        logger.error("[Scheduler] No knowledge state available")
        return {
            **state,
            "errors": state.get("errors", []) + ["Scheduler requires knowledge state"],
            "execution_log": state.get("execution_log", []) + [{
                "agent": "Scheduler",
                "action": "failed",
                "error": "No knowledge state",
                "timestamp": time.time()
            }]
        }
    
    logger.info(f"[Scheduler] Generating adaptive study plan for {student_id}")
    
    study_plan = generate_study_plan(student_id, diagnostic, knowledge_state)
    
    # Serialize plan for API response
    plan_json = {
        "plan_id": study_plan["plan_id"],
        "start_date": study_plan["start_date"],
        "end_date": study_plan["end_date"],
        "total_blocks": len(study_plan["blocks"]),
        "blocks": study_plan["blocks"],
        "rationale": study_plan["rationale"],
        "expected_improvement": study_plan["expected_score_improvement"],
        "multimodal_enabled": True
    }
    
    # Persist to Supabase
    _persist_study_plan(student_id, study_plan)
    
    execution_log_entry = {
        "agent": "Scheduler",
        "action": "generate_study_plan",
        "student_id": student_id,
        "plan_days": len(study_plan["blocks"]),
        "expected_improvement": study_plan["expected_score_improvement"],
        "timestamp": time.time()
    }
    
    return {
        **state,
        "study_plan": study_plan,
        "plan_json": plan_json,
        "response_message": f"Generated {len(study_plan['blocks'])}-block study plan. "
                           f"Expected improvement: +{study_plan['expected_score_improvement']:.0f} points",
        "execution_log": state.get("execution_log", []) + [execution_log_entry]
    }


def _persist_study_plan(student_id: str, plan: StudyPlan):
    """Save study plan to Supabase."""
    try:
        student_response = supabase.table("students").select("id").eq(
            "external_id", student_id
        ).execute()
        
        if not student_response.data:
            logger.warning(f"Cannot persist plan: student {student_id} not found")
            return
        
        student_uuid = student_response.data[0]["id"]
        
        # Insert plan
        plan_response = supabase.table("study_plans").insert({
            "student_id": student_uuid,
            "plan_start_date": plan["start_date"],
            "plan_end_date": plan["end_date"],
            "plan_json": {
                "blocks": plan["blocks"],
                "rationale": plan["rationale"],
                "interleaving_strategy": plan["interleaving_strategy"]
            },
            "generation_model": GROQ_MODEL
        }).execute()
        
        if plan_response.data:
            plan_uuid = plan_response.data[0]["id"]
            
            # Insert individual blocks
            for block in plan["blocks"]:
                supabase.table("study_blocks").insert({
                    "study_plan_id": plan_uuid,
                    "day_number": block["day"],
                    "date": block["date"],
                    "area": block.get("area"),
                    "topic": block.get("topic"),
                    "recommended_duration_hours": block.get("duration_hours"),
                    "practice_questions": block.get("practice_questions"),
                    "review_materials": block.get("resources", [])
                }).execute()
        
        logger.info(f"Study plan persisted for {student_id}")
        
    except Exception as e:
        logger.error(f"Failed to persist study plan: {e}")
