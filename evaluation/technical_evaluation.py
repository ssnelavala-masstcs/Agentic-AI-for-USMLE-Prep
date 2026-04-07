"""
Technical Evaluation Script for Agentic USMLE System.

Runs 100 test iterations and collects performance metrics.
Outputs summary statistics to evaluation/results/
"""

import asyncio
import time
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import statistics

from src.agents.main import run_student_assessment

# Create results directory
os.makedirs("evaluation/results", exist_ok=True)


def generate_mock_student(student_id: str) -> Dict[str, Any]:
    """Generate mock student data for testing."""
    import random
    
    nbme_score = random.randint(160, 220)
    uworld_percentile = random.randint(30, 80)
    
    weak_areas_options = ["Cardiology", "Biochemistry", "Pharmacology", "Neurology", "Microbiology"]
    strong_areas_options = ["Anatomy", "Physiology", "Pathology", "Ethics", "Preventive Medicine"]
    
    num_weak = random.randint(1, 3)
    num_strong = random.randint(1, 3)
    
    weak_areas = random.sample(weak_areas_options, num_weak)
    strong_areas = random.sample(strong_areas_options, num_strong)
    
    report = (
        f"Student {student_id} scored {nbme_score} on NBME practice exam, "
        f"{uworld_percentile}th percentile on UWorld. "
        f"Weak areas: {', '.join(weak_areas)}. "
        f"Strong areas: {', '.join(strong_areas)}."
    )
    
    return {
        "student_id": student_id,
        "report_text": report,
        "expected_weak": weak_areas,
        "expected_strong": strong_areas
    }


async def run_single_evaluation(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run pipeline for one student and collect metrics."""
    start_time = time.time()
    
    try:
        result = await run_student_assessment(
            student_id=student_data["student_id"],
            report_text=student_data["report_text"],
            requires_review=False
        )
        
        execution_time = (time.time() - start_time) * 1000  # ms
        
        return {
            "student_id": student_data["student_id"],
            "status": result["status"],
            "execution_time_ms": execution_time,
            "success": result["status"] in ["success", "completed_with_errors"],
            "diagnostic_found": result.get("diagnostic") is not None,
            "knowledge_state_found": result.get("knowledge_state") is not None,
            "plan_found": result.get("study_plan") is not None,
            "weak_areas_identified": len(result.get("diagnostic", {}).get("weak_areas", [])),
            "plan_blocks_generated": len(result.get("study_plan", {}).get("blocks", [])),
            "errors": result.get("errors", [])
        }
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return {
            "student_id": student_data["student_id"],
            "status": "error",
            "execution_time_ms": execution_time,
            "success": False,
            "error": str(e)
        }


async def run_full_evaluation(n_runs: int = 100):
    """Run complete evaluation suite."""
    print(f"Starting technical evaluation: {n_runs} runs")
    print("=" * 60)
    
    results: List[Dict[str, Any]] = []
    
    for i in range(1, n_runs + 1):
        student_id = f"EVAL{i:03d}"
        student_data = generate_mock_student(student_id)
        
        result = await run_single_evaluation(student_data)
        results.append(result)
        
        if i % 10 == 0:
            print(f"Completed {i}/{n_runs} runs...")
    
    # Calculate metrics
    success_count = sum(1 for r in results if r["success"])
    success_rate = (success_count / len(results)) * 100
    
    exec_times = [r["execution_time_ms"] for r in results if r["success"]]
    avg_time = statistics.mean(exec_times) if exec_times else 0
    median_time = statistics.median(exec_times) if exec_times else 0
    min_time = min(exec_times) if exec_times else 0
    max_time = max(exec_times) if exec_times else 0
    
    diagnostic_count = sum(1 for r in results if r.get("diagnostic_found"))
    knowledge_count = sum(1 for r in results if r.get("knowledge_state_found"))
    plan_count = sum(1 for r in results if r.get("plan_found"))
    
    total_blocks = sum(r.get("plan_blocks_generated", 0) for r in results)
    avg_blocks = total_blocks / success_count if success_count > 0 else 0
    
    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total Runs: {n_runs}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"\nExecution Time (successful runs only):")
    print(f"  Mean: {avg_time:.0f}ms")
    print(f"  Median: {median_time:.0f}ms")
    print(f"  Min: {min_time:.0f}ms")
    print(f"  Max: {max_time:.0f}ms")
    print(f"\nPipeline Components:")
    print(f"  Diagnostic generated: {diagnostic_count}/{n_runs} ({diagnostic_count/n_runs*100:.1f}%)")
    print(f"  Knowledge state updated: {knowledge_count}/{n_runs} ({knowledge_count/n_runs*100:.1f}%)")
    print(f"  Study plan generated: {plan_count}/{n_runs} ({plan_count/n_runs*100:.1f}%)")
    print(f"  Avg blocks per plan: {avg_blocks:.1f}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"evaluation/results/evaluation_{timestamp}.json"
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "n_runs": n_runs,
        "success_rate": success_rate,
        "execution_time": {
            "mean_ms": avg_time,
            "median_ms": median_time,
            "min_ms": min_time,
            "max_ms": max_time
        },
        "components": {
            "diagnostic": diagnostic_count,
            "knowledge_state": knowledge_count,
            "study_plan": plan_count
        },
        "avg_blocks_per_plan": avg_blocks,
        "individual_results": results
    }
    
    with open(results_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    print("=" * 60)
    
    return summary


if __name__ == "__main__":
    asyncio.run(run_full_evaluation(n_runs=100))
