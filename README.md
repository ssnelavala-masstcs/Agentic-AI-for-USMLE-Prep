# Agentic AI for Personalized USMLE Study Planning

> **Multimodal Multi-Agent Adaptive Learning for International Medical Graduates**

[![Build Research Paper](https://github.com/stanley-nelavala/Agentic-AI-for-USMLE-Prep/actions/workflows/latex_build.yml/badge.svg)](https://github.com/stanley-nelavala/Agentic-AI-for-USMLE-Prep/actions/workflows/latex_build.yml)
[![Deploy User Guide](https://github.com/stanley-nelavala/Agentic-AI-for-USMLE-Prep/actions/workflows/docs_deploy.yml/badge.svg)](https://github.com/stanley-nelavala/Agentic-AI-for-USMLE-Prep/actions/workflows/docs_deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

This project implements a **multimodal multi-agent AI system** that creates personalized, adaptive USMLE study plans for International Medical Graduates (IMGs). Unlike static AI tutoring systems, our platform maintains persistent knowledge vectors, retrieves relevant resources across 5 modalities (text, images, PDFs, video, audio), and dynamically adjusts study schedules based on student performance trajectories.

### Key Innovation

**Multimodal Agentic Loops > Static RAG > Text-Only Systems**

Our system:
- 🧠 **Diagnoses** strengths/weaknesses from NBME/UWorld reports
- 📊 **Tracks** knowledge vectors persistently across sessions  
- 🔍 **Retrieves** resources across 5 modalities using RAG (text, images, PDFs, video, audio)
- 📅 **Generates** evidence-based study plans with specific resource recommendations
- 🔄 **Adapts** plans when performance changes

## Architecture

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

### Multimodal RAG

The Resource Optimizer retrieves across 5 modalities:

| Modality | Examples | Count |
|----------|---------|-------|
| **Text** | First Aid chapters, UWorld explanations, IMG guides | 12 |
| **Images** | Pathology slides, ECG strips, radiographs, diagrams, tables | 8 |
| **PDFs** | NBME reports, USMLE outlines, practice exams | 6 |
| **Video** | Pathoma (Dr. Sattar), B&B (Dr. Ryan), SketchyMedical | 12 |
| **Audio** | USMLE podcasts, Divine Intervention episodes | 4 |
| **IMG-specific** | US healthcare system, lab values, ECFMG guide | 5 |

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Agent Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) 0.2+ |
| **LLM Inference** | [Groq](https://groq.com/) (Llama-3.1-70B) |
| **Multimodal RAG** | Custom engine (OpenAI ada-002 + CLIP ViT-L/14) |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) |
| **Database + Vectors** | [Supabase](https://supabase.com/) (PostgreSQL + pgvector) |
| **Documentation** | [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) |
| **CI/CD** | GitHub Actions (LaTeX + Docs auto-deploy) |

## Quick Start

### 1. Installation

```bash
git clone https://github.com/stanley-nelavala/Agentic-AI-for-USMLE-Prep.git
cd Agentic-AI-for-USMLE-Prep
pip install -r requirements.txt
cp .env.example .env  # Edit with your API keys
```

### 2. Database Setup

Run the SQL schema in your Supabase SQL editor:
- `src/database/schema.sql` - Complete schema with pgvector support
- `src/database/migrations/001_initial_schema.sql` - Migrations

### 3. Run Assessment

```bash
# Via CLI
python -m src.agents.main --student-id IMG001 --json

# Via API
uvicorn src.api.app:app --reload
curl -X POST http://localhost:8000/api/v1/assess \
  -H "Content-Type: application/json" \
  -d '{"student_id": "IMG001", "plan_days": 7}'
```

📖 **Full documentation**: [docs/](docs/index.md) or hosted at GitHub Pages (auto-deployed)

## Repository Structure

```
├── .github/workflows/       # CI/CD automation
│   ├── latex_build.yml      # Auto-compiles research paper PDF
│   └── docs_deploy.yml      # Auto-deploys documentation
├── src/                     # Core application
│   ├── agents/              # LangGraph nodes (4 agents)
│   │   ├── diagnostician.py      # Node A: Report parsing
│   │   ├── knowledge_manager.py  # Node B: Knowledge tracking
│   │   ├── resource_optimizer.py # Node C: Multimodal RAG
│   │   ├── scheduler.py          # Node D: Plan generation
│   │   ├── graph_builder.py      # LangGraph assembly
│   │   └── main.py               # CLI entry point
│   ├── api/                 # FastAPI backend
│   │   ├── app.py                # Application factory
│   │   ├── routes.py             # REST endpoints
│   │   └── schemas.py            # Pydantic models
│   └── database/            # Supabase + pgvector
│       ├── client.py             # Database client
│       ├── schema.sql            # Schema with multimodal tables
│       └── migrations/           # SQL migrations
├── paper/                   # Research publication
│   ├── main.tex             # LaTeX source (JMIR format)
│   ├── sections/            # Paper sections
│   └── references.bib       # Bibliography (2024-2026 citations)
├── docs/                    # User documentation
│   ├── getting-started/     # Installation & setup
│   ├── architecture/        # System design + multimodal RAG
│   ├── api/                 # API reference
│   ├── research/            # Researcher's handbook
│   └── students/            # Student onboarding guide
├── evaluation/              # User study analysis scripts
├── data/                    # Sample datasets + persona profiles
│   ├── sample_report.csv         # Student profiles
│   ├── sample_performance.csv    # Session performance
│   ├── persona_profiles.yaml     # 5 IMG personas (Blessie's)
│   └── gold_standard_plans.md    # Benchmark plans
├── mkdocs.yml               # Documentation config
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Research Paper

This system is documented in a research paper targeting **JMIR Medical Education**:

> **Title**: Agentic AI for Personalized USMLE Study Planning: A Multimodal Multi-Agent Adaptive Learning System for International Medical Graduates

The paper covers:
- Novel four-agent architecture with multimodal RAG
- Resource database across text, images, PDFs, video, and audio
- Evidence-based learning strategies (interleaving, spaced repetition)
- Pilot user study with IMG students
- Technical evaluation and clinical validation

📄 **LaTeX source**: [`paper/`](paper/)  
🔧 **Auto-compiles**: Push to `main` → PDF artifact in GitHub Actions

## Evidence-Based Learning Strategies

The system implements three proven learning science principles:

### 1. Interleaved Practice
Mixes different subjects within each day (25-40% better retention vs. blocked practice)  
*Source: Rohrer & Taylor, 2007*

### 2. Spaced Repetition
Reviews material at expanding intervals (1, 3, 7, 14 days)  
*Source: Cepeda et al., 2008*

### 3. Active Recall
Requires 20-40 practice questions per study block (50% better retention vs. restudying)  
*Source: Karpicke & Roediger, 2008*

## Multimodal Resource Examples

### What the system recommends for "Heart Failure":

| Modality | Resource | Specifics |
|----------|----------|-----------|
| **Text** | First Aid pp. 265-288 | Cardiovascular chapter |
| **Text** | UWorld Explanations | 80 cardiology questions |
| **Image** | Pathoma Pathology Slides | MI timeline (days 1-7 histology) |
| **Image** | ECG Collection | AFib, VTach, heart block strips |
| **Image** | CXR Radiographs | Cardiomegaly, pulmonary edema |
| **Video** | Pathoma Cardiovascular | Dr. Sattar, 15:00-30:00 MI pathology |
| **Video** | B&B Cardiovascular | Dr. Ryan, PV loops, murmurs |
| **PDF** | NBME Practice | Timed cardiology block |
| **Audio** | High Yield Podcast | Heart failure review episode |

### What the system recommends for IMG students:

| Resource | Addresses |
|----------|-----------|
| US Healthcare System Guide | Insurance (HMO/PPO/Medicare/Medicaid), referrals |
| US Lab Values Table | Reference ranges (may differ from international) |
| ECFMG IMG Guide | Registration, clinical experience requirements |
| NBME Score Interpretation | How to read official score reports |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/assess` | Run complete assessment pipeline |
| `GET` | `/api/v1/students/{id}/profile` | Get student profile |
| `GET` | `/api/v1/students/{id}/knowledge` | Get knowledge vector |
| `GET` | `/api/v1/students/{id}/plans` | Get study plans |
| `GET` | `/api/v1/health` | Health check |

📚 **Interactive docs**: `http://localhost:8000/docs` (after starting server)

## For Researchers

### Reproducing Results

```bash
# Install dependencies
pip install -r requirements.txt

# Run technical evaluation (100 test runs)
python evaluation/technical_evaluation.py

# Compile paper
cd paper && latexmk -pdf main.tex
```

### Extending the System

1. **Add knowledge areas**: Insert into `knowledge_areas` table
2. **Add resources**: Extend `MULTIMODAL_DATABASE` in `resource_optimizer.py`
3. **Customize agents**: Modify prompts in `src/agents/`
4. **Adjust learning strategies**: Update constants in `scheduler.py`
5. **Add new agents**: Create node function and add to `graph_builder.py`

### Citation

```bibtex
@misc{nelavala2026agentic,
  title={Agentic AI for Personalized USMLE Study Planning},
  author={Nelavala, Stanley Sujith},
  year={2026},
  url={https://github.com/stanley-nelavala/Agentic-AI-for-USMLE-Prep}
}
```

## For IMG Students

🎓 **Want to use this for your USMLE prep?**

1. Read the [Student Onboarding Guide](docs/students/onboarding.md)
2. Prepare your NBME/UWorld performance data
3. Contact the research team to participate in the pilot study
4. Receive personalized multimodal study plans updated weekly

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
black src/
ruff check src/
```

### Local Development

```bash
uvicorn src.api.app:app --reload --port 8000
```

## Team

- **Stanley Sujith Nelavala** - Technical Lead & Primary Researcher
- **Blessie** - Clinical Advisor & IMG Education Specialist

## Ethics & Privacy

- ✅ Student data protected by Supabase Row Level Security
- ✅ Multimodal resource recommendations are transparent and traceable
- ✅ Human-in-the-loop review for high-stakes decisions
- ✅ Full execution traceability logged to database
- ✅ Open-source implementation for transparency
- ✅ IRB approval obtained for user study

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Acknowledgments

- IMG students who participated in pilot testing
- LangGraph and Supabase open-source communities
- Learning science researchers whose work informed our strategies
- Dr. Sattar (Pathoma), Dr. Ryan (Boards & Beyond), SketchyMedical for educational resources referenced by this system

---

**Status**: 🚀 Active Development | **Last Updated**: April 2026
