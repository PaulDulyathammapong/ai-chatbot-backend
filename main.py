# main.py (Simplified Version for Debugging)
import os
from fastapi import FastAPI #, HTTPException
# from contextlib import asynccontextmanager
# from fastapi.middleware.cors import CORSMiddleware

# --- Commented out imports ---
# from models import UserQuery, ApiResponse, ReelData, ContentCard, CtaButton
# from rag_system import setup_database, add_reel_to_db, query_vector_db
# import google.generativeai as genai
# import json

# --- Commented out lifespan ---
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Lifespan startup")
#     # setup_database()
#     # ... add data ...
#     yield
#     print("Lifespan shutdown")

# --- Basic FastAPI App ---
app = FastAPI(
    title="AI Chatbot Backend (Debug Mode)",
    version="DEBUG",
    # lifespan=lifespan # Disabled for now
)

# --- Commented out CORS ---
# origins = ["https://paulai.site", ...]
# app.add_middleware(CORSMiddleware, ...)

# --- Commented out Google AI setup ---
# try:
#     genai.configure(...)
# except KeyError:
#     print("API Key missing")
# model = None # Disabled for now

# --- Basic Root Endpoint ---
@app.get("/")
def read_root():
    print("Root endpoint was hit!") # Add logging
    return {"Status": "OK", "Message": "Simplified Backend is Running!"}

# --- Commented out Search Endpoint ---
# @app.post("/api/search", ...)
# async def search_and_format(...):
#     pass

# --- Commented out Manual Setup Endpoint ---
# @app.post("/manual-setup-database", ...)
# def run_manual_database_setup(...):
#     pass

print("Simplified main.py finished loading.") # Add logging at the end
