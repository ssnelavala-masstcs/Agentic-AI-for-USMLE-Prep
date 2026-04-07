# Student Onboarding Guide

Welcome to the Agentic USMLE Study Planning System! This guide will help you get started.

## What is This System?

This is an **AI-powered study planning tool** designed specifically for International Medical Graduates (IMGs) preparing for USMLE Step 1.

Unlike commercial question banks that just give you practice questions, this system:

1. **Analyzes** your NBME/UWorld performance reports
2. **Identifies** your specific weak areas
3. **Creates** a personalized study schedule using evidence-based strategies
4. **Adapts** your plan based on your progress

## Who Should Use This?

- IMGs preparing for USMLE Step 1
- Students with baseline NBME scores between 160-220
- Anyone who wants a structured, adaptive study plan
- Students willing to share their performance data for research

## Getting Started

### Step 1: Provide Your Information

You'll need to share:

1. **Student ID**: A unique identifier (e.g., `IMG001`)
2. **NBME Score**: Your most recent practice exam score (if available)
3. **UWorld Percentile**: Your current UWorld performance percentile (if available)
4. **Target Exam Date**: When you plan to take the actual USMLE
5. **Daily Study Hours**: How many hours per day you can study

### Step 2: Upload Your Performance Report

You can provide:
- Text summary of your NBME/UWorld performance
- Specific weak/strong areas you're aware of
- Recent practice question session results

**Example report format:**

```
NBME 25 Score: 185
UWorld Percentile: 45%

Weak Areas:
- Cardiology: 60% correct on practice questions
- Biochemistry: 50% correct
- Pharmacology: 55% correct

Strong Areas:
- Anatomy: 80% correct
- Physiology: 75% correct

Available study time: 6 hours/day
Target exam date: September 15, 2026
```

### Step 3: Receive Your Study Plan

Within seconds, the system will generate:

1. **Diagnostic Assessment**: Analysis of your strengths/weaknesses
2. **Knowledge Profile**: Your current predicted USMLE score
3. **Study Plan**: A detailed 7-day schedule with specific topics and practice questions

## Understanding Your Study Plan

### Plan Structure

Your plan will include:

| Component | Description |
|-----------|-------------|
| **Study Blocks** | Individual study sessions (2-4 per day) |
| **Topics** | Specific topics to focus on (not just "Cardiology" but "Heart Failure") |
| **Practice Questions** | Number of questions to complete per block |
| **Review Type** | How to study: active recall, spaced repetition, interleaved, or full review |
| **Resources** | Recommended materials (UWorld, First Aid, Pathoma, etc.) |

### Example Day

```
Day 1: Monday, April 7, 2026

Block 1 (2.5 hours): Cardiology - Heart Failure
- Type: Active Recall
- Practice Questions: 30
- Resources: UWorld, First Aid, Pathoma

Block 2 (2.0 hours): Anatomy - Thorax
- Type: Interleaved
- Practice Questions: 20
- Resources: UWorld, Amboss

Block 3 (1.5 hours): Physiology - High-yield Review
- Type: Spaced Repetition
- Practice Questions: 12
- Resources: Anki, First Aid Rapid Review
```

### Every 3rd Day: Review Day

Every third day will be a comprehensive review day:
- Morning: Intensive review of your weakest area
- Afternoon: Mixed practice questions (simulates exam conditions)

## Evidence-Based Strategies Used

Your plan implements three proven learning strategies:

### 1. Interleaved Practice

Instead of studying one topic all day, your plan mixes different subjects. Research shows this improves long-term retention by 25-40%.

**Why?** It forces your brain to discriminate between different types of problems—exactly what the USMLE does.

### 2. Spaced Repetition

Review sessions are scheduled at optimal intervals to prevent forgetting. You'll review material just before you're about to forget it.

**Why?** The "forgetting curve" is steepest in the first few days. Spaced review flattens it.

### 3. Active Recall

Every block includes practice questions. Testing yourself is more effective than re-reading notes.

**Why?** Retrieval strengthens memory traces more than passive review.

## Tracking Your Progress

### Knowledge Vector

The system maintains a "knowledge vector" tracking your proficiency in each area:

```
Cardiology: 35% → 42% → 48% → 55%
Biochemistry: 40% → 45% → 50% → 52%
Anatomy: 75% → 76% → 78% → 80%
```

Watch your proficiencies increase over time!

### Predicted Score

Based on your knowledge state, the system predicts your USMLE score:

```
Week 1: 182
Week 2: 188
Week 3: 194
Week 4: 201  ← Passing threshold is ~196
```

## Providing Feedback

After using your plan for a few days, tell us:

1. **Was the plan helpful?** (1-5 scale)
2. **Did it address your weaknesses?** (Yes/Partial/No)
3. **Were the daily hours realistic?** (Yes/No)
4. **What would you change?** (Open feedback)

Your feedback helps improve the system for future students!

## Privacy & Data Use

- Your data is stored securely in Supabase
- Only you and the research team can access your data
- Individual scores are never shared publicly
- Aggregate data may be used in research publications (anonymized)

## Support

If you have questions or issues:

- **Technical issues**: Contact Stanley (technical lead)
- **Study advice**: Contact Blessie (clinical advisor)
- **General questions**: Check this documentation

## Next Steps

1. Review the [Using Your Plan Guide](using-plans.md) for tips
2. Run your first assessment via the API or CLI
3. Start following your generated plan
4. Report back after 1 week with your experience

Good luck with your USMLE preparation! 🎓
