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
        quiz_section = st.container()
        quiz_section.markdown('<div class="quiz-section">', unsafe_allow_html=True)
        
        # Initialize or get quiz from session state
        if 'current_quiz' not in st.session_state:
            with st.spinner("Generating quiz..."):
                quiz = get_quiz(video_title, video_description)
                st.session_state.current_quiz = quiz
        
        # Display the quiz
        display_quiz(st.session_state.current_quiz, quiz_section)
        quiz_section.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()