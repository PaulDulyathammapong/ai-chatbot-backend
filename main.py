# main.py (ฉบับสุดท้ายที่สมบูรณ์แบบ)
import os
import json
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware  # Import CORS

from models import UserQuery, ApiResponse, ReelData, ContentCard, CtaButton
from rag_system import setup_database, add_reel_to_db, query_vector_db
import google.generativeai as genai

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup event: Application is starting up.")
    try:
        print("Running database setup...")
        setup_database()
        print("Populating database with sample data...")
        sample_reels = [
            ReelData(url="https://facebook.com/reels/funny_cat_video_1", description="แมวอ้วนตกใจแตงกวา ตลกมากจนต้องดูซ้ำ", quality_score=0.98),
            ReelData(url="https://facebook.com/reels/cooking_fail_2", description="เชฟมือใหม่ทำอาหารในครัวพลาด ฮาสุดๆ", quality_score=0.95),
        ]
        for reel in sample_reels:
            add_reel_to_db(reel)
        print("Database setup and data population complete.")
    except Exception as e:
        print(f"An error occurred during startup setup: {e}")
    yield
    print("Shutdown event.")

app = FastAPI(
    title="AI Chatbot Backend",
    version="1.0.0",
    lifespan=lifespan
)

# --- เพิ่มส่วนนี้เพื่อบอก "ยาม" ให้รับสาย ---
origins = [
    "https://paulai.site",
    "http://paulai.site",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------------------------------

try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("!!! FATAL ERROR: GOOGLE_API_KEY is not set.")

generation_config = {"temperature": 0.7}
SYSTEM_INSTRUCTION = """
You are an expert content curator and a friendly, engaging storyteller. Your primary goal is to make users feel excited and curious about content they've requested, encouraging them to click and watch it on Facebook.
**CONTEXT:**
You will receive a list of 5 Facebook Reel URLs, each with a short description and a quality score. These have been retrieved by a RAG system based on a user's query. Your task is to analyze this list and generate a persuasive, conversational, and concise presentation for each of the 5 Reels.
**RULES:**
1. **Analyze and Select:** Prioritize the ones with the highest `quality_score`.
2. **Conversational Tone:** Address the user directly and in a friendly, natural tone. Use Thai language. Use phrases like "เจอคลิปที่น่าจะใช่สำหรับคุณเลย!", "อันนี้น่าจะถูกใจนะ", or "ถ้าชอบแนวผ่อนคลาย ลองดูนี่สิ".
3. **Create a Compelling Narrative:** For each Reel, craft a short, enticing introduction (1-2 sentences). Do NOT just repeat the description. Instead, evoke emotion and curiosity. Focus on the *feeling* the user will get.
4. **Clear Call-to-Action (CTA):** The button text must be exactly "ดูคลิปบน Facebook".
5. **Strict Output Format:** You MUST return a JSON object containing a list called `content_cards`. Each object in the list must have exactly two keys: `presentation_text` and `cta_button`.
"""
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    generation_config=generation_config,
    system_instruction=SYSTEM_INSTRUCTION
)

@app.get("/")
def read_root():
    return {"Status": "OK", "Message": "Welcome to the AI Chatbot Backend!"}

@app.post("/api/search", response_model=ApiResponse)
async def search_and_format(user_query: UserQuery):
    try:
        rag_results = query_vector_db(user_query.query_text)
        if not rag_results:
            not_found_card = ContentCard(
                presentation_text="ขออภัยค่ะ ไม่พบวิดีโอที่ตรงกับที่คุณมองหา ลองใช้คำค้นหาอื่นดูนะคะ",
                cta_button=CtaButton(text="ลองใหม่", url="#")
            )
            return ApiResponse(content_cards=[not_found_card])

        prompt_for_gemini = json.dumps([r.model_dump() for r in rag_results], indent=2)
        response = model.generate_content(prompt_for_gemini)

        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        response_data = json.loads(cleaned_response)

        validated_response = ApiResponse.model_validate(response_data)
        return validated_response
    except Exception as e:
        print(f"An error occurred during search: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")