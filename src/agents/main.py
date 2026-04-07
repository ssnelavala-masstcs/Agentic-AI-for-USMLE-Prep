"""
Main entry point for the USMLE Agentic AI System.

Provides a simple interface to run the complete agent pipeline
and serves as a CLI tool for testing.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from src.agents.graph_builder import graph
from src.agents.state import AgentState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def run_student_assessment(
    student_id: str,
    report_text: Optional[str] = None,
    performance_data: Optional[list] = None,
    requires_review: bool = False
) -> Dict[str, Any]:
    """
    Run the complete agentic pipeline for a student.
    
    Args:
        student_id: External student identifier
        report_text: Raw NBME/UWorld performance report
        performance_data: Session-level performance logs
        requires_review: Force human review routing
        
    Returns:
        Complete pipeline results including study plan
    """
    initial_state: AgentState = {
        "student_external_id": student_id,
        "input_report": report_text or "",
        "new_performance_data": performance_data,
        "diagnostic": None,
        "knowledge_state": None,
        "study_plan": None,
        "requires_human_review": requires_review,
        "human_feedback": None,
        "iteration_count": 1,
        "errors": [],
        "execution_log": [],
        "response_message": "",
        "plan_json": None
    }
    
    # Execute the graph
    config = {"configurable": {"thread_id": f"{student_id}_{datetime.now().isoformat()}"}}
    
    logger.info(f"Starting assessment for student {student_id}")
    
    try:
        result = await graph.ainvoke(initial_state, config=config)
        
        logger.info(f"Assessment completed for {student_id}")
        logger.info(f"Response: {result.get('response_message', 'N/A')}")
        
        return {
            "student_id": student_id,
            "status": "success" if not result.get("errors") else "completed_with_errors",
            "diagnostic": result.get("diagnostic"),
            "knowledge_state": result.get("knowledge_state"),
            "study_plan": result.get("plan_json"),
            "response": result.get("response_message"),
            "execution_log": result.get("execution_log", []),
            "errors": result.get("errors", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return {
            "student_id": student_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def run_sync(*args, **kwargs):
    """Synchronous wrapper for async execution."""
    return asyncio.run(run_student_assessment(*args, **kwargs))


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="USMLE Agentic AI System")
    parser.add_argument("--student-id", required=True, help="Student identifier")
    parser.add_argument("--report", help="Path to performance report file")
    parser.add_argument("--review", action="store_true", help="Require human review")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    report_text = None
    if args.report:
        with open(args.report, "r") as f:
            report_text = f.read()
    
    result = run_sync(
        student_id=args.student_id,
        report_text=report_text,
        requires_review=args.review
    )
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"\n{'='*60}")
        print(f"USMLE Agentic Assessment Results")
        print(f"{'='*60}")
        print(f"Student ID: {result['student_id']}")
        print(f"Status: {result['status']}")
        print(f"\nResponse: {result.get('response', 'N/A')}")
        
        if result.get("diagnostic"):
            diag = result["diagnostic"]
            print(f"\nDiagnostic Summary:")
            print(f"  NBME Score: {diag.get('nbme_score', 'N/A')}")
            print(f"  UWorld Percentile: {diag.get('uworld_percentile', 'N/A')}")
            print(f"  Weak Areas: {', '.join(diag.get('weak_areas', []))}")
            print(f"  Strong Areas: {', '.join(diag.get('strong_areas', []))}")
        
        if result.get("knowledge_state"):
            ks = result["knowledge_state"]
            print(f"\nKnowledge State:")
            print(f"  Predicted Score: {ks.get('predicted_score', 'N/A')}")
            print(f"  Areas Tracked: {len(ks.get('area_proficiency', {}))}")
        
        if result.get("study_plan"):
            plan = result["study_plan"]
            print(f"\nStudy Plan:")
            print(f"  Plan ID: {plan.get('plan_id', 'N/A')}")
            print(f"  Total Blocks: {plan.get('total_blocks', 0)}")
            print(f"  Expected Improvement: +{plan.get('expected_improvement', 0):.0f} points")
        
        print(f"\nExecution Log:")
        for entry in result.get("execution_log", []):
            print(f"  [{entry.get('agent')}] {entry.get('action')}")
        
        if result.get("errors"):
            print(f"\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")
        
        print(f"{'='*60}\n")
