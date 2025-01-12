import streamlit as st
import requests
from urllib.parse import parse_qs, urlparse
from typing import List, Dict, Any

# Backend API URL
BACKEND_URL = "http://localhost:8000"

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query)['v'][0]
            if parsed_url.path[:7] == '/embed/':
                return parsed_url.path.split('/')[2]
            if parsed_url.path[:3] == '/v/':
                return parsed_url.path.split('/')[2]
        return None
    except Exception as e:
        st.error(f"Error parsing video URL: {str(e)}")
        return None

def get_quiz(title: str, description: str) -> List[Dict[str, Any]]:
    """Fetch quiz from backend API"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/quiz",
            params={"title": title, "description": description}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error getting quiz: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error getting quiz: {str(e)}")
        return []

def get_qa(title: str, description: str) -> List[Dict[str, Any]]:
    """Fetch Q&A from backend API"""
    try:
        # Get video ID from session state
        video_id = st.session_state.get('video_id', '')
        if not video_id:
            st.error("No video ID available")
            return []
            
        response = requests.get(
            f"{BACKEND_URL}/qa/{video_id}",
            params={"title": title, "description": description}
        )
        st.write(f"Debug - Response status: {response.status_code}")
        st.write(f"Debug - Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            qa_list = data.get('qa', [])
            if not qa_list:
                st.warning("No Q&A questions were generated. Using default questions.")
                return get_default_questions()
            return qa_list
        else:
            st.error(f"Error getting Q&A: {response.text}")
            return get_default_questions()
    except Exception as e:
        st.error(f"Error getting Q&A: {str(e)}")
        return get_default_questions()

def get_default_questions() -> List[Dict[str, Any]]:
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

def evaluate_qa_answer(question: Dict[str, Any], answer: str) -> tuple[float, str, list]:
    """Submit Q&A answer for evaluation"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/qa/evaluate",
            json={"question": question, "answer": answer}
        )
        if response.status_code == 200:
            result = response.json()
            return (
                result.get('score', 0.0),
                result.get('feedback', ''),
                result.get('concepts_covered', [])
            )
        else:
            st.error(f"Error evaluating answer: {response.text}")
            return 0.0, "Error evaluating answer", []
    except Exception as e:
        st.error(f"Error evaluating answer: {str(e)}")
        return 0.0, "Error evaluating answer", []

def display_quiz(quiz: List[Dict[str, Any]], container) -> None:
    """Display quiz in the given container"""
    if not quiz:
        container.warning("No quiz available for this video.")
        return

    container.subheader("📝 Quiz")
    
    # Initialize session state for quiz
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = {}
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    if 'quiz_score' not in st.session_state:
        st.session_state.quiz_score = 0
    
    # Display questions and collect answers
    for i, question in enumerate(quiz):
        container.write(f"**Question {i+1}:** {question.get('question', '')}")
        options = question.get('options', [])
        
        # Radio button for each question
        answer = container.radio(
            "Select your answer:",
            options,
            key=f"q_{i}",
            index=None,
            help="Choose the best answer"
        )
        
        if answer:
            st.session_state.quiz_answers[i] = answer
        
        container.write("---")
    
    # Submit button
    if not st.session_state.quiz_submitted and container.button("Submit Quiz", key="submit_quiz"):
        score = 0
        results = container.container()
        results.subheader("Quiz Results")
        
        for i, question in enumerate(quiz):
            user_answer = st.session_state.quiz_answers.get(i)
            correct_answer = question.get('correct_answer', '')
            
            if user_answer == correct_answer:
                score += 1
                results.success(f"Q{i+1}: ✅ Correct!")
            else:
                results.error(f"Q{i+1}: ❌ Incorrect")
                results.info(f"Correct answer: {correct_answer}")
        
        st.session_state.quiz_score = score
        results.info(f"Your Score: {score}/{len(quiz)}")
        st.session_state.quiz_submitted = True
        
        # Show motivational message based on score
        percentage = (score / len(quiz)) * 100
        if percentage == 100:
            results.balloons()
            results.success("🎉 Perfect score! Excellent work!")
        elif percentage >= 70:
            results.success("👏 Great job! Keep up the good work!")
        else:
            results.info("📚 Keep learning! Try watching the video again and retake the quiz.")
        
        # Add retry button
        if results.button("Try Again"):
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.quiz_score = 0
            st.experimental_rerun()

