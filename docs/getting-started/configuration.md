# Configuration Guide

Detailed configuration options for the Agentic USMLE system.

## Environment Variables

All configuration is managed through environment variables. See `.env.example` for the complete list.

### Required Variables

| Variable | Description | Example |
|----------|-----------|---------|
| `GROQ_API_KEY` | Groq API key for LLM inference | `gsk_abc123...` |
| `SUPABASE_URL` | Supabase project URL | `https://xyz.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | `eyJ...` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_MODEL` | `llama-3.1-70b-versatile` | LLM model to use |
| `OPENAI_API_KEY` | - | For embedding generation |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DEBUG` | `true` | Enable debug logging |
| `LOG_LEVEL` | `INFO` | Logging level |

## Agent Configuration

Agent behavior can be tuned through code-level constants:

### Diagnostician

Located in `src/agents/diagnostician.py`:

- `LEARNING_RATE = 0.15` - How quickly proficiency updates
- `COMPETENCY_THRESHOLD = 60.0` - Minimum proficiency for "mastered"

### Knowledge Manager

Located in `src/agents/knowledge_manager.py`:

- `RETENTION_DECAY = 0.02` - Daily decay for unreviewed topics
- Score prediction formula maps proficiency to 140-260 scale

### Adaptive Scheduler

Located in `src/agents/scheduler.py`:

- `DEFAULT_PLAN_DAYS = 7` - Default plan duration
- `MAX_DAILY_HOURS = 12` - Maximum study hours per day
- `BREAK_INTERVAL_MINUTES = 50` - Study/break cycle

## Graph Configuration

The LangGraph structure in `src/agents/graph_builder.py` supports:

### Conditional Review Routing

The `should_review()` function routes to human review when:

- Predicted score < 180
- More than 3 weak areas identified
- `requires_human_review` flag is set in request

### Memory Checkpointing

The graph uses `MemorySaver()` for state persistence across turns. For production, replace with a persistent checkpointer (e.g., PostgreSQL).

## Database Schema

The Supabase schema supports extensive customization:

### Adding Knowledge Areas

```sql
INSERT INTO knowledge_areas (name, category, subtopics, weight_in_exam)
VALUES ('Genetics', 'Basic Sciences', ARRAY['Mendelian', 'Molecular'], 4.0);
```

### Custom RLS Policies

Modify policies in `src/database/schema.sql` to adjust data access controls.

## API Configuration

FastAPI settings in `src/api/app.py`:

### CORS

Update `allow_origins` for production deployment:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict in production
    ...
)
```

### Rate Limiting

Add rate limiting middleware for production:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
```

## Logging

The system uses Python's standard logging:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
```

For production, consider structured logging with JSON format and log aggregation (e.g., Logstash, Datadog).
