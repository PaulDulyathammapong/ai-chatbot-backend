# rag_system.py (Corrected get_db_connection)
import os
import psycopg2
from pgvector.psycopg2 import register_vector
import google.generativeai as genai
from typing import List
from models import ReelData

# --- Gemini Embedding Setup ---
try:
    # Ensure GOOGLE_API_KEY is set in Railway Variables
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    embedding_model = "models/text-embedding-004"
except KeyError:
    print("!!! FATAL ERROR: GOOGLE_API_KEY environment variable not set.")
    embedding_model = None # Set to None to prevent errors later if key is missing

def get_db_connection():
    """
    Establishes connection to the PostgreSQL database on Railway
    using ONLY the DATABASE_URL environment variable.
    """
    conn_string = os.environ.get("DATABASE_URL")
    if not conn_string:
        # If DATABASE_URL is not set, raise an error immediately.
        raise ValueError("FATAL ERROR: DATABASE_URL environment variable is not set.")
    try:
        # Attempt to connect using the provided URL
        conn = psycopg2.connect(conn_string)
        register_vector(conn) # Register pgvector types for this connection
        return conn
    except psycopg2.OperationalError as e:
        # Catch connection errors and provide more details.
        print(f"!!! FATAL ERROR: Could not connect to database using DATABASE_URL.")
        print(f"Error details: {e}")
        raise e # Re-raise the exception to stop the application if connection fails

def setup_database():
    """Creates the 'reels' table if it doesn't exist."""
    print("Attempting to set up database table...")
    conn = None # Initialize conn to None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Enable vector extension - This should already be done by the template,
        # but running it again is safe.
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        # Create table with embedding column sized for text-embedding-004 (768 dimensions)
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
        # If setup fails, we should ideally stop the app or handle it gracefully.
        raise e # Re-raise exception
    finally:
        if conn:
            conn.close()


def add_reel_to_db(reel: ReelData):
    """Generates embedding and inserts/updates reel data in the database."""
    if not embedding_model:
        print("Error: Embedding model not configured. Skipping add_reel_to_db.")
        return

    conn = None
    try:
        # Generate embedding for the description
        embedding = genai.embed_content(
            model=embedding_model,
            content=reel.description,
            task_type="RETRIEVAL_DOCUMENT"
        )["embedding"]

        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert data, do nothing if URL already exists
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
        print("Error: Embedding model not configured. Skipping query_vector_db.")
        return []

    conn = None
    try:
        # Generate embedding for the user's query
        query_embedding = genai.embed_content(
            model=embedding_model,
            content=query_text,
            task_type="RETRIEVAL_QUERY"
        )["embedding"]

        conn = get_db_connection()
        cursor = conn.cursor()
        # Find 5 nearest neighbors using L2 distance (<->)
        cursor.execute(
            "SELECT url, description, quality_score FROM reels ORDER BY embedding <-> %s::vector LIMIT 5;",
            (query_embedding,)
        )
        results = cursor.fetchall()
        cursor.close()
        # Convert results to ReelData objects
        return [ReelData(url=row[0], description=row[1], quality_score=row[2]) for row in results]
    except Exception as e:
        print(f"Error querying vector DB: {e}")
        return [] # Return empty list on error
    finally:
        if conn:
            conn.close()
