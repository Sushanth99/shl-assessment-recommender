from google import genai
import requests
from fastapi import HTTPException
from bs4 import BeautifulSoup
import os

def get_job_description_from_url(url: str) -> str:
    session = requests.Session()
    # url = "https://www.linkedin.com/jobs/view/research-engineer-ai-at-shl-4194768899/?originalSubdomain=in"
    response = session.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Input URL invalid")
    
    content = BeautifulSoup(response.content, 'html.parser').get_text(strip=True, separator='\n')

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    generated_response = client.models.generate_content(
        model="gemini-2.0-flash",
        # contents=f"Get the job description from the following context in plain text:\n{content}",
        contents=f"Extract a short description of the job and the skills and experience required in that order in plain text :\n{content}",
        
    )
    return generated_response.text