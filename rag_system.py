# rag_system.py (เวอร์ชันแก้ไขที่ถูกต้อง)
import os
import psycopg2
from pgvector.psycopg2 import register_vector
import google.generativeai as genai
from typing import List
from models import ReelData

# --- การตั้งค่า Gemini Embedding ---
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("!!! WARNING: GOOGLE_API_KEY environment variable not set. This is OK for now if you are not running locally.")

embedding_model = "models/text-embedding-004"

def get_db_connection():
    """สร้างการเชื่อมต่อกับฐานข้อมูล PostgreSQL บน Railway จาก Environment Variable"""
    conn_string = os.environ.get("DATABASE_URL")
    if not conn_string:
        raise ValueError("DATABASE_URL environment variable is not set.")
    conn = psycopg2.connect(conn_string)
    return conn

def setup_database():
    print("Setting up the database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(conn)
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
    conn.close()
    print("Database setup complete.")

def add_reel_to_db(reel: ReelData):
    print(f"Embedding and adding reel: {reel.url}")
    try:
        embedding = genai.embed_content(
            model=embedding_model,
            content=reel.description,
            task_type="RETRIEVAL_DOCUMENT"
        )["embedding"]
        conn = get_db_connection()
        register_vector(conn)
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
        conn.close()
        print(f"Successfully added reel: {reel.url}")
    except Exception as e:
        print(f"Error adding reel {reel.url}: {e}")

def query_vector_db(query_text: str) -> List[ReelData]:
    print(f"Searching for reels related to: '{query_text}'")
    try:
        query_embedding = genai.embed_content(
            model=embedding_model,
            content=query_text,
            task_type="RETRIEVAL_QUERY"
        )["embedding"]
        conn = get_db_connection()
        register_vector(conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT url, description, quality_score FROM reels ORDER BY embedding <-> %s::vector LIMIT 5;",
            (query_embedding,)
        )
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [ReelData(url=row[0], description=row[1], quality_score=row[2]) for row in results]
    except Exception as e:
        print(f"Error querying vector DB: {e}")
        return []

if __name__ == '__main__':
    # ส่วนนี้สำหรับรันเพื่อเพิ่มข้อมูลลง DB โดยตรง
    # เราจะยังไม่ใช้ตอนนี้ แต่เตรียมไว้
    print("Running data population script...")
    # 1. ตั้งค่า API Key และ DB URL บนเครื่องก่อนรัน
    # For Windows: set GOOGLE_API_KEY=... && set DATABASE_URL=...
    # For Mac/Linux: export GOOGLE_API_KEY=... && export DATABASE_URL=...

    setup_database() # สร้างตารางถ้ายังไม่มี

    sample_reels = [
        ReelData(url="https://facebook.com/reels/funny_cat_video_1", description="แมวอ้วนตกใจแตงกวา ตลกมากจนต้องดูซ้ำ", quality_score=0.98),
        ReelData(url="https://facebook.com/reels/cooking_fail_2", description="เชฟมือใหม่ทำอาหารในครัวพลาด ฮาสุดๆ", quality_score=0.95),
        ReelData(url="https://facebook.com/reels/nature_relax_3", description="ชมวิวธรรมชาติสวยๆ ที่สวิตเซอร์แลนด์ พร้อมเพลงฟังสบายๆ ช่วยให้ผ่อนคลาย", quality_score=0.92),
        ReelData(url="https://facebook.com/reels/dog_skate_4", description="สุนัขแสนรู้โชว์ลีลาเล่นสเก็ตบอร์ดอย่างโปร", quality_score=0.94),
        ReelData(url="https://facebook.com/reels/magic_trick_5", description="นักมายากลโชว์ทริคง่ายๆ ที่คุณทำตามได้ที่บ้าน", quality_score=0.89),
    ]

    for reel in sample_reels:
        add_reel_to_db(reel)

    print("Sample data population complete.")