"""
Supabase client configuration and utilities.
Provides centralized database connection management.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Supabase credentials not found. "
        "Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your .env file."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def get_supabase_client() -> Client:
    """Dependency injector for FastAPI routes."""
    return supabase


def test_connection() -> bool:
    """Test Supabase connection by querying knowledge_areas."""
    try:
        response = supabase.table("knowledge_areas").select("count").limit(1).execute()
        return True
    except Exception as e:
        print(f"Supabase connection failed: {e}")
        return False
