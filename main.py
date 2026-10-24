from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from function import tasks, tasks_lock, process_page
from answer_question import answer_the_query
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PageRequest(BaseModel):
    url: str

class AskRequest(BaseModel):
    url: str
    question: str
    session_id: str
@app.post("/analyze")
async def analyze_page(request: PageRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid4())
    url = str(request.url)

    with tasks_lock:
        tasks[task_id] = {
            "stage": "starting",
            "progress": 0,
            "message": "Starting analysis...",
            "error": False,
        }

    background_tasks.add_task(process_page, task_id, url)
    return {"task_id": task_id}

@app.get("/progress/{task_id}")
async def get_progress(task_id: str):
    with tasks_lock:
        task = tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Analysis task not found.")
        return task

@app.post("/ask")
def ask_question(request: AskRequest):
    
    
    answer,context = answer_the_query(request.question, request.url,request.session_id)
    return {
        "question": request.question,
        "answer": answer,
        'context':context
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
