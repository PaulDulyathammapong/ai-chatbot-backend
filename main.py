# main.py (Final Version with CORS)
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
    print("Startup event: Running database setup.")
    try:
        setup_database()
        # Add sample data if needed (this will run on every startup)
        sample_reels = [
            ReelData(url="https://facebook.com/reels/funny_cat_video_1", description="A funny cat video.", quality_score=0.98),
            ReelData(url="https://facebook.com/reels/cooking_fail_2", description="A hilarious cooking fail.", quality_score=0.95),
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

# --- Add This CORS Section ---
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
# -----------------------------

try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("!!! FATAL ERROR: GOOGLE_API_KEY is not set.")

# ... The rest of your main.py code (endpoints) remains the same ...

generation_config = {"temperature": 0.7}
SYSTEM_INSTRUCTION = "You are an expert content curator..."
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest", generation_config=generation_config, system_instruction=SYSTEM_INSTRUCTION)

@app.get("/")
def read_root():
    return {"Status": "OK", "Message": "Welcome to the AI Chatbot Backend!"}

@app.post("/api/search", response_model=ApiResponse)
async def search_and_format(user_query: UserQuery):
    try:
        rag_results = query_vector_db(user_query.query_text)
        if not rag_results:
            not_found_card = ContentCard(
                presentation_text="Sorry, no matching videos found. Please try another search.",
                cta_button=CtaButton(text="Try Again", url="#")
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