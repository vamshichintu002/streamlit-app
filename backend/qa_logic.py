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

def get_default_questions() -> List[Dict]:
    """Return default questions when there's an error."""
    return [
        {
            "question": "Explain how Python handles variable assignment and memory management.",
            "expected_concepts": ["dynamic typing", "memory allocation", "reference counting", "garbage collection"]
        },
        {
            "question": "What are the key differences between lists and tuples in Python, and when would you use each?",
            "expected_concepts": ["mutability", "immutability", "data structure", "performance", "use cases"]
        },
        {
            "question": "Describe Python's approach to object-oriented programming.",
            "expected_concepts": ["classes", "objects", "inheritance", "encapsulation", "polymorphism"]
        }
    ]

def generate_qa_for_video(video_title: str, video_description: str) -> List[Dict]:
    """Generate open-ended questions based on video content."""
    logger.info(f"Generating Q&A for video: {video_title}")
    
    try:
        # Initialize Groq client with API key
        api_key = os.environ.get("GROQ_API_KEY")
        
        if not api_key:
            logger.error("GROQ_API_KEY environment variable is not set")
            return get_default_questions()
            
        client = Groq(api_key=api_key)
        
        # Prepare the prompt
        prompt = f"""Create open-ended questions based on this Python tutorial:
        Title: {video_title}
        Description: {video_description}

        Generate 3 open-ended questions that test understanding of key concepts. Return ONLY a JSON array with this exact format:
        [
            {{
                "question": "Question text here that requires a short explanation",
                "expected_concepts": ["concept1", "concept2", "concept3", "concept4"]
            }}
        ]

        The questions should:
        1. Be specific to the video content
        2. Require 1-3 line answers
        3. Test understanding of important concepts
        4. Include 3-5 expected concepts for each question"""
        
        # Generate questions using Groq
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a question generator that creates open-ended questions about Python programming tutorials. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract and parse the response
        response_text = completion.choices[0].message.content.strip()
        qa_data = json.loads(response_text)
        
        # Validate question format
        if not isinstance(qa_data, list) or len(qa_data) == 0:
            logger.error("Invalid Q&A format: not a list or empty")
            return get_default_questions()
            
        for item in qa_data:
            if not all(key in item for key in ["question", "expected_concepts"]):
                logger.error("Q&A item missing required fields")
                return get_default_questions()
            if not isinstance(item["expected_concepts"], list) or len(item["expected_concepts"]) < 3:
                logger.error("Q&A item has invalid expected_concepts")
                return get_default_questions()
                
        return qa_data
        
    except Exception as e:
        logger.error(f"Error generating Q&A: {str(e)}")
        return get_default_questions()

def evaluate_answer(question: Dict, user_answer: str) -> tuple[float, str, list]:
    """Evaluate user's answer using GROQ."""
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY environment variable is not set")
            return 0.0, "Unable to evaluate answer", []
            
        client = Groq(api_key=api_key)
        
        # Prepare the evaluation prompt
        prompt = f"""Evaluate this answer to a Python-related question:
        Question: {question['question']}
        User's Answer: {user_answer}
        Expected Concepts: {', '.join(question['expected_concepts'])}
        
        Evaluate the answer based on:
        1. Accuracy of the explanation
        2. Coverage of expected concepts
        3. Clarity and conciseness
        
        Return ONLY a JSON object with this format:
        {{
            "score": (float between 0 and 1),
            "feedback": "Constructive feedback explaining the score and suggesting improvements",
            "concepts_covered": ["list", "of", "concepts", "mentioned", "in", "answer"]
        }}"""
        
        # Generate evaluation using Groq
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are an answer evaluator for Python programming questions. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # Extract and parse the response
        response_text = completion.choices[0].message.content.strip()
        evaluation = json.loads(response_text)
        
        return (
            float(evaluation.get('score', 0.0)),
            evaluation.get('feedback', ''),
            evaluation.get('concepts_covered', [])
        )
        
    except Exception as e:
        logger.error(f"Error evaluating answer: {str(e)}")
        return 0.0, "Error evaluating answer", []
