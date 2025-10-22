# rag_system.py (Final Version - Using Service Name/Individual Params)
import os
import psycopg2
from pgvector.psycopg2 import register_vector
import google.generativeai as genai
from typing import List
from models import ReelData

try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    embedding_model = "models/text-embedding-004"
except KeyError:
    print("!!! FATAL ERROR: GOOGLE_API_KEY environment variable not set.")
    embedding_model = None

def get_db_connection():
    """
    Connects using individual environment variables provided by Railway.
    This bypasses potential issues with DATABASE_URL parsing.
    Uses PGHOST as the primary connection method.
    """
    try:
        # Use PGHOST (which Railway sets to the service name/internal host)
        db_host = os.environ.get("PGHOST")
        if not db_host:
            raise ValueError("PGHOST environment variable is not set by Railway.")

        conn = psycopg2.connect(
            host=db_host, # Use the internal service host provided by Railway
            port=os.environ.get("PGPORT"),
            user=os.environ.get("PGUSER"),
            password=os.environ.get("PGPASSWORD"),
            dbname=os.environ.get("PGDATABASE")
        )
        register_vector(conn)
        print(f"Successfully connected to database using host: {db_host}")
        return conn
    except KeyError as e:
        # This catches if any of the PG* variables are missing
        print(f"!!! FATAL ERROR: Missing required database connection variable: {e}")
        raise ValueError(f"Missing required database connection variable: {e}")
    except psycopg2.OperationalError as e:
        # This catches general connection errors (wrong password, host unreachable etc.)
        print(f"!!! FATAL ERROR: Could not connect to database using individual parameters.")
        print(f"Host tried: {os.environ.get('PGHOST')}")
        print(f"Error details: {e}")
        raise e
    except ValueError as e:
         # Catches the specific error if PGHOST is missing
         print(f"!!! FATAL ERROR: {e}")
         raise e


def setup_database():
    """Creates the 'reels' table if it doesn't exist."""
    print("Attempting to set up database table...")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Enable vector extension if not enabled
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        # Create table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reels (
            id SERIAL PRIMARY KEY,
            url VARCHAR(255) UNIQUE NOT NULL,
            description TEXT,
            quality_score FLOAT,
            embedding VECTOR(768)
        );
        """)
        conn.commit()
        cursor.close()
        print("Database table 'reels' checked/created successfully.")
    except Exception as e:
        print(f"Error during database setup: {e}")
        # Reraise the exception to make it visible in Railway logs
        raise e
    finally:
        if conn:
            conn.close()

def add_reel_to_db(reel: ReelData):
    """Generates embedding and inserts/updates reel data in the database."""
    if not embedding_model:
        print("Error: Embedding model not configured (GOOGLE_API_KEY missing?). Skipping add_reel_to_db.")
        return

    conn = None
    try:
        embedding = genai.embed_content(
            model=embedding_model,
            content=reel.description,
            task_type="RETRIEVAL_DOCUMENT"
        )["embedding"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO reels (url, description, quality_score, embedding)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
            """,
            (reel.url, reel.description, reel.quality_score, embedding)
        )
        conn.commit()
        cursor.close()
        print(f"Successfully added/skipped reel: {reel.url}")
    except Exception as e:
        print(f"Error adding reel {reel.url} to DB: {e}")
    finally:
        if conn:
            conn.close()

def query_vector_db(query_text: str) -> List[ReelData]:
    """Generates query embedding and finds the 5 most similar reels."""
    if not embedding_model:
        print("Error: Embedding model not configured (GOOGLE_API_KEY missing?). Skipping query_vector_db.")
        return []

    conn = None
    try:
        query_embedding = genai.embed_content(
            model=embedding_model,
            content=query_text,
            task_type="RETRIEVAL_QUERY"
        )["embedding"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT url, description, quality_score FROM reels ORDER BY embedding <-> %s::vector LIMIT 5;",
            (query_embedding,)
        )
        results = cursor.fetchall()
        cursor.close()
        return [ReelData(url=row[0], description=row[1], quality_score=row[2]) for row in results]
    except Exception as e:
        print(f"Error querying vector DB: {e}")
        return []
    finally:
        if conn:
            conn.close()
