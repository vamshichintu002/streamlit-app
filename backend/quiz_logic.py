from typing import List, Dict
import os
import json
import logging
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_default_quiz() -> List[Dict]:
    """Return a default quiz when there's an error."""
    return [
        {
            "question": "What is the main purpose of Python?",
            "options": [
                "General-purpose programming",
                "Only web development",
                "Only data science",
                "Only game development"
            ],
            "correct_answer": "General-purpose programming"
        },
        {
            "question": "Which of these is a core feature of Python?",
            "options": [
                "Dynamic typing",
                "Static typing only",
                "Manual memory management",
                "Compilation required"
            ],
            "correct_answer": "Dynamic typing"
        },
        {
            "question": "What makes Python popular for beginners?",
            "options": [
                "Simple, readable syntax",
                "Complex compilation process",
                "Manual memory management",
                "Strict typing system"
            ],
            "correct_answer": "Simple, readable syntax"
        }
    ]

def generate_quiz_for_video(video_title: str, video_description: str) -> List[Dict]:
    """Generate a quiz based on video content."""
    logger.info(f"Generating quiz for video: {video_title}")
    
    try:
        # Initialize Groq client with API key
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY environment variable is not set")
            return get_default_quiz()
            
        client = Groq(api_key=api_key)
        
        # Prepare the prompt
        prompt = f"""Create a quiz based on this Python tutorial:
        Title: {video_title}
        Description: {video_description}

        Generate 3 multiple-choice questions. Return ONLY a JSON array with this exact format:
        [
            {{
                "question": "Question text here",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "correct_answer": "Option that is correct (must match exactly one of the options)"
            }}
        ]"""
        
        # Generate quiz using Groq
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a quiz generator that creates multiple-choice questions about Python programming tutorials. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract and parse the response
        response_text = completion.choices[0].message.content.strip()
        quiz_data = json.loads(response_text)
        
        # Validate quiz format
        if not isinstance(quiz_data, list) or len(quiz_data) == 0:
            logger.error("Invalid quiz format: not a list or empty")
            return get_default_quiz()
            
        for item in quiz_data:
            if not all(key in item for key in ["question", "options", "correct_answer"]):
                logger.error("Quiz item missing required fields")
                return get_default_quiz()
            if item["correct_answer"] not in item["options"]:
                logger.error("Correct answer not in options")
                return get_default_quiz()
        
        logger.info("Successfully generated quiz")
        return quiz_data
        
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        return get_default_quiz()
