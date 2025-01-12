import streamlit as st
from urllib.parse import urlencode
import requests
from typing import List, Dict, Any

# Backend API URL
BACKEND_URL = "http://localhost:8000"

def search_courses(query: str) -> List[Dict[str, Any]]:
    try:
        response = requests.get(f"{BACKEND_URL}/search", params={"query": query})
        return response.json()
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return []

def get_quiz(title: str, description: str) -> List[Dict[str, Any]]:
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
    if not quiz:
        container.warning("No quiz available for this video.")
        return

    container.subheader("📝 Quiz Time!")
    
    # Store answers in session state
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    
    for i, question in enumerate(quiz):
        q_id = f"q_{i}"
        container.write(f"**Question {i+1}:** {question.get('question', '')}")
        options = question.get('options', [])
        
        # Radio button for each question
        answer = container.radio(
            "Select your answer:",
            options,
            key=f"radio_{i}",
            index=None,
            help="Choose the best answer"
        )
        
        # Store the answer in session state
        if answer:
            st.session_state.user_answers[q_id] = answer
        
        container.write("---")
    
    # Submit button
    if container.button("Submit Quiz", key="submit_quiz") and not st.session_state.quiz_submitted:
        score = 0
        results = container.container()
        results.subheader("Quiz Results")
        
        for i, question in enumerate(quiz):
            q_id = f"q_{i}"
            user_answer = st.session_state.user_answers.get(q_id)
            correct_answer = question.get('correct_answer', '')
            
            if user_answer == correct_answer:
                score += 1
                results.success(f"Q{i+1}: Correct! ✅")
            else:
                results.error(f"Q{i+1}: Incorrect ❌ - Correct answer: {correct_answer}")
        
        results.info(f"Final Score: {score}/{len(quiz)}")
        st.session_state.quiz_submitted = True
        
        # Add a retry button
        if results.button("Try Again"):
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.experimental_rerun()

def main():
    st.set_page_config(
        page_title="Learning Platform - Course Search",
        page_icon="📚",
        layout="wide",
        menu_items={},
        initial_sidebar_state="collapsed"
    )
    
    # Hide the menu button
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            .stDeployButton {display:none;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)
    
    st.title("📚 Learning Platform")
    st.subheader("Search for Educational Content")
    
    search_query = st.text_input("Enter your search query (e.g., 'python course', 'machine learning')")
    
    if st.button("Search"):
        if search_query:
            with st.spinner("Searching for courses..."):
                results = search_courses(search_query)
                
                if results:
                    st.subheader(f"Found {len(results)} Courses")
                    for result in results:
                        with st.container():
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                if 'thumbnails' in result and result['thumbnails']:
                                    st.image(result['thumbnails'][0]['url'], use_column_width=True)
                            with col2:
                                st.markdown(f"#### {result.get('title', 'No Title')}")
                                st.write(result.get('duration', 'Duration not available'))
                                st.write(result.get('viewCount', {}).get('text', 'N/A views'))
                                description = result.get('description', '').strip()
                                if len(description) > 1000:
                                    description = description[:1000] + "..."
                                st.write(description)
                                
                                query_params = urlencode({
                                    'video': result.get('link', ''),
                                    'title': result.get('title', 'No Title'),
                                    'description': description
                                })
                                st.markdown(f"[Start Learning](player?{query_params})")
                                st.markdown("---")
                                with st.expander(f"📺 {result.get('title', 'No Title')}", expanded=False):
                                    st.write(f"**Description:** {result.get('description', 'No description available')}")
                                    st.write(f"**Duration:** {result.get('duration', 'Duration not available')}")
                                    st.write(f"**Channel:** {result.get('channel', 'Channel not available')}")
                                    
                                    if st.button(f"Generate Quiz for {result.get('title', 'No Title')[:30]}..."):
                                        with st.spinner("Generating quiz..."):
                                            quiz = get_quiz(
                                                result.get('title', 'No Title'),
                                                result.get('description', 'No description available')
                                            )
                                            quiz_container = st.container()
                                            display_quiz(quiz, quiz_container)
                else:
                    st.warning("No courses found. Try a different search term.")
        else:
            st.warning("Please enter a search query.")

if __name__ == "__main__":
    main()
