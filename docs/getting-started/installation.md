# Installation Guide

This guide walks through setting up the Agentic USMLE system for development or research use.

## Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Supabase account** (free tier sufficient)
- **Groq API key** (free tier available)
- **Git** for version control

## Step 1: Clone the Repository

```bash
git clone https://github.com/stanley-nelavala/Agentic-AI-for-USMLE-Prep.git
cd Agentic-AI-for-USMLE-Prep
```

## Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or using pyproject.toml:

```bash
pip install -e ".[dev]"
```

## Step 4: Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Groq API
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Obtaining API Keys

**Groq API Key:**
1. Sign up at [console.groq.com](https://console.groq.com)
2. Create an API key in the dashboard
3. Free tier includes 10K requests/day

**Supabase Credentials:**
1. Create a project at [supabase.com](https://supabase.com)
2. Go to Project Settings → API
3. Copy your project URL and service role key

## Step 5: Initialize Database

Run the SQL schema in your Supabase SQL editor:

1. Open your Supabase project
2. Navigate to SQL Editor
3. Copy and paste contents of `src/database/schema.sql`
4. Run the migration from `src/database/migrations/001_initial_schema.sql`

## Step 6: Verify Installation

Test the database connection:

```bash
python -c "from src.database.client import test_connection; print(test_connection())"
```

Run the API server:

```bash
uvicorn src.api.app:app --reload
```

Visit `http://localhost:8000/docs` to see the API documentation.

## Step 7: Run a Test Assessment

```bash
python -m src.agents.main --student-id IMG001 --json
```

This will run the complete agent pipeline with mock data.

## Troubleshooting

### Groq API Not Configured

If `GROQ_API_KEY` is not set, the system will fall back to mock diagnostics. This is fine for testing.

### Supabase Connection Error

Verify your URL and key are correct. Check that the schema has been applied.

### Import Errors

Ensure you're in the project root directory and the virtual environment is activated.

## Next Steps

- Read the [Quick Start Guide](quickstart.md) to run your first assessment
- Explore the [Architecture Overview](../architecture/overview.md) to understand the system
- Review the [API Documentation](../api/endpoints.md) for integration details
