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
    allow_origins=["https://ai-sql-generator-frontend.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Security (unchanged)
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
        "Only generate SELECT statements."
        if mode == "read"
        else "You may generate INSERT, UPDATE, DELETE, CREATE, ALTER, or DROP statements."
    )

    return f"""
You are an expert SQL engineer.

Database: {req.database}
Dialect rules: {dialect_rule}

STRICT RULES:
- Output ONLY SQL
- No explanations
- Use ONLY tables/columns from schema
- Single SQL statement
- {mode_rule}

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
    if mode in ["select", "read"]:
        mode = "read"
    else:
        mode = "write"

    if mode == "read" and has_write_intent(req.criteria):
        raise HTTPException(
            status_code=400,
            detail="Write operations are not allowed in READ mode"
        )

    prompt = build_prompt(req, mode)

    try:
        # 🔥 CALL LOCAL LLM (OLLAMA)
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "codellama",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        result = response.json()
        sql = result.get("response", "").strip()

        validate_sql(sql, mode)

        return {"sql": sql}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))