# Evaluation Results

This directory contains evaluation results from technical and user studies.

## Files Generated

- `evaluation_results_*.json` - Technical evaluation runs (100 iterations)
- `score_improvement.png` - Visualization of pre/post score changes
- `user_study_analysis.ipynb` - Jupyter notebook with full analysis

## Running Evaluations

### Technical Evaluation

```bash
python evaluation/technical_evaluation.py
```

Outputs:
- Success rate
- Execution time statistics
- Component generation rates
- Full results JSON

### User Study Analysis

After collecting user study data:

```bash
jupyter notebook evaluation/user_study_analysis.ipynb
```

## Metrics Tracked

| Metric | Target | Description |
|--------|--------|-------------|
| Success Rate | > 95% | Pipeline completion without errors |
| Mean Execution Time | < 10s | Total pipeline time |
| Diagnostic Accuracy | > 80% | Correct weak area identification |
| Plan Quality | > 0.8/1.0 | Expert rubric score |
