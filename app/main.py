from fastapi import FastAPI

app = FastAPI(title="IT Helpdesk Agent")

@app.get("/")
def home():
    return {"message": "IT Helpdesk Agent is running"}

@app.post("/chat")
def chat(payload: dict):
    return {"reply": "Hello! Unga problem enna?", "received": payload}