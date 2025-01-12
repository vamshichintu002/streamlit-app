from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from youtubesearchpython import VideosSearch
from typing import List, Dict, Any
from quiz_logic import generate_quiz_for_video

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search")
async def search_youtube_playlists(query: str) -> List[Dict[str, Any]]:
    try:
        # Create a video search with a playlist filter
        search = VideosSearch(query + " python course playlist", limit=10)
        results = search.result()['result']
        
        # Filter for playlist results
        playlists = [
            result for result in results
            if 'playlist' in result.get('title', '').lower() or 
               'course' in result.get('title', '').lower()
        ]
        
        return playlists
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz")
async def get_quiz(title: str, description: str) -> List[Dict[str, Any]]:
    try:
        quiz = generate_quiz_for_video(title, description)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
