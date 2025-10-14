# main.py
import os
from fastapi import FastAPI, HTTPException
from models import UserQuery, ApiResponse
from rag_system import query_vector_db
# --- เพิ่ม 2 บรรทัดนี้ ---
from rag_system import setup_database, add_reel_to_db
from models import ReelData
import google.generativeai as genai
import json

app = FastAPI(
    title="AI Chatbot Backend",
    description="The Hub for connecting Frontend, RAG, and Gemini Pro.",
    version="1.0.0",
)

# ... (โค้ดส่วนที่เหลือของคุณ) ...

@app.get("/")
def read_root():
    return {"Status":"OK","Message":"Welcome to the AI Chatbot Backend!"}

# --- เพิ่ม Endpoint ใหม่นี้เข้าไปล่างสุดทั้งหมด ---
@app.post("/api/setup-database", tags=["Setup"])
def run_database_setup():
    """
    Endpoint พิเศษสำหรับตั้งค่าฐานข้อมูลและเพิ่มข้อมูลตัวอย่าง
    """
    try:
        setup_database()
        sample_reels = [
            ReelData(url="https://facebook.com/reels/funny_cat_video_1", description="แมวอ้วนตกใจแตงกวา ตลกมากจนต้องดูซ้ำ", quality_score=0.98),
            ReelData(url="https://facebook.com/reels/cooking_fail_2", description="เชฟมือใหม่ทำอาหารในครัวพลาด ฮาสุดๆ", quality_score=0.95),
            ReelData(url="https://facebook.com/reels/nature_relax_3", description="ชมวิวธรรมชาติสวยๆ ที่สวิตเซอร์แลนด์ พร้อมเพลงฟังสบายๆ ช่วยให้ผ่อนคลาย", quality_score=0.92),
            ReelData(url="https://facebook.com/reels/dog_skate_4", description="สุนัขแสนรู้โชว์ลีลาเล่นสเก็ตบอร์ดอย่างโปร", quality_score=0.94),
            ReelData(url="https://facebook.com/reels/magic_trick_5", description="นักมายากลโชว์ทริคง่ายๆ ที่คุณทำตามได้ที่บ้าน", quality_score=0.89),
        ]
        for reel in sample_reels:
            add_reel_to_db(reel)
        return {"status": "success", "message": "Database setup and sample data population complete."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))