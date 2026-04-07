# Evaluation Framework

Scripts and methodology for analyzing system performance and user study data.

## Technical Evaluation

### Pipeline Execution Tests

Run the evaluation suite:

```bash
python evaluation/technical_evaluation.py
```

This script:
1. Generates 100 simulated student profiles
2. Runs the complete agent pipeline for each
3. Collects execution metrics
4. Outputs summary statistics

### Metrics Collected

| Metric | Description | Target |
|--------|-----------|--------|
| `execution_time_ms` | Total pipeline time | < 10,000ms |
| `success_rate` | Percentage of successful runs | > 95% |
| `diagnostic_accuracy` | Weak area identification accuracy | > 80% |
| `plan_quality` | Rubric score (expert review) | > 0.8/1.0 |

## User Study Analysis

### Pre/Post Score Comparison

```python
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

# Load data
data = pd.read_csv("data/user_study_results.csv")

# Paired t-test
t_stat, p_value = stats.ttest_rel(data['post_score'], data['pre_score'])

# Effect size (Cohen's d)
cohen_d = (data['post_score'].mean() - data['pre_score'].mean()) / data['pre_score'].std()

print(f"t({len(data)-1}) = {t_stat:.2f}, p = {p_value:.3f}")
print(f"Cohen's d = {cohen_d:.2f}")
```

### Visualization

```python
# Score trajectory
plt.figure(figsize=(10, 6))
plt.scatter(data['pre_score'], data['post_score'], alpha=0.7)
plt.plot([140, 260], [140, 260], 'r--', alpha=0.5)  # Diagonal
plt.xlabel('Pre-study NBME Score')
plt.ylabel('Post-study NBME Score')
plt.title('Score Improvement')
plt.savefig('evaluation/score_improvement.png')
```

### Qualitative Analysis

Interview themes:

```python
# Example theme coding
themes = {
    "Plan Helpfulness": ["The plan told me exactly what to study", "I never would have mixed these topics"],
    "Personalization": ["It knew my weak areas", "Felt tailored to my needs"],
    "Usability": ["API was clear", "Need better UI"],
    "Recommendation": ["Would tell my friends", "Better than my old schedule"]
}
```

## Rubric Scoring

### Plan Quality Rubric (Blessie's Framework)

Score each criterion 0-1:

| Criterion | 0 (Poor) | 0.5 (Partial) | 1 (Excellent) |
|-----------|----------|---------------|---------------|
| Weak area prioritization | Ignores weak areas | Some focus on weak areas | Heavy focus on weakest topics |
| Interleaving quality | All blocked practice | Some mixing | Optimal interleaving |
| Spaced repetition | No review scheduling | Review present but irregular | Evidence-based intervals |
| IMG appropriateness | Generic advice | Some IMG consideration | Addresses IMG-specific gaps |
| Feasibility | Unrealistic hours | Mostly feasible | Well-calibrated to student |

### Inter-Rater Reliability

If multiple experts score plans:

```python
from scipy.stats import pearsonr

rater1 = [0.9, 0.8, 0.95, ...]
rater2 = [0.85, 0.82, 0.90, ...]

correlation, p_value = pearsonr(rater1, rater2)
print(f"Inter-rater reliability: r = {correlation:.2f}")
```

## Statistical Power

For the pilot study (n=10-20):

- **Effect size detectable**: d = 0.8 (large) with n=15, α=0.05, power=0.80
- **Recommendation**: Treat pilot as exploratory; definitive RCT needs n=100+

## Reporting Results

Follow JMIR guidelines:

1. Report exact p-values (not just < 0.05)
2. Include confidence intervals for effect sizes
3. Describe missing data
4. Report both statistical and practical significance

## Example Report

```markdown
## Results

### Primary Outcome

Students improved by an average of 12.3 points (SD = 8.5) on NBME practice exams after 4 weeks of agentic-guided study, t(14) = 5.42, p < 0.001, 95% CI [7.8, 16.8]. The effect size was large (Cohen's d = 1.45).

### Secondary Outcomes

- Average system usage: 4.2 sessions/week (SD = 1.8)
- Plans generated: 3.1 per student (SD = 1.2)
- Plan helpfulness rating: 4.2/5.0 (SD = 0.6)

### Qualitative Themes

Three major themes emerged:
1. **Structured guidance** (12/15 participants): "Finally knew what to study each day"
2. **Weak area focus** (10/15): "Made me study things I was avoiding"
3. **Confidence building** (8/15): "Seeing my predicted score go up helped"
```
