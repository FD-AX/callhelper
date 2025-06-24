from fastapi import FastAPI, WebSocket, Request, Response, HTTPException, status, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse

from app.model import graph

app = FastAPI()

@app.post("/chat")
def send_message( query: str):
    result = graph.invoke({"text": query})
    return result