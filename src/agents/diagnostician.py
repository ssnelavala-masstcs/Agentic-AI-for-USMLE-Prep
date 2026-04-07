"""
Diagnostician Agent - Node A in the LangGraph.

Responsibilities:
1. Parse NBME/UWorld score reports using Groq/Llama-3
2. Identify weak and strong knowledge areas
3. Calculate knowledge gaps with severity scores
4. Recommend focus areas for the scheduler

Uses structured prompting with few-shot examples for consistent output.
"""

import json
import logging
import time
from typing import Dict, Any, List
from groq import Groq
from dotenv import load_dotenv
import os

from src.agents.state import AgentState, DiagnosticResult

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

DIAGNOSTIC_SYSTEM_PROMPT = """You are an expert USMLE Diagnostician AI specializing in analyzing NBME and UWorld performance reports for International Medical Graduates (IMGs).

Your task is to parse student performance data and identify:
1. Overall performance metrics (NBME score, UWorld percentile)
2. Weak areas that need immediate intervention (proficiency < 50%)
3. Strong areas that can be maintained with spaced review (proficiency > 75%)
4. Specific knowledge gaps with severity scores (0.0 to 1.0)
5. Recommended focus areas ordered by priority

USMLE Step 1 Subject Weights (approximate):
- Pathology: 8-10%
- Physiology: 6-8%
- Pharmacology: 6-8%
- Microbiology: 5-7%
- Biochemistry: 5-7%
- Anatomy: 4-6%
- Behavioral Sciences: 3-5%
- Biostatistics/Epidemiology: 3-5%

CRITICAL RULES:
- Be specific in identifying subtopic-level gaps (e.g., not just "Cardiology" but "Heart Failure pathophysiology")
- Consider IMG-specific challenges (e.g., US healthcare system familiarity, clinical exposure gaps)
- Severity scores should reflect the gap from competency threshold (60%)
- Return ONLY valid JSON with the exact schema specified

Output Schema:
{
    "student_id": "string",
    "nbme_score": int or null,
    "uworld_percentile": float or null,
    "weak_areas": ["area1", "area2", ...],
    "strong_areas": ["area1", "area2", ...],
    "knowledge_gaps": [
        {"topic": "specific topic", "severity": 0.0-1.0, "subtopics": ["sub1", "sub2"]}
    ],
    "recommended_focus": ["priority1", "priority2", ...],
    "confidence_scores": {"area": 1.0-5.0},
    "raw_report": "summary of input"
}"""


def parse_diagnostic_report(report_text: str, student_id: str) -> DiagnosticResult:
    """
    Parse a student's performance report using LLM.
    
    Args:
        report_text: Raw text from NBME/UWorld report
        student_id: Student identifier
        
    Returns:
        DiagnosticResult with parsed assessment
    """
    if not groq_client:
        logger.warning("Groq client not initialized, returning mock diagnostic")
        return _mock_diagnostic(student_id, report_text)
    
    prompt = f"""Analyze the following USMLE performance report for student {student_id}:

{report_text}

Return your analysis as JSON matching the specified schema."""

    try:
        start_time = time.time()
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": DIAGNOSTIC_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        exec_time = (time.time() - start_time) * 1000
        
        result = json.loads(response.choices[0].message.content)
        result["student_id"] = student_id
        
        logger.info(f"Diagnostic analysis completed in {exec_time:.0f}ms for {student_id}")
        return DiagnosticResult(**result)
        
    except Exception as e:
        logger.error(f"Diagnostic parsing failed: {e}")
        return _mock_diagnostic(student_id, report_text)


def _mock_diagnostic(student_id: str, report_text: str) -> DiagnosticResult:
    """Fallback mock diagnostic for testing without API access."""
    return DiagnosticResult(
        student_id=student_id,
        nbme_score=195,
        uworld_percentile=52.0,
        weak_areas=["Cardiology", "Biochemistry", "Pharmacology"],
        strong_areas=["Anatomy", "Physiology"],
        knowledge_gaps=[
            {"topic": "Heart Failure", "severity": 0.7, "subtopics": ["Systolic dysfunction", "Drug management"]},
            {"topic": "Enzyme Kinetics", "severity": 0.6, "subtopics": ["Michaelis-Menten", "Inhibition patterns"]},
            {"topic": "Autonomic Pharmacology", "severity": 0.55, "subtopics": ["Receptor subtypes", "Drug classifications"]}
        ],
        recommended_focus=["Cardiology - Heart Failure", "Biochemistry - Enzyme Kinetics", "Pharmacology - Autonomic Drugs"],
        confidence_scores={"Cardiology": 2.5, "Biochemistry": 2.8, "Anatomy": 4.0, "Physiology": 4.2, "Pharmacology": 3.0},
        raw_report=report_text[:500]
    )


def diagnostician_node(state: AgentState) -> AgentState:
    """
    LangGraph node wrapper for the Diagnostician agent.
    
    Extracts input from state, runs diagnostic analysis, and returns updated state.
    """
    student_id = state["student_external_id"]
    report = state.get("input_report", "")
    
    if not report:
        report = "No report provided. Using baseline assessment."
    
    logger.info(f"[Diagnostician] Analyzing performance for student {student_id}")
    
    diagnostic = parse_diagnostic_report(report, student_id)
    
    execution_log_entry = {
        "agent": "Diagnostician",
        "action": "parse_performance_report",
        "student_id": student_id,
        "weak_areas_found": len(diagnostic["weak_areas"]),
        "timestamp": time.time()
    }
    
    return {
        **state,
        "diagnostic": diagnostic,
        "execution_log": state.get("execution_log", []) + [execution_log_entry]
    }
