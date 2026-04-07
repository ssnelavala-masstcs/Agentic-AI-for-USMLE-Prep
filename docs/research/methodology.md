# Researcher's Handbook: Methodology

This document describes the research methodology for evaluating the Agentic USMLE system.

## Research Questions

1. **RQ1**: Does agentic AI-generated study planning improve USMLE practice exam scores compared to self-directed study?
2. **RQ2**: How does the quality of LLM-generated plans compare to heuristic-based plans as evaluated by clinical experts?
3. **RQ3**: What is the feasibility and reliability of the agentic pipeline in production conditions?

## Study Design

### Phase 1: Technical Evaluation (Completed)

**Objective**: Validate system functionality and performance.

**Methods**:
- 100 test runs with simulated student data
- Measure execution time, success rate, plan quality
- Compare LLM vs. heuristic plan generation

**Metrics**:
- Pipeline execution time (target: < 10 seconds)
- Success rate (target: > 95%)
- Plan quality rubric score (target: > 0.8/1.0)

### Phase 2: Expert Review (In Progress)

**Objective**: Clinical validation of generated plans.

**Methods**:
- Blessie (clinical advisor) evaluates 30 plans using rubric
- Compare against manually created "gold standard" plans
- Qualitative feedback on plan appropriateness

**Rubric** (5 criteria, 0-1 scale each):
1. Weak area prioritization
2. Interleaving quality
3. Spaced repetition implementation
4. IMG-specific appropriateness
5. Feasibility (time allocation)

### Phase 3: Pilot User Study (Planned)

**Objective**: Real-world evaluation with IMG students.

**Participants**: 10-20 IMGs preparing for USMLE Step 1

**Inclusion Criteria**:
- IMG (non-US medical school graduate)
- Planning to take Step 1 within 6 months
- Baseline NBME score < 200
- Willing to use system for minimum 2 weeks

**Procedure**:
1. Pre-study: Baseline NBME practice exam
2. Weeks 1-2: Use system for study planning
3. Mid-study: Usage metrics collection
4. Weeks 3-4: Continue system use
5. Post-study: NBME practice exam, qualitative interview

**Outcome Measures**:
- **Primary**: NBME score change (pre vs. post)
- **Secondary**: System usage (sessions, plans generated)
- **Qualitative**: Plan helpfulness, personalization, usability

## Data Analysis

### Quantitative

```python
# Score improvement analysis
from scipy import stats

pre_scores = [175, 180, 170, ...]
post_scores = [185, 190, 182, ...]

t_stat, p_value = stats.ttest_rel(post_scores, pre_scores)
effect_size = (mean(post) - mean(pre)) / std(pre)
```

### Qualitative

Thematic analysis of interview transcripts:
1. Transcribe interviews
2. Open coding
3. Axial coding
4. Theme identification
5. Member checking

## Ethical Considerations

- **Informed consent**: Participants must understand study purpose and data usage
- **Data anonymization**: Remove PII before analysis
- **IRB approval**: Required before starting user study
- **Right to withdraw**: Participants can exit at any time

## Reproducibility

All code is open-source. To replicate:
1. Clone repository
2. Follow installation guide
3. Run evaluation scripts in `evaluation/`
4. Use sample data in `data/`

## Publication Target

**JMIR Medical Education**

- Impact Factor: 2.8
- Open access
- Focus on medical education technology
- Accepts mixed-methods studies

## Timeline

| Phase | Start | End | Status |
|-------|-------|-----|--------|
| Technical Evaluation | 2026-04-01 | 2026-04-07 | ✅ Complete |
| Expert Review | 2026-04-08 | 2026-04-20 | 🔄 In Progress |
| Pilot Recruitment | 2026-04-15 | 2026-05-01 | ⏳ Pending |
| Pilot Study | 2026-05-01 | 2026-06-01 | ⏳ Pending |
| Data Analysis | 2026-06-01 | 2026-06-15 | ⏳ Pending |
| Manuscript Writing | 2026-06-15 | 2026-07-01 | ⏳ Pending |
