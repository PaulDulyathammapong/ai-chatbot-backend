# main.py (Final Debug Version - Lifespan Disabled)
import os
import json
from fastapi import FastAPI, HTTPException
# from contextlib import asynccontextmanager # Lifespan not used
from fastapi.middleware.cors import CORSMiddleware

from models import UserQuery, ApiResponse, ReelData, ContentCard, CtaButton
from rag_system import setup_database, add_reel_to_db, query_vector_db # Keep imports
import google.generativeai as genai # Keep import

# --- Lifespan function commented out ---
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Startup event: Application is starting up.")
#     # ... (Database setup code removed from here) ...
#     yield
#     print("Shutdown event.")

app = FastAPI(
    title="AI Chatbot Backend",
    version="1.0.0",
    # lifespan=lifespan # <--- Disable lifespan here
)

# --- CORS Middleware (Keep Enabled) ---
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

# --- Google AI Setup (Keep Enabled) ---
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("!!! FATAL ERROR: GOOGLE_API_KEY environment variable not set.")

generation_config = {"temperature": 0.7}
SYSTEM_INSTRUCTION = """
You are an expert content curator... (rest of instruction)
""" # Keep instruction
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    generation_config=generation_config,
    system_instruction=SYSTEM_INSTRUCTION
) # Keep model setup

# --- API Endpoints (Keep Enabled) ---
@app.get("/")
def read_root():
    return {"Status": "OK", "Message": "Backend Running (Lifespan Disabled)!"} # Updated message

@app.post("/api/search", response_model=ApiResponse)
async def search_and_format(user_query: UserQuery):
    # This will likely fail now because DB wasn't set up, but that's OK for this test
    try:
        rag_results = query_vector_db(user_query.query_text)
        if not rag_results:
            not_found_card = ContentCard(presentation_text="DB not set up yet.", cta_button=CtaButton(text="-", url="#"))
            return ApiResponse(content_cards=[not_found_card])
        # ... (rest of search endpoint) ...
        prompt_for_gemini = json.dumps([r.model_dump() for r in rag_results], indent=2)
        response = model.generate_content(prompt_for_gemini)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        response_data = json.loads(cleaned_response)
        validated_response = ApiResponse.model_validate(response_data)
        return validated_response
    except Exception as e:
        print(f"An error occurred during search (expected if DB empty): {e}")
        raise HTTPException(status_code=500, detail="Search error (DB might be empty).")


# --- Manual Setup Endpoint (Keep Enabled, but remove DEBUG tag for now) ---
@app.post("/manual-setup-database") # Removed tags=["DEBUG"]
def run_manual_database_setup():
    """
    Endpoint to manually set up DB after server starts.
    """
    try:
        print("Manual Setup: Running database setup...")
        setup_database()
        print("Manual Setup: Populating database with sample data...")
        sample_reels = [
            ReelData(url="https://facebook.com/reels/funny_cat_1", description="????????????????? ??????", quality_score=0.98),
            ReelData(url="https://facebook.com/reels/cooking_fail_1", description="????????????????? ??????", quality_score=0.95),
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

print("main.py finished loading (Lifespan Disabled).") # Add logging
