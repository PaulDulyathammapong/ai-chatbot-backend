# rag_system.py (Upgraded with SQLAlchemy)
import os
from sqlalchemy import create_engine, text
import google.generativeai as genai
from typing import List
from models import ReelData

try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    embedding_model = "models/text-embedding-004"
except KeyError:
    print("!!! FATAL ERROR: GOOGLE_API_KEY environment variable not set.")
    embedding_model = None

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("FATAL ERROR: DATABASE_URL environment variable is not set.")

# Create a reusable engine
engine = create_engine(DATABASE_URL)

def get_db_connection():
    """Gets a connection from the SQLAlchemy engine."""
    try:
        conn = engine.connect()
        print("Successfully connected to database using SQLAlchemy.")
        return conn
    except Exception as e:
        print(f"!!! FATAL ERROR: Could not connect to database using SQLAlchemy.")
        print(f"Error details: {e}")
        raise e

def setup_database():
    print("Attempting to set up database table...")
    with get_db_connection() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS reels (
            id SERIAL PRIMARY KEY,
            url VARCHAR(255) UNIQUE NOT NULL,
            description TEXT,
            quality_score FLOAT,
            embedding VECTOR(768)
        );
        """))
        conn.commit()
        print("Database table 'reels' checked/created successfully.")

def add_reel_to_db(reel: ReelData):
    if not embedding_model: return

    embedding_list = genai.embed_content(
        model=embedding_model,
        content=reel.description,
        task_type="RETRIEVAL_DOCUMENT"
    )["embedding"]

    # pgvector expects a string representation of the vector
    embedding_str = str(embedding_list)

    with get_db_connection() as conn:
        # Use text() for query and bind parameters
        stmt = text("""
        INSERT INTO reels (url, description, quality_score, embedding)
        VALUES (:url, :description, :quality_score, :embedding)
        ON CONFLICT (url) DO NOTHING;
        """)
        conn.execute(stmt, {
            "url": reel.url, 
            "description": reel.description, 
            "quality_score": reel.quality_score, 
            "embedding": embedding_str
        })
        conn.commit()
        print(f"Successfully added/skipped reel: {reel.url}")

def query_vector_db(query_text: str) -> List[ReelData]:
    if not embedding_model: return []

    query_embedding_list = genai.embed_content(
        model=embedding_model,
        content=query_text,
        task_type="RETRIEVAL_QUERY"
    )["embedding"]

    embedding_str = str(query_embedding_list)

    with get_db_connection() as conn:
        stmt = text("SELECT url, description, quality_score FROM reels ORDER BY embedding <-> :embedding LIMIT 5;")
        result = conn.execute(stmt, {"embedding": embedding_str})
        results = result.fetchall()
        return [ReelData(url=row[0], description=row[1], quality_score=row[2]) for row in results]
