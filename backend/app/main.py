import requests
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.dialects import DIALECT_RULES
from app.validator import validate_sql

# ----------------------------
# Request model
# ----------------------------
class SQLRequest(BaseModel):
    language: str
    database: str
    sqlMode: str
    schema: str
    criteria: str

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Security
# ----------------------------
SECRET_KEY = "my-super-secret-key-123"

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Access denied")

# ----------------------------
# Write intent detector
# ----------------------------
WRITE_KEYWORDS = [
    "delete", "insert", "update", "drop",
    "truncate", "create", "alter"
]

def has_write_intent(text: str) -> bool:
    return any(word in text.lower() for word in WRITE_KEYWORDS)

# ----------------------------
# Prompt builder
# ----------------------------
def build_prompt(req: SQLRequest, mode: str) -> str:
    dialect_rule = DIALECT_RULES.get(req.database, "")

    mode_rule = (
        "ONLY generate SELECT statements."
        if mode == "read"
        else "You may generate INSERT, UPDATE, DELETE, CREATE, ALTER, or DROP statements."
    )

    return f"""
You are an expert SQL generator.

STRICT RULES:
- Output ONLY SQL
- NO explanations
- NO markdown
- Use ONLY tables/columns from schema
- Single SQL statement
- {mode_rule}

Database: {req.database}
Dialect rules: {dialect_rule}

Schema:
{req.schema}

User request:
{req.criteria}
"""

# ----------------------------
# API endpoint
# ----------------------------
@app.post("/generate-sql")
def generate_sql(req: SQLRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    mode = req.sqlMode.lower()
    mode = "read" if mode in ["read", "select"] else "write"

    if mode == "read" and has_write_intent(req.criteria):
        raise HTTPException(
            status_code=400,
            detail="Write operations are not allowed in READ mode"
        )

    prompt = build_prompt(req, mode)

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:3b",
                "prompt": prompt + "\nReturn ONLY the SQL statement. No explanations.",
                "stream": False
            },
            timeout=60
        )

        response.raise_for_status()
        result = response.json()

        raw = result.get("response", "").strip()

        # CLEAN OUTPUT (CRITICAL FIX)
        if "```" in raw:
            raw = raw.split("```")[1]

        sql = raw.strip()

        validate_sql(sql, mode)

        return {"sql": sql}

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="SQL generation failed")
