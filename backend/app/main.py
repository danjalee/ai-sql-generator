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

# ✅ Allow local + deployed frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ai-sql-generator-frontend.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Security
# ----------------------------
SECRET_KEY = "my-super-secret-key-123"

def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != SECRET_KEY:
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
""".strip()

# ----------------------------
# API endpoint
# ----------------------------
@app.post("/generate-sql")
def generate_sql(req: SQLRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    mode = "read" if req.sqlMode.lower() in ["read", "select"] else "write"

    if mode == "read" and has_write_intent(req.criteria):
        raise HTTPException(
            status_code=400,
            detail="Write operations are not allowed in READ mode"
        )

    prompt = build_prompt(req, mode)

    try:
        # ✅ LOCAL OLLAMA ONLY
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "codellama",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        if response.status_code != 200:
            raise RuntimeError(response.text)

        result = response.json()
        sql = result.get("response", "").strip()

        if not sql:
            raise ValueError("Empty SQL generated")

        validate_sql(sql, mode)

        return {"sql": sql}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {e}")
