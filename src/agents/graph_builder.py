"""
LangGraph State Graph Definition.

This module assembles the complete agentic workflow:
Diagnostician -> KnowledgeManager -> Scheduler -> [HumanReview] -> Persist

The graph supports:
- Linear execution for automated planning
- Human-in-the-loop interruption for review
- Conditional routing based on confidence thresholds
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.state import AgentState
from src.agents.diagnostician import diagnostician_node
from src.agents.knowledge_manager import knowledge_manager_node
from src.agents.resource_optimizer import resource_optimizer_node
from src.agents.scheduler import scheduler_node

logger = logging.getLogger(__name__)


def should_review(state: AgentState) -> Literal["review", "finalize"]:
    """
    Conditional edge: determine if human review is needed.
    
    Review is triggered when:
    - Student has low confidence (predicted score < 180)
    - Multiple weak areas identified (>3)
    - Explicitly requested in state
    """
    knowledge_state = state.get("knowledge_state")
    diagnostic = state.get("diagnostic")
    
    needs_review = state.get("requires_human_review", False)
    
    if knowledge_state and knowledge_state.get("predicted_score", 200) < 180:
        needs_review = True
    
    if diagnostic and len(diagnostic.get("weak_areas", [])) > 3:
        needs_review = True
    
    if needs_review:
        logger.info("[Graph] Routing to human review")
        return "review"
    
    logger.info("[Graph] Skipping human review, finalizing")
    return "finalize"


def human_review_node(state: AgentState) -> AgentState:
    """
    Human-in-the-loop node for Blessie/Stanley to review and adjust plans.
    
    In production, this would wait for UI approval.
    For now, it auto-approves with logging.
    """
    logger.info("[HumanReview] Plan review requested - auto-approving in prototype")
    
    feedback = state.get("human_feedback")
    execution_log = state.get("execution_log", []) + [{
        "agent": "HumanReview",
        "action": "plan_approved",
        "feedback": feedback,
        "timestamp": __import__("time").time()
    }]
    
    return {
        **state,
        "human_feedback": feedback or {"status": "approved", "notes": "Auto-approved in prototype mode"},
        "execution_log": execution_log
    }


def finalize_node(state: AgentState) -> AgentState:
    """Final processing node - aggregates results and prepares response."""
    study_plan = state.get("study_plan")
    
    response = {
        "status": "success",
        "student_id": state["student_external_id"],
        "iterations": state.get("iteration_count", 1),
        "agents_executed": len(state.get("execution_log", []))
    }
    
    if study_plan:
        response["plan_summary"] = {
            "plan_id": study_plan["plan_id"],
            "duration_days": len(study_plan["blocks"]),
            "start_date": study_plan["start_date"],
            "end_date": study_plan["end_date"],
            "expected_improvement": study_plan["expected_score_improvement"],
            "rationale": study_plan["rationale"]
        }
    
    execution_log = state.get("execution_log", []) + [{
        "agent": "Finalizer",
        "action": "response_prepared",
        "summary": response,
        "timestamp": __import__("time").time()
    }]
    
    return {
        **state,
        "response_message": state.get("response_message", "Plan generation completed successfully"),
        "plan_json": state.get("plan_json"),
        "execution_log": execution_log
    }


def build_graph() -> StateGraph:
    """
    Build the complete USMLE Agentic Graph.
    
    Graph Structure:
    START -> Diagnostician -> KnowledgeManager -> ResourceOptimizer -> Scheduler -> Conditional Edge
                                                                                          ├──> HumanReview -> Finalize -> END
                                                                                          └──> Finalize -> END
    """
    logger.info("Building USMLE Agentic Graph...")

    # Create state graph with memory for checkpointing
    workflow = StateGraph(AgentState)

    # Add nodes (4 agents)
    workflow.add_node("diagnostician", diagnostician_node)
    workflow.add_node("knowledge_manager", knowledge_manager_node)
    workflow.add_node("resource_optimizer", resource_optimizer_node)
    workflow.add_node("scheduler", scheduler_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("finalize", finalize_node)
    
    # Set entry point
    workflow.set_entry_point("diagnostician")
    
    # Define edges
    workflow.add_edge("diagnostician", "knowledge_manager")
    workflow.add_edge("knowledge_manager", "resource_optimizer")
    workflow.add_edge("resource_optimizer", "scheduler")
    
    # Conditional edge from scheduler
    workflow.add_conditional_edges(
        "scheduler",
        should_review,
        {
            "review": "human_review",
            "finalize": "finalize"
        }
    )
    
    # Review always goes to finalize
    workflow.add_edge("human_review", "finalize")
    workflow.add_edge("finalize", END)
    
    logger.info("USMLE Agentic Graph built successfully")
    return workflow


def create_compiled_graph():
    """Create and compile the graph with memory checkpointing."""
    workflow = build_graph()
    
    # Add memory for state persistence across turns
    memory = MemorySaver()
    
    compiled = workflow.compile(checkpointer=memory)
    logger.info("Graph compiled with memory checkpointing")
    
    return compiled


# Module-level compiled graph instance
graph = create_compiled_graph()
