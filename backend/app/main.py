import requests
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.intent import detect_patterns, Pattern
from app.strategy import STRATEGY_RULES
from app.validator import validate_sql
from app.dialects import DIALECT_RULES
from app.executor import execute_sql

# ----------------------------
# Request model
# ----------------------------
class SQLRequest(BaseModel):
    language: str
    database: str
    schema: str
    criteria: str

# ----------------------------
# App
# ----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "my-super-secret-key-123"

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Access denied")

# ----------------------------
# LLM
# ----------------------------
def call_llm(prompt: str) -> str:
    res = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "top_p": 0.1}
        },
        timeout=60
    )
    res.raise_for_status()
    raw = res.json().get("response", "").strip()
    if "```" in raw:
        raw = raw.split("```")[1].strip()
    return raw.rstrip(";")

# ----------------------------
# Prompt
# ----------------------------
def build_prompt(req: SQLRequest) -> str:
    patterns = detect_patterns(req.criteria)

    strategy_text = "\n".join(
        STRATEGY_RULES[p] for p in patterns
    )

    return f"""
You are a LeetCode SQL expert.

STRICT RULES:
- Output ONE SQL statement
- SQL ONLY
- MUST start with SELECT or WITH
- DO NOT invent columns
- Use ONLY schema tables/columns
- Follow ALL strategy rules exactly

STRATEGY RULES:
{strategy_text}

DIALECT:
{DIALECT_RULES.get(req.database, "")}

SCHEMA:
{req.schema}

QUESTION:
{req.criteria}
"""

# ----------------------------
# Endpoint
# ----------------------------
@app.post("/generate-sql")
def generate_sql(req: SQLRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    try:
        sql = call_llm(build_prompt(req))

        # Fast path
        try:
            validate_sql(sql)
            return {"sql": sql}
        except Exception:
            pass

        # Single repair attempt
        repair_prompt = f"""
The SQL below is WRONG.

Fix it.

STRICT:
- SQL ONLY
- ONE statement
- MUST start with SELECT or WITH

SCHEMA:
{req.schema}

QUESTION:
{req.criteria}

SQL:
{sql}
"""
        sql = call_llm(repair_prompt)
        validate_sql(sql)

        return {"sql": sql}

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="SQL generation failed")
