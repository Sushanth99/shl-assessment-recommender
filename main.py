from typing import Union
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pinecone import Pinecone
from pinecone_utils import pinecone_inference
from gemini_utils import get_job_description_from_url
from utils import has_url
from dotenv import load_dotenv
import os

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host="https://individual-tests-index-4sgrwfc.svc.aped-4627-b74a.pinecone.io")
namespace = "ns1"

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/search")
def search_items(method: str = "rag", query: Union[str, None] = None):
    if not query:
        return JSONResponse(content={"detail": "Invalid Input"}, status_code=400)
    url = has_url(query)
    if url:
        query = query.replace(url, "") + "\n" + get_job_description_from_url(url)
    hits = pinecone_inference(index, namespace, query)
    return JSONResponse(content=jsonable_encoder(hits))