# USMLE Agentic AI System

> **Multimodal Multi-Agent Adaptive Learning for USMLE Preparation**

Welcome to the documentation for the Agentic AI USMLE Study Planning System—an intelligent, adaptive tutoring platform built with LangGraph, FastAPI, Supabase/pgvector, and multimodal RAG.

## What is This System?

This project implements a **multimodal multi-agent AI orchestration system** that:

1. **Diagnoses** student strengths and weaknesses from NBME/UWorld performance reports
2. **Tracks** knowledge vectors persistently across study sessions
3. **Retrieves** relevant resources across 5 modalities (text, images, PDFs, video, audio) using RAG
4. **Generates** adaptive, evidence-based study plans with specific resource recommendations

Unlike static AI tutoring systems, this platform maintains state, retrieves across modalities, and adapts over time—creating truly personalized learning experiences for International Medical Graduates (IMGs).

## Quick Links

- **[Installation Guide](getting-started/installation.md)** - Set up the system
- **[Quick Start](getting-started/quickstart.md)** - Run your first assessment
- **[Architecture Overview](architecture/overview.md)** - System design including multimodal RAG
- **[Research Paper](https://github.com/stanley-nelavala/Agentic-AI-for-USMLE-Prep/paper)** - LaTeX source for JMIR submission

## System Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────────┐     ┌───────────────────┐
│ Diagnostician │────▶│ Knowledge Manager │────▶│ Resource Optimizer  │────▶│ Adaptive Scheduler │
│  (Groq/LLM)  │     │  (Supabase DB)   │     │  (Multimodal RAG)   │     │  (LangGraph Node)  │
└─────────────┘     └──────────────────┘     └──────────────────────┘     └───────────────────┘
                                                                                       │
                                                                                       ▼
                                                                              ┌───────────────────┐
                                                                              │   Human Review    │
                                                                              │  (Conditional)    │
                                                                              └───────────────────┘
```

## Key Features

- **Stateful Agentic Graph** - LangGraph orchestration with memory checkpointing
- **Multimodal RAG** - Retrieval across text, images (pathology, ECG, radiographs), PDFs, video (with timestamps), and audio
- **Evidence-Based Learning** - Interleaved practice, spaced repetition, active recall
- **Persistent Knowledge Tracking** - Supabase/pgvector-backed student knowledge vectors
- **IMG Optimization** - Automatic boosting of IMG-specific resources (US healthcare system, lab values)
- **Human-in-the-Loop** - Conditional review routing for clinical oversight
- **RESTful API** - FastAPI with OpenAPI/Swagger documentation
- **Open Source** - Fully documented for reproducible research

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Agent Orchestration | LangGraph 0.2+ |
| LLM Inference | Groq (Llama-3.1-70B) |
| Multimodal RAG | Custom engine (OpenAI ada-002 + CLIP ViT-L/14) |
| Backend API | FastAPI |
| Database + Vectors | Supabase (PostgreSQL + pgvector) |
| Documentation | MkDocs Material |
| CI/CD | GitHub Actions |

## Citation

If you use this system in your research, please cite:

```bibtex
@misc{nelavala2026agentic,
  title={Agentic AI for Personalized USMLE Study Planning},
  author={Nelavala, Stanley Sujith},
  year={2026},
  url={https://github.com/stanley-nelavala/Agentic-AI-for-USMLE-Prep}
}
```

## License

MIT License - See LICENSE file for details.
