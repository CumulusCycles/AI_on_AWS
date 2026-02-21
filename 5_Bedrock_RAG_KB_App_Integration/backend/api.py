import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

API_GW_URL = os.environ["API_URL"]

app = FastAPI(title="AI Agent Insure — RAG API", version="1.0.0")


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    generated_response: str
    s3_locations: list[str]


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        response = requests.post(API_GW_URL, json={"query": request.query}, timeout=30)
        response.raise_for_status()
        data = response.json()
        return QueryResponse(
            query=data.get("query", request.query),
            generated_response=data.get("generated_response", ""),
            s3_locations=data.get("s3_locations", []),
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="API Gateway timed out.")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
