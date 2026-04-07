# System Architecture Overview

The Agentic USMLE system implements a **stateful multimodal multi-agent graph** where specialized AI agents communicate through a typed state object.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Application                                     │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         API Routes (REST)                                 │   │
│  │   /assess  /students/{id}/profile  /students/{id}/knowledge              │   │
│  └────────────────────────────────┬─────────────────────────────────────────┘   │
│                                   │                                              │
│  ┌────────────────────────────────▼─────────────────────────────────────────┐   │
│  │                     LangGraph State Graph                                 │   │
│  │                                                                           │   │
│  │  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────┐          │   │
│  │  │Diagnostician│─▶│Knowledge Manager │─▶│Resource Optimizer  │          │   │
│  │  │ (Node A)    │  │   (Node B)       │  │  (Node C)          │          │   │
│  │  └─────────────┘  └──────────────────┘  │  (Multimodal RAG)  │          │   │
│  │                                         └─────────┬──────────┘          │   │
│  │                                                   │                      │   │
│  │  ┌────────────────────────────────────────────────▼──────────────┐     │   │
│  │  │                  Adaptive Scheduler (Node D)                   │     │   │
│  │  └───────────────────────────────────────┬───────────────────────┘     │   │
│  │                                          │                             │   │
│  │          ┌───────────────────────────────┼──────────────────┐         │   │
│  │          ▼                               │                  │         │   │
│  │  ┌─────────────┐                         │                  │         │   │
│  │  │Human Review │ (conditional)           │                  │         │   │
│  │  └──────┬──────┘                         │                  │         │   │
│  │         │                                ▼                  │         │   │
│  │         │                          ┌───────────┐            │         │   │
│  │         │◀─────────────────────────│ Finalize  │◀───────────┘         │   │
│  │         │                          └───────────┘                      │   │
│  └─────────┼─────────────────────────────────────────────────────────────┘   │
│            │                                                                 │
│  ┌─────────▼────────────────────────────────────────────────────────────┐   │
│  │                        Supabase Database                              │   │
│  │  students | knowledge | plans | logs | agent_executions              │   │
│  │  multimodal_resources (text/img embeddings) | student_uploads         │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Four-Agent Design

| Agent | Responsibility | Input | Output |
|-------|---------------|-------|--------|
| **A: Diagnostician** | Parse performance reports | Raw report text | Structured assessment |
| **B: Knowledge Manager** | Maintain knowledge vectors | Diagnostic + performance | Updated proficiencies |
| **C: Resource Optimizer** | Multimodal RAG retrieval | Knowledge state + topics | Resource recommendations across text, images, PDFs, video, audio |
| **D: Adaptive Scheduler** | Generate study plans | Knowledge + resources | Multimodal study plan |

## Multimodal RAG Pipeline

The Resource Optimizer (Agent C) implements a 4-stage retrieval pipeline:

```
1. Topic Scoring → Score all 45+ resources by topic match
2. Modality Balancing → Ensure text + image + video + qbank coverage
3. Constraint Filtering → Filter by time, learning style, IMG status
4. Ranking → Sort by combined relevance (topic + tier + ratings + popularity)
```

### Supported Modalities

| Modality | Examples | Embedding Model | Dimensions |
|----------|---------|----------------|------------|
| **Text** | First Aid chapters, UWorld explanations | OpenAI ada-002 | 1536 |
| **Images** | Pathology slides, ECG strips, radiographs, diagrams | CLIP ViT-L/14 | 768 |
| **PDFs** | NBME reports, study guides, practice exams | OpenAI ada-002 (extracted text) | 1536 |
| **Video** | Pathoma, B&B lectures with timestamps | OpenAI ada-002 (metadata/transcripts) | 1536 |
| **Audio** | Podcast episodes, lecture recordings | OpenAI ada-002 (transcripts) | 1536 |

## Design Principles

### 1. Stateful Orchestration
- Memory checkpointing via LangGraph's `MemorySaver`
- Database persistence for all student data and agent outputs
- Execution logging for debugging and research

### 2. Agent Specialization
Each agent has a narrow, well-defined responsibility enabling independent optimization and evaluation.

### 3. Conditional Routing
Intelligent branching routes low-confidence or high-risk students to human review.

### 4. Fallback Mechanisms
Every agent has a fallback (mock diagnostic, heuristic plans, text-only resources) ensuring reliability.

### 5. IMG Optimization
Automatic boosting of IMG-specific resources (US healthcare system, lab values, clinical context) for identified IMG students.

## Module Structure

```
src/
├── agents/
│   ├── state.py              # TypedDict state definitions
│   ├── diagnostician.py      # Node A: Report parsing (Groq/LLM)
│   ├── knowledge_manager.py  # Node B: Knowledge tracking (Supabase)
│   ├── resource_optimizer.py # Node C: Multimodal RAG (45+ resources)
│   ├── scheduler.py          # Node D: Plan generation (interleaved + spaced)
│   ├── graph_builder.py      # LangGraph assembly (4 agents + review)
│   └── main.py               # CLI and async entry point
├── api/
│   ├── app.py                # FastAPI application factory
│   ├── routes.py             # REST endpoints
│   └── schemas.py            # Pydantic models
└── database/
    ├── client.py             # Supabase client
    ├── schema.sql            # Database schema (with pgvector)
    └── migrations/           # SQL migrations
```
