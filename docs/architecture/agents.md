# Agents Documentation

## Four-Agent Architecture

| Agent | File | Purpose |
|-------|------|---------|
| A: Diagnostician | `src/agents/diagnostician.py` | Parse NBME/UWorld reports |
| B: Knowledge Manager | `src/agents/knowledge_manager.py` | Maintain knowledge vectors |
| C: Resource Optimizer | `src/agents/resource_optimizer.py` | Multimodal RAG retrieval |
| D: Adaptive Scheduler | `src/agents/scheduler.py` | Generate study plans |

## Agent C: Multimodal Resource Optimizer (RAG)

**File**: `src/agents/resource_optimizer.py`

### Responsibility

Retrieve and recommend relevant USMLE study resources across 5 modalities using a unified relevance scoring system.

### Supported Modalities

```python
class Modality(str, Enum):
    TEXT = "text"    # First Aid chapters, UWorld explanations
    PDF = "pdf"      # NBME reports, study guides, practice exams
    IMAGE = "image"  # Pathology slides, ECG strips, radiographs, diagrams
    VIDEO = "video"  # Pathoma, B&B lectures with timestamps
    AUDIO = "audio"  # Podcasts, lecture recordings
```

### MultimodalResource Data Model

Each resource includes:
- **Core fields**: id, name, source, modality, area, topic, description, tier
- **Content**: text content, file paths, page ranges, timestamps
- **Embeddings**: text_embedding (1536d), image_embedding (768d)
- **Image metadata**: image_type, image_description
- **Video metadata**: video_url, duration, key_frames
- **Engagement**: estimated_hours, student_rating, usage_count
- **Tags**: topic tags, img_specific flag

### Resource Database

45+ curated resources including:

| Modality | Count | Examples |
|----------|-------|---------|
| Text | 12 | FA chapters, UWorld explanations, IMG guides |
| Images | 8 | Pathology slides, ECG strips, metabolic maps, drug tables |
| PDFs | 6 | NBME reports, USMLE outline, Free 120, IMG guide |
| Video | 12 | Pathoma (Dr. Sattar), B&B (Dr. Ryan), SketchyMedical |
| Audio | 4 | High Yield Podcast, Divine Intervention |
| IMG-specific | 5 | US healthcare system, lab values, ECFMG guide |

### Retrieval Algorithm

```python
def retrieve(
    query_area: str,
    query_topic: str,
    max_results: int = 10,
    modalities: Optional[List[Modality]] = None,
    min_tier: ResourceTier = ResourceTier.SUPPLEMENTARY,
    img_specific_bonus: bool = False
) -> List[MultimodalResource]:
```

**Scoring components:**
1. Area match (+5.0 exact, +3.0 partial)
2. Topic match in description (+3.0) and topic field (+2.0)
3. Tag matches (+1.0 each)
4. Modality preference bonus (+2.0)
5. Tier priority (+0.5 to +2.5)
6. Student rating bonus (up to +1.5)
7. IMG-specific bonus (+1.5)
8. Usage popularity bonus (+0.5)

### Multimodal Set Retrieval

```python
def retrieve_multimodal_set(
    area: str,
    topic: str,
    target_hours: float,
    learning_style: Optional[str] = None,
    is_img_student: bool = False
) -> Dict[str, List[MultimodalResource]]:
```

Ensures balanced modality coverage:
1. **Text**: Always included (primary reference)
2. **Image**: Included for visual learners or when time allows
3. **Video**: Included for conceptual understanding
4. **QBank**: Always included for active recall
5. **IMG-specific**: Included for IMG students
6. **PDF**: Included if high-yield reference available

### Production Vector Search

Currently uses heuristic scoring. For production:

```python
# Text similarity search
text_results = supabase.rpc('match_resources_text', {
    'query_embedding': openai.Embedding.create(input=query, model="text-embedding-ada-002"),
    'match_threshold': 0.7,
    'count': 10
})

# Image similarity search
image_results = supabase.rpc('match_resources_image', {
    'query_embedding': clip_model.encode(image),
    'match_threshold': 0.6,
    'count': 5
})
```

### LangGraph Node

```python
def resource_optimizer_node(state: AgentState) -> AgentState:
    """Enhances study plan with multimodal resource recommendations."""
```

Adds to each block:
- `resources`: List of resource names
- `resource_details`: Dict mapping modality → resource list
- `resource_summary`: Human-readable summary
- `is_img_optimized`: Whether IMG resources were boosted
