from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
logger.info(f"GROQ_API_KEY present: {'GROQ_API_KEY' in os.environ}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .quiz_logic import generate_quiz_for_video
from typing import Optional

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/quiz/{video_id}")
async def get_quiz(video_id: str, title: str = "", description: Optional[str] = ""):
    """Generate a quiz based on video title and description"""
    logger.info(f"Generating quiz for video_id: {video_id}, title: {title}")
    try:
        quiz = generate_quiz_for_video(title, description)
        return {"quiz": quiz}
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/test-quiz")
async def test_quiz():
    """Test endpoint to verify quiz generation"""
    logger.info("Testing quiz generation")
    try:
        test_title = "Python Programming Basics"
        test_description = "Learn the fundamentals of Python programming language"
        quiz = generate_quiz_for_video(test_title, test_description)
        logger.info(f"Generated quiz: {quiz}")
        return {"quiz": quiz}
    except Exception as e:
        logger.error(f"Error in test quiz: {str(e)}", exc_info=True)
        raise
