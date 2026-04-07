"""
FastAPI routes for the USMLE Agentic AI System.

Provides REST endpoints for:
- Student assessment and plan generation
- Retrieving study plans
- Updating performance data
- Viewing knowledge state
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from src.api.schemas import (
    PlanGenerationRequest,
    AssessmentResponse,
    DiagnosticResponse,
    KnowledgeStateResponse,
    PlanResponse,
    StudentProfile
)
from src.agents.main import run_student_assessment
from src.database.client import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["USMLE Agentic System"])


@router.post("/assess", response_model=AssessmentResponse)
async def generate_assessment(request: PlanGenerationRequest):
    """
    Run the complete agentic assessment pipeline.
    
    Executes: Diagnostician -> KnowledgeManager -> Scheduler
    Returns: Complete study plan with diagnostic and knowledge state
    """
    try:
        # Format performance data for agents
        perf_data = None
        if request.performance_data:
            perf_data = [p.model_dump() for p in request.performance_data]
        
        # Run the agent pipeline
        result = await run_student_assessment(
            student_id=request.student_id,
            report_text=request.report_text,
            performance_data=perf_data,
            requires_review=request.requires_review
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        # Build response
        response_data = {
            "student_id": result["student_id"],
            "status": result["status"],
            "response_message": result.get("response"),
            "execution_log": result.get("execution_log", []),
            "errors": result.get("errors", [])
        }
        
        if result.get("diagnostic"):
            response_data["diagnostic"] = result["diagnostic"]
        
        if result.get("knowledge_state"):
            ks = result["knowledge_state"]
            response_data["knowledge_state"] = {
                "student_id": ks["student_id"],
                "area_proficiency": ks["area_proficiency"],
                "predicted_score": ks["predicted_score"],
                "last_updated": ks["last_updated"]
            }
        
        if result.get("study_plan"):
            plan = result["study_plan"]
            response_data["study_plan"] = {
                "plan_id": plan["plan_id"],
                "start_date": plan["start_date"],
                "end_date": plan["end_date"],
                "total_blocks": plan["total_blocks"],
                "blocks": plan["blocks"],
                "rationale": plan["rationale"],
                "expected_improvement": plan["expected_improvement"]
            }
        
        return AssessmentResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assessment failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/{student_id}/profile", response_model=StudentProfile)
async def get_student_profile(student_id: str):
    """Retrieve student profile information."""
    try:
        response = supabase.table("students").select("*").eq("external_id", student_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
        
        data = response.data[0]
        return StudentProfile(
            student_id=data["external_id"],
            name=data.get("name"),
            email=data.get("email"),
            target_exam_date=data.get("target_exam_date"),
            study_hours_per_day=data.get("study_hours_per_day"),
            baseline_nbme_score=data.get("baseline_nbme_score"),
            baseline_uworld_percentile=data.get("baseline_uworld_percentile")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve student profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/{student_id}/knowledge", response_model=KnowledgeStateResponse)
async def get_knowledge_state(student_id: str):
    """Retrieve current knowledge vector for a student."""
    try:
        from src.agents.knowledge_manager import get_student_knowledge, _calculate_predicted_score
        
        proficiency = get_student_knowledge(student_id)
        
        if not proficiency:
            raise HTTPException(status_code=404, detail=f"No knowledge data for {student_id}")
        
        return KnowledgeStateResponse(
            student_id=student_id,
            area_proficiency=proficiency,
            predicted_score=_calculate_predicted_score(proficiency),
            last_updated=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve knowledge state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/{student_id}/plans", response_model=List[PlanResponse])
async def get_student_plans(student_id: str, limit: int = 5):
    """Retrieve recent study plans for a student."""
    try:
        response = supabase.table("study_plans").select(
            "*, study_blocks(*)"
        ).eq("student_external_id", student_id).order(
            "created_at", desc=True
        ).limit(limit).execute()
        
        if not response.data:
            return []
        
        plans = []
        for plan_data in response.data:
            plan_json = plan_data.get("plan_json", {})
            plans.append(PlanResponse(
                plan_id=str(plan_data["id"]),
                start_date=plan_data["plan_start_date"],
                end_date=plan_data["plan_end_date"],
                total_blocks=len(plan_json.get("blocks", [])),
                blocks=plan_json.get("blocks", []),
                rationale=plan_json.get("rationale", ""),
                expected_improvement=0.0
            ))
        
        return plans
    except Exception as e:
        logger.error(f"Failed to retrieve plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    from src.database.client import test_connection
    
    db_connected = test_connection()
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "database": "connected" if db_connected else "disconnected",
        "timestamp": datetime.now().isoformat()
    }