def display_qa(qa_list: List[Dict[str, Any]], container) -> None:
    """Display Q&A section in the given container"""
    if not qa_list:
        container.warning("No Q&A available for this video.")
        return

    container.subheader("🤔 Open-ended Questions")
    
    # Initialize session state for Q&A
    if 'qa_answers' not in st.session_state:
        st.session_state.qa_answers = {}
    if 'qa_evaluations' not in st.session_state:
        st.session_state.qa_evaluations = {}
    if 'qa_submitted' not in st.session_state:
        st.session_state.qa_submitted = False
    if 'qa_total_score' not in st.session_state:
        st.session_state.qa_total_score = 0
    
    # Display questions and collect answers
    for i, qa_item in enumerate(qa_list):
        container.write(f"**Question {i+1}:** {qa_item.get('question', '')}")
        
        # Text area for each answer
        answer = container.text_area(
            "Your answer:",
            key=f"qa_{i}",
            help="Write a 1-3 line answer"
        )
        
        if answer:
            st.session_state.qa_answers[i] = answer
        
        container.write("---")
    
    # Submit button
    if not st.session_state.qa_submitted and container.button("Submit Answers", key="submit_qa"):
        total_score = 0
        results = container.container()
        results.subheader("Q&A Results")
        
        for i, qa_item in enumerate(qa_list):
            user_answer = st.session_state.qa_answers.get(i, "")
            if user_answer:
                evaluation = evaluate_qa_answer(qa_item, user_answer)
                st.session_state.qa_evaluations[i] = evaluation
                score, feedback, concepts = evaluation  # Unpack the tuple
                total_score += score
                
                results.write(f"**Question {i+1}:**")
                results.write(f"Score: {score:.2f}")
                results.info(feedback)
                results.write("Concepts covered: " + ", ".join(concepts))  # Use the unpacked concepts
                results.write("---")
        
        avg_score = total_score / len(qa_list) if qa_list else 0
        st.session_state.qa_total_score = avg_score
        results.info(f"Overall Score: {avg_score:.2f}/1.0")
        st.session_state.qa_submitted = True
        
        # Combined performance assessment
        if hasattr(st.session_state, 'quiz_score'):
            quiz_percentage = st.session_state.quiz_score / len(st.session_state.quiz_answers) if st.session_state.quiz_answers else 0
            combined_score = (quiz_percentage + avg_score) / 2
            
            if combined_score < 0.7:  # Less than 70%
                results.warning("Based on your quiz and Q&A performance, we recommend rewatching the video to better understand the concepts.")
            elif combined_score < 0.85:  # Between 70% and 85%
                results.info("Good effort! Consider reviewing specific sections of the video related to the concepts you missed.")
            else:  # 85% or higher
                results.success("Excellent work! You've demonstrated a strong understanding of the material.")

def main():
    st.set_page_config(
        layout="wide",
        menu_items={},  # Hide the menu
        initial_sidebar_state="collapsed"  # Hide the sidebar
    )
    
    # Hide the menu button and other UI elements
    st.markdown("""
    <style>
        .quiz-section {
            height: auto;  /* Allow height to adjust dynamically */
            overflow-y: visible;  /* Remove scroll if not needed */
            padding: 1rem;
            background-color: #0e1117;
            border-radius: 10px;
            position: relative;  /* Change from sticky to relative */
            top: 0;
        }
        .stVideo {
            width: 100%;
            height: 100%;
            min-height: calc(100vh - 100px);
        }
        .block-container {
            padding: 1rem !important;
        }
        [data-testid="stVerticalBlock"] {
            gap: 0rem;
        }
        .st-emotion-cache-1v0mbdj {
            width: 100%;
        }
        .stSubheader {
            padding-top: 1rem;  /* Add padding to the title */
            margin-bottom: 1rem;  /* Add margin to the title */
        }
    </style>
""", unsafe_allow_html=True)
    
    # Get video details from query parameters
    video_url = st.query_params.get("video", "")
    video_title = st.query_params.get("title", "")
    video_description = st.query_params.get("description", "")
    
    if not video_url:
        st.error("No video selected. Please go back to the main page and select a video.")
        return
    
    # Create two columns: video player and quiz
    col1, col2 = st.columns([2, 1])  # Wider video, narrower quiz
    
    with col1:
        st.subheader("📺 " + video_title)
        video_id = get_video_id(video_url)
        if video_id:
            # Store video_id in session state
            st.session_state['video_id'] = video_id
            # Embed YouTube video
            embed_code = f'''
                <iframe
                    src="https://www.youtube.com/embed/{video_id}"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen
                    class="stVideo"
                    style="border-radius: 10px;"
                ></iframe>
            '''
            st.markdown(embed_code, unsafe_allow_html=True)
        else:
            st.error("Invalid video URL")
    
    with col2:
        quiz_container = st.container()
        quiz_container.markdown('<div class="quiz-section">', unsafe_allow_html=True)
        
        # Initialize or get quiz from session state
        if 'current_quiz' not in st.session_state:
            with st.spinner("Generating quiz..."):
                quiz = get_quiz(video_title, video_description)
                st.session_state.current_quiz = quiz
        
        # Display the quiz
        display_quiz(st.session_state.current_quiz, quiz_container)
        quiz_container.markdown('</div>', unsafe_allow_html=True)
        
        qa_container = st.container()
        qa_list = get_qa(video_title, video_description)
        display_qa(qa_list, qa_container)

if __name__ == "__main__":
    main()  