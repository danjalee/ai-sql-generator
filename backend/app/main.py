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
    schema: str
    criteria: str

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
# Intent detection (AI responsibility)
# ----------------------------
WRITE_KEYWORDS = [
    "delete", "remove", "insert", "add",
    "update", "modify", "drop", "truncate",
    "create", "alter", "clean", "erase"
]

def detect_intent(text: str) -> str:
    text = text.lower()
    if any(word in text for word in WRITE_KEYWORDS):
        return "write"
    return "read"

# ----------------------------
# Prompt builder (NO USER MODE)
# ----------------------------
def build_prompt(req: SQLRequest) -> str:
    dialect_rule = DIALECT_RULES.get(req.database, "")

    return f"""
You are an expert SQL generator.

Your responsibilities:
- Decide whether the request is READ or WRITE
- Generate exactly ONE valid SQL statement

STRICT RULES:
- Output ONLY SQL
- NO explanations
- NO markdown
- Use ONLY tables and columns from the schema
- Prefer SELECT unless modification is explicitly requested
- Use OR / AND for logical conditions when possible
- Output executable SQL only

Database: {req.database}
Dialect rules: {dialect_rule}

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

    intent = detect_intent(req.criteria)
    prompt = build_prompt(req)

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:3b",
                "prompt": prompt + "\nReturn ONLY the SQL statement.",
                "stream": False
            },
            timeout=60
        )

        response.raise_for_status()
        result = response.json()

        raw = result.get("response", "").strip()

        # Remove code fences if any
        if "```" in raw:
            raw = raw.split("```")[1].strip()

        sql = raw.strip().rstrip(";")
        sql_lower = sql.lower()

        # ----------------------------
        # Enforce intent
        # ----------------------------
        if sql_lower.startswith((
            "insert", "update", "delete",
            "create", "alter", "drop", "truncate"
        )):
            if intent != "write":
                raise HTTPException(
                    status_code=400,
                    detail="Write operation detected but intent is not explicit"
                )

        validate_sql(sql)

        return {"sql": sql}

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="SQL generation failed")