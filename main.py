# main.py (Final Version - Manual Setup)
import os
import json
from fastapi import FastAPI, HTTPException

from models import UserQuery, ApiResponse, ReelData, ContentCard, CtaButton
from rag_system import setup_database, add_reel_to_db, query_vector_db
import google.generativeai as genai

# --- ลบ Lifespan Event ที่มีปัญหาออกไปทั้งหมด ---

# --- เริ่มต้น FastAPI App แบบธรรมดา ---
app = FastAPI(
    title="AI Chatbot Backend",
    description="The Hub for connecting Frontend, RAG, and Gemini Pro.",
    version="1.0.0",
)

# --- โค้ดส่วนที่เหลือเหมือนเดิม ---
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("!!! FATAL ERROR: GOOGLE_API_KEY environment variable not set. API calls will fail.")

generation_config = {"temperature": 0.7}
SYSTEM_INSTRUCTION = "You are an expert content curator..."
model = genai.GenerativeModel(...) # ย่อไว้เพื่อให้อ่านง่าย

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"Status": "OK", "Message": "Welcome to the AI Chatbot Backend!"}

@app.post("/api/search", response_model=ApiResponse)
async def search_and_format(user_query: UserQuery):
    # ... โค้ดส่วนนี้เหมือนเดิม ...
    try:
        rag_results = query_vector_db(user_query.query_text)
        if not rag_results:
            # ...
            return ApiResponse(...)
        # ...
        return validated_response
    except Exception as e:
        # ...
        raise HTTPException(...)

# --- สร้างประตูหลังบ้านสำหรับ Setup ข้อมูลด้วยตัวเอง ---
@app.post("/manual-setup-database", tags=["DEBUG"])
def run_manual_database_setup():
    """
    Endpoint พิเศษสำหรับตั้งค่าฐานข้อมูลและเพิ่มข้อมูลตัวอย่างด้วยตัวเอง
    """
    try:
        print("Manual Setup: Running database setup...")
        setup_database()
        print("Manual Setup: Populating database with sample data...")
        sample_reels = [
            ReelData(url="https://facebook.com/reels/funny_cat_1", description="แมวอ้วนตกใจแตงกวา ตลกมาก", quality_score=0.98),
            ReelData(url="https://facebook.com/reels/cooking_fail_1", description="ทำอาหารพลาดในครัว ฮาสุดๆ", quality_score=0.95),
        ]
        for reel in sample_reels:
            add_reel_to_db(reel)
        message = "Database setup and data population complete."
        print(message)
        return {"status": "success", "message": message}
    except Exception as e:
        error_message = f"An error occurred during manual setup: {e}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)