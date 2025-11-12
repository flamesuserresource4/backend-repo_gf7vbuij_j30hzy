import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScoreIn(BaseModel):
    name: str
    time_ms: int
    moves: int

@app.get("/")
def read_root():
    return {"message": "Matching Tiles API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

@app.get("/api/leaderboard", response_model=List[dict])
def get_leaderboard():
    try:
        docs = get_documents("leaderboard", {}, limit=50)
        # Sort by best time, then by fewer moves
        docs_sorted = sorted(docs, key=lambda d: (d.get("time_ms", 1e12), d.get("moves", 1e12)))
        # Map _id to string and only expose needed fields
        result = [
            {
                "id": str(doc.get("_id")),
                "name": doc.get("name", "Anonymous"),
                "time_ms": int(doc.get("time_ms", 0)),
                "moves": int(doc.get("moves", 0)),
            }
            for doc in docs_sorted
        ][:20]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/leaderboard", status_code=201)
def post_score(score: ScoreIn):
    try:
        data = score.model_dump()
        _id = create_document("leaderboard", data)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
