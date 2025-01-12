from dotenv import load_dotenv
import os
import logging
from youtubesearchpython import VideosSearch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
logger.info(f"GROQ_API_KEY present: {'GROQ_API_KEY' in os.environ}")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.quiz_logic import generate_quiz_for_video
from backend.qa_logic import generate_qa_for_video, evaluate_answer
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionAnswer(BaseModel):
    question: dict
    answer: str

@app.get("/search")
async def search_youtube_playlists(query: str) -> List[Dict[str, Any]]:
    """Search for Python course playlists on YouTube"""
    try:
        search = VideosSearch(query + " python course playlist", limit=10)
        results = search.result()['result']
        
        playlists = [
            result for result in results
            if 'playlist' in result.get('title', '').lower() or 
               'course' in result.get('title', '').lower()
        ]
        
        return playlists
    except Exception as e:
        logger.error(f"Error searching YouTube playlists: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz/{video_id}")
async def get_quiz(video_id: str, title: str = "", description: Optional[str] = ""):
    """Generate a quiz based on video title and description"""
    logger.info(f"Generating quiz for video_id: {video_id}, title: {title}")
    try:
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
            
        quiz = generate_quiz_for_video(title, description)
        return {"quiz": quiz}
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/qa/{video_id}")
async def get_qa(video_id: str, title: str = "", description: Optional[str] = ""):
    """Generate Q&A based on video title and description"""
    logger.info(f"Generating Q&A for video_id: {video_id}, title: {title}, description: {description}")
    try:
        if not title:
            logger.error("Title parameter is missing")
            raise HTTPException(status_code=400, detail="Title is required")
            
        qa = generate_qa_for_video(title, description)
        logger.info(f"Generated Q&A: {qa}")
        
        if not qa:
            logger.error("Failed to generate Q&A questions")
            raise HTTPException(status_code=404, detail="Failed to generate Q&A")
            
        return {"qa": qa}
    except Exception as e:
        logger.error(f"Error generating Q&A: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/qa/evaluate")
async def evaluate_qa(qa: QuestionAnswer):
    """Evaluate user's answer to a Q&A question"""
    logger.info("Evaluating Q&A answer")
    try:
        score, feedback, concepts = evaluate_answer(qa.question, qa.answer)
        return {
            "score": score,
            "feedback": feedback,
            "concepts_covered": concepts
        }
    except Exception as e:
        logger.error(f"Error evaluating answer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
