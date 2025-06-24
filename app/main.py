from fastapi import FastAPI, WebSocket, Request, Response, HTTPException, status, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.model import graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
def send_message( query: str):
    result = graph.invoke({"text": query})
    return result