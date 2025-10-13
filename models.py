# models.py (เวอร์ชันแก้ไขที่ถูกต้อง)
from pydantic import BaseModel
from typing import List

class UserQuery(BaseModel):
    query_text: str

class ReelData(BaseModel):
    url: str
    description: str
    quality_score: float

class CtaButton(BaseModel):
    text: str = "ดูคลิปบน Facebook"
    url: str

class ContentCard(BaseModel):
    presentation_text: str
    cta_button: CtaButton

class ApiResponse(BaseModel):
    content_cards: List[ContentCard]