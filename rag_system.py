# rag_system.py (Final Version - Force Host Override)
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
    Connects using DATABASE_URL but explicitly overrides the host
    with PGHOST to force network connection.
    """
    conn_string = os.environ.get("DATABASE_URL")
    db_host = os.environ.get("PGHOST") # Get the Railway-provided host

    if not conn_string:
        raise ValueError("FATAL ERROR: DATABASE_URL environment variable is not set.")
    if not db_host:
         raise ValueError("FATAL ERROR: PGHOST environment variable is not set by Railway.")

    try:
        # Connect using the full URL, BUT force the host
        conn = psycopg2.connect(conn_string, host=db_host)
        register_vector(conn)
        print(f"Successfully connected to database using forced host: {db_host}")
        return conn
    except psycopg2.OperationalError as e:
        print(f"!!! FATAL ERROR: Could not connect to database even with forced host.")
        print(f"Host forced: {db_host}")
        print(f"Error details: {e}")
        raise e
    except ValueError as e:
         print(f"!!! FATAL ERROR: {e}")
         raise e

# --- ??????????????? rag_system.py (setup_database, add_reel_to_db, query_vector_db) ---
# --- ????????????????? ???????????? ---
def setup_database(): ... # (????????)
def add_reel_to_db(reel: ReelData): ... # (????????)
def query_vector_db(query_text: str) -> List[ReelData]: ... # (????????)

# --- ???????? setup_database ---
def setup_database():
    print("Attempting to set up database table...")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
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
        raise e
    finally:
        if conn:
            conn.close()

# --- ???????? add_reel_to_db ---
def add_reel_to_db(reel: ReelData):
    if not embedding_model: return
    conn = None
    try:
        embedding = genai.embed_content(model=embedding_model, content=reel.description, task_type="RETRIEVAL_DOCUMENT")["embedding"]
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

# --- ???????? query_vector_db ---
def query_vector_db(query_text: str) -> List[ReelData]:
    if not embedding_model: return []
    conn = None
    try:
        query_embedding = genai.embed_content(model=embedding_model, content=query_text, task_type="RETRIEVAL_QUERY")["embedding"]
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
