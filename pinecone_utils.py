#!/usr/bin/env python3

from typing import List, Dict
# from pinecone.core.openapi.db_data.model.hit import Hit
import pandas as pd
from pinecone import Pinecone, Index
from dotenv import load_dotenv
import os

load_dotenv()
DATA_DIR = "data/"
INDEX_NAME = "individual-tests-index"
# Initialize a Pinecone client with your API key
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create a dense index with integrated embedding
def pinecone_create_index(index_name: str) -> None:
    """
    Create a Pinecone index with the specified name if it doesn't exist.
    Args:
        index_name (str): The name of the index to create.
    """
    if not pc.has_index(index_name):
        pc.create_index_for_model(
            name=index_name,
            cloud="aws",
            region="us-east-1",
            embed={
                "model":"llama-text-embed-v2",
                "field_map":{"text": "Description"} # Field to be embedded
            }
        )
    return pc.describe_index(name=index_name)["host"]

def pinecone_get_records_for_integrated_embedding(file_path: str) -> List[Dict]:
    """
    Read a CSV file and return its records as a list of dictionaries, which are compatible with
    Pinecone integrated embeddings.
    Args:
        file_path (str): The path to the CSV file.
    Returns:
        List[Dict]: A list of dictionaries representing the records in the CSV file.    
    """
    df = pd.read_csv(file_path)
    df = df.reset_index()
    df['id'] = df['index'].map(lambda x: str(x))
    df = df.drop(["index"], axis=1)
    df["Assessment_Time"] = df["Assessment_Time"].map(lambda x: str(x) if not pd.isna(x) else "NA")
    # description = df["Description"].tolist()
    records = df.to_dict("records")
    return records

def pinecone_upsert_data(host: str, namespace: str, records: List[Dict], batch_size: int = 32) -> None:
    """
    Upsert records to a Pinecone index in batches.
    Args:
        index_name (str): The name of the Pinecone index.
        records (List[Dict]): A list of dictionaries representing the records to upsert.
    """
    index = pc.Index(host=host)
    batch_size = 32
    for i in range(0, len(records), batch_size):
        index.upsert_records(namespace, records[i: i+batch_size])

def pinecone_normalize_results(results: Dict) -> List[Dict]:
    hits = []
    for item in results["result"]["hits"]:
        dict_item = item.to_dict()
        # dict_item.update(dict_item.pop("fields"))
        hits.append(dict_item)
    return hits

def pinecone_inference(index: Index, namespace: str, query: str) -> List[Dict]:

    results = index.search(
        namespace=namespace,
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
    hits = pinecone_normalize_results(results)
    return hits


if __name__ == "__main__":
    # Create the index
    host = pinecone_create_index(INDEX_NAME)

    # Get records from the CSV file
    records = pinecone_get_records_for_integrated_embedding(DATA_DIR + "individual_test_solutions_with_description.csv")

    # Upsert data to Pinecone
    pinecone_upsert_data(host, "ns1", records)

    # Close the Pinecone client
    # pc.close()