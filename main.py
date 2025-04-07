from typing import Union, List
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pinecone import Pinecone
from pinecone_utils import pinecone_inference
import os
from dotenv import load_dotenv
load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host="https://individual-tests-index-4sgrwfc.svc.aped-4627-b74a.pinecone.io")
namespace = "ns1"

def pinecone_get_results(query: str):
    results = index.search(
        namespace="dense-index",
        query={
            "top_k": 15,
            "inputs": {
                'text': query
            }
        
        },
        rerank={
            "model": "bge-reranker-v2-m3",
            "top_n": 10,
            "rank_fields": ["Description"]
        }
    )
    return results

def pinecone_normalize_results(results):
    hits = []
    for item in results["result"]["hits"]:
        dict_item = item.to_dict()
        # dict_item.update(dict_item.pop("fields"))
        hits.append(dict_item)
    return hits
        

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# sample_query = "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes."

@app.get("/search")
def search_items(method: str = "rag", query: Union[str, None] = None):
    if not query:
        return JSONResponse(content={"detail": "Invalid Input"}, status_code=400)
    hits = pinecone_inference(index, namespace, query)
    return JSONResponse(content=jsonable_encoder(hits))