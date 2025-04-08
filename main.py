import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, Form, HTTPException
from helper.Loading_data import load_data
from helper.full_chain import get_response, simple_chat


_ = load_dotenv(override=True)

app = FastAPI(
    debug=True,
    title="RAG - Weaviate Chatbot",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/ingest")
async def Add_Data_Pinecone(files_data: Optional[UploadFile]=None):
    pass



@app.post("/chat")
async def chatbot_response(user_query: str = Form(...), user_id: str = Form(None)):
    pass


@app.post("/hybrid")
async def hybrid_chat(user_query: str = Form(...), user_id: str = Form(None)):
    pass