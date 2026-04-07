# Database Documentation

The system uses Supabase (PostgreSQL + pgvector) for persistent storage with multimodal RAG support.

## Schema Overview

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `students` | Student profiles | external_id, name, learning_style |
| `knowledge_areas` | USMLE subject taxonomy | name, category, subtopics |
| `student_knowledge` | Knowledge vectors | student_id, area_id, proficiency_score, embedding (1536d) |
| `multimodal_resources` | Resource catalog | modality, area, text_embedding (1536d), image_embedding (768d) |
| `student_resource_interactions` | Usage tracking | student_id, resource_id, interaction_type, rating |
| `student_uploads` | Student documents | file_type, file_url, extracted_text, embedding |
| `performance_logs` | Session data | student_id, area, questions, accuracy |
| `study_plans` | Generated plans | student_id, plan_json, multimodal_enabled |
| `study_blocks` | Daily schedule | plan_id, day, area, resource_modalities |
| `agent_executions` | Execution traces | student_id, agent, input, output |

## Multimodal Resources Table

The core of the RAG system:

```sql
CREATE TABLE multimodal_resources (
    id UUID PRIMARY KEY,
    resource_id VARCHAR(50) UNIQUE,  -- e.g., "fa-txt-cardio"
    name VARCHAR(255),
    source VARCHAR(100),              -- "First Aid", "UWorld", "Pathoma"
    modality resource_modality,       -- text, pdf, image, video, audio
    area VARCHAR(100),
    topic VARCHAR(200),
    description TEXT,
    tier resource_tier,               -- essential, high-yield, supplementary, reference
    
    -- Content
    content_text TEXT,                -- Text content / transcript
    content_url TEXT,                 -- File path or URL
    page_range VARCHAR(50),           -- "pp. 265-280"
    timestamp_range VARCHAR(50),      -- "12:30-18:45"
    
    -- Embeddings
    text_embedding vector(1536),      -- OpenAI ada-002
    image_embedding vector(768),      -- CLIP ViT-L/14
    
    -- Image metadata
    image_type VARCHAR(50),           -- pathology_slide, ECG, radiograph, diagram, table
    image_description TEXT,
    
    -- Video metadata
    video_url TEXT,
    duration_minutes DECIMAL(5,1),
    key_frames TEXT[],                -- ["00:00 Topic 1", "30:00 Topic 2"]
    
    -- Engagement
    estimated_hours DECIMAL(3,1),
    student_rating DECIMAL(2,1),
    usage_count INTEGER,
    
    -- Tags
    tags TEXT[],
    img_specific BOOLEAN DEFAULT FALSE
);
```

## Vector Indexes

```sql
-- Text similarity (IVFFlat for approximate nearest neighbor)
CREATE INDEX idx_resources_text_embedding 
    ON multimodal_resources USING ivfflat (text_embedding vector_cosine_ops);

-- Image similarity
CREATE INDEX idx_resources_image_embedding 
    ON multimodal_resources USING ivfflat (image_embedding vector_cosine_ops);
```

## Row Level Security

RLS policies ensure data isolation:

```sql
-- Students can only access their own data
CREATE POLICY "Students can view own data" ON students
    FOR SELECT USING (auth.uid()::text = external_id);

-- Resource catalog is publicly readable
CREATE POLICY "Anyone can view resources" ON multimodal_resources
    FOR SELECT USING (true);

-- Students can track their resource interactions
CREATE POLICY "Students can insert own interactions" ON student_resource_interactions
    FOR INSERT WITH CHECK (student_id IN (
        SELECT id FROM students WHERE external_id = auth.uid()::text
    ));
```

## Student Uploads (Multimodal Inputs)

Students can upload:
- **PDFs**: NBME score reports, study guides
- **Images**: Pathology photos, ECG prints
- **Text**: Study notes, performance summaries

```sql
CREATE TABLE student_uploads (
    id UUID PRIMARY KEY,
    student_id UUID REFERENCES students(id),
    file_type VARCHAR(20),            -- pdf, image, text
    file_url TEXT,                    -- Supabase Storage URL
    file_name VARCHAR(255),
    extracted_text TEXT,              -- OCR/extracted content
    text_embedding vector(1536),      -- For RAG retrieval
    description TEXT,
    created_at TIMESTAMP
);
```

## Connection Management

```python
from src.database.client import supabase, get_supabase_client

# Direct use
supabase.table("multimodal_resources").select("*").eq("modality", "image").execute()

# FastAPI dependency
@app.get("/endpoint")
async def endpoint(db: Client = Depends(get_supabase_client)):
    db.table("students").select("*").execute()
```

## Vector Search (Production)

```python
# Generate query embedding
from openai import OpenAI
client = OpenAI()

query_embedding = client.embeddings.create(
    input="heart failure pathophysiology",
    model="text-embedding-ada-002"
).data[0].embedding

# Search Supabase
results = supabase.rpc('match_resources_text', {
    'query_embedding': query_embedding,
    'match_threshold': 0.7,
    'match_count': 10
}).execute()
```

## Seed Data

The schema includes:
- 10 USMLE knowledge areas with subtopics
- 13 sample multimodal resources across all modalities
- 5 IMG-specific resources flagged
