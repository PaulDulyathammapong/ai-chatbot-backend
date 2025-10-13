# main.py (เวอร์ชันแก้ไขที่ถูกต้อง)
import os
from fastapi import FastAPI, HTTPException
from models import UserQuery, ApiResponse
from rag_system import query_vector_db
import google.generativeai as genai
import json

# ---> บรรทัดนี้สำคัญมาก! <---
app = FastAPI(
    title="AI Chatbot Backend",
    description="The Hub for connecting Frontend, RAG, and Gemini Pro.",
    version="1.0.0",
)

try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("!!! WARNING: GOOGLE_API_KEY environment variable not set. API calls will fail.")

generation_config = {"temperature": 0.7, "top_p": 1.0, "top_k": 32, "max_output_tokens": 4096}

SYSTEM_INSTRUCTION = """
You are an expert content curator and a friendly, engaging storyteller. Your primary goal is to make users feel excited and curious about content they've requested, encouraging them to click and watch it on Facebook.
**CONTEXT:**
You will receive a list of 5 Facebook Reel URLs, each with a short description and a quality score. These have been retrieved by a RAG system based on a user's query. Your task is to analyze this list and generate a persuasive, conversational, and concise presentation for each of the 5 Reels.
**RULES:**
1. **Analyze and Select:** Prioritize the ones with the highest `quality_score`.
2. **Conversational Tone:** Address the user directly and in a friendly, natural tone. Use Thai language. Use phrases like "เจอคลิปที่น่าจะใช่สำหรับคุณเลย!", "อันนี้น่าจะถูกใจนะ", or "ถ้าชอบแนวผ่อนลาย ลองดูนี่สิ".
3. **Create a Compelling Narrative:** For each Reel, craft a short, enticing introduction (1-2 sentences). Do NOT just repeat the description. Instead, evoke emotion and curiosity. Focus on the *feeling* the user will get.
4. **Clear Call-to-Action (CTA):** The button text must be exactly "ดูคลิปบน Facebook".
5. **Strict Output Format:** You MUST return a JSON object containing a list called `content_cards`. Each object in the list must have exactly two keys: `presentation_text` and `cta_button`.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    generation_config=generation_config,
    system_instruction=SYSTEM_INSTRUCTION
)

@app.post("/api/search", response_model=ApiResponse)
async def search_and_format(user_query: UserQuery):
    try:
        rag_results = query_vector_db(user_query.query_text)
        if not rag_results:
            from models import ContentCard, CtaButton
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
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON from AI model.")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.get("/")
def read_root():
    return {"Status": "OK", "Message": "Welcome to the AI Chatbot Backend!"}