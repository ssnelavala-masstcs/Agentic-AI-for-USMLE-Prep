# Multimodal RAG Documentation

Details of the multimodal Resource Optimizer system.

## Overview

The Resource Optimizer is a Retrieval-Augmented Generation (RAG) engine that retrieves USMLE study resources across 5 modalities: text, images, PDFs, video, and audio.

## Resource Catalog

### Text Resources (12)

| Resource | Area | Pages | Hours |
|----------|------|-------|-------|
| First Aid - Cardiovascular | Cardiology | pp. 265-288 | 4.0 |
| First Aid - Biochemistry | Biochemistry | pp. 95-128 | 3.5 |
| First Aid - Ethics | Ethics | pp. 293-304 | 1.5 |
| UWorld Cardiology Explanations | Cardiology | - | 8.0 |
| UWorld Pharmacology Explanations | Pharmacology | - | 7.0 |
| US Healthcare System for IMGs | Ethics | - | 1.5 [IMG] |
| US Lab Values for IMGs | General | - | 1.0 [IMG] |

### Image Resources (8)

| Resource | Type | Description | Hours |
|----------|------|-------------|-------|
| Pathoma Cardiovascular Pathology | Pathology slides | Atherosclerosis, MI, valvular lesions | 2.0 |
| Pathoma Inflammation Images | Pathology slides | Granulomas, wound healing | 2.5 |
| ECG Arrhythmia Collection | ECG strips | AFib, VTach, heart blocks, WPW | 2.5 |
| Cardiovascular Radiographs | Radiographs | CXR: heart failure, edema, effusions | 1.5 |
| Metabolic Pathway Maps | Diagrams | Glycolysis, TCA, ETC maps | 2.0 |
| Pharmacology Drug Tables | Tables | Antiarrhythmics, antibiotics | 3.0 |

### PDF Resources (6)

| Resource | Purpose | Hours |
|----------|---------|-------|
| NBME Score Report Guide | Interpreting score reports | 0.5 [IMG] |
| USMLE Content Outline | Exam blueprint | 1.0 |
| IMG Guide to USMLE (ECFMG) | IMG preparation | 2.0 [IMG] |
| USMLE Free 120 | Practice questions | 4.0 |
| NBME Practice Forms 25-31 | Practice exams | 14.0 |

### Video Resources (12)

| Resource | Source | Duration | Key Timestamps | Hours |
|----------|--------|----------|----------------|-------|
| Pathoma General Pathology | Dr. Sattar | 180 min | 6 key segments | 3.0 |
| Pathoma Cardiovascular | Dr. Sattar | 65 min | 5 key segments | 1.5 |
| B&B Biochemistry | Dr. Ryan | 300 min | 7 key segments | 5.0 |
| B&B Cardiovascular Physiology | Dr. Ryan | 120 min | 6 key segments | 2.5 |
| Sketchy Micro Bacteriology | SketchyMedical | 240 min | 4 memory palaces | 4.0 |

### Audio Resources (4)

| Resource | Topic | Duration | Hours |
|----------|-------|----------|-------|
| High Yield Podcast - Cardiology | Cardiology review | 120 min | 2.0 |
| Divine Intervention - Pharmacology | Drug pearls | 90 min | 1.5 |

## Retrieval Pipeline

### Stage 1: Topic Scoring

Every resource is scored using:

```python
score = (
    5.0 if exact_area_match else
    3.0 if partial_area_match else 0
    + 3.0 if topic_in_description
    + 2.0 if topic_in_topic_field
    + sum(1.0 for matching_tag)
    + tier_bonus (0.5-2.5)
    + student_rating/5 * 1.5
    + 1.5 if img_specific and is_img_student
    + 0.5 if usage_count > 10
)
```

### Stage 2: Modality Balancing

Ensures at least one resource from each category:
- **Primary text**: Core reference (First Aid chapter or UWorld explanations)
- **Visual**: Image or diagram for visual learners
- **Video**: Lecture segment for conceptual understanding
- **QBank**: Practice questions for active recall
- **IMG**: IMG-specific resource when applicable

### Stage 3: Constraint Filtering

- Filters by available study time
- Respects learning style preferences
- Ensures tier minimums (at least "high-yield" quality)

### Stage 4: Ranking

Returns top resources sorted by combined relevance score.

## Embedding Strategy (Production)

### Text Embeddings
- **Model**: OpenAI text-embedding-ada-002
- **Dimensions**: 1536
- **Indexed with**: Supabase pgvector IVFFlat

### Image Embeddings
- **Model**: CLIP ViT-L/14
- **Dimensions**: 768
- **Indexed with**: Supabase pgvector IVFFlat

### Vector Search

```sql
-- Text similarity
SELECT * FROM multimodal_resources
ORDER BY text_embedding <=> query_embedding
LIMIT 10;

-- Image similarity
SELECT * FROM multimodal_resources
WHERE modality = 'image'
ORDER BY image_embedding <=> query_embedding
LIMIT 5;
```

## IMG-Specific Resources

These resources are boosted for IMG students:

| Resource | Addresses |
|----------|-----------|
| US Healthcare System Guide | Insurance types, referrals, prior auth |
| US Lab Values Table | Reference ranges that differ from international |
| NBME Score Report Guide | How to interpret official reports |
| ECFMG IMG Guide | Registration and requirements |
| USMLE Free 120 | Most representative practice questions |

## Extending the Database

Add new resources to `MULTIMODAL_DATABASE` in `resource_optimizer.py`:

```python
MultimodalResource(
    id="unique-id",
    name="Resource Name",
    source="Source Name",
    modality=Modality.TEXT,  # or IMAGE, PDF, VIDEO, AUDIO
    area="USMLE Area",
    topic="Specific Topic",
    description="What this covers",
    tier=ResourceTier.ESSENTIAL,
    content_text="Optional text content",
    page_range="pp. X-Y",  # for text
    image_type="pathology_slide",  # for images
    video_url="https://...",  # for video
    duration_minutes=60,  # for video/audio
    key_frames=["00:00 Topic 1", "30:00 Topic 2"],  # for video
    estimated_hours=2.0,
    student_rating=4.5,
    tags=["tag1", "tag2"],
    img_specific=True  # if IMG-specific
)
```

## Student Interaction Tracking

The system tracks which resources students actually use:

```sql
INSERT INTO student_resource_interactions (
    student_id, resource_id, interaction_type, 
    duration_minutes, rating, notes
) VALUES (...);
```

This data enables:
- Resource quality refinement based on actual usage
- Personalized recommendations ("students like you found this helpful")
- Engagement analytics for the research study
