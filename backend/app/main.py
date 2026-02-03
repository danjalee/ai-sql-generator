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
    "create", "alter", "erase"
]

def detect_intent(text: str) -> str:
    text = text.lower()
    if any(word in text for word in WRITE_KEYWORDS):
        return "write"
    return "read"

# ----------------------------
# Zero-row requirement detection
# ----------------------------
ZERO_ROW_HINTS = [
    "each", "every", "all",
    "even if", "including",
    "0", "zero", "no exam",
    "no record"
]

def requires_zero_rows(text: str) -> bool:
    t = text.lower()
    return any(h in t for h in ZERO_ROW_HINTS)

# ----------------------------
# JOIN analysis
# ----------------------------
def has_inner_join(sql: str) -> bool:
    s = sql.lower()
    return (
        " join " in s
        and "left join" not in s
        and "right join" not in s
        and "cross join" not in s
    )

# ----------------------------
# Prompt builder
# ----------------------------
def build_prompt(req: SQLRequest, force_join_fix: bool = False) -> str:
    dialect_rule = DIALECT_RULES.get(req.database, "")

    join_fix_rule = ""
    if force_join_fix:
        join_fix_rule = """
CRITICAL JOIN RULE:
- The result MUST include rows with zero matches
- NEVER use INNER JOIN for counting
- Use CROSS JOIN between base entities
- Use LEFT JOIN for fact tables
- Use COALESCE(COUNT(...), 0)
"""

    return f"""
You are an expert SQL generator.

Your responsibilities:
- Decide READ or WRITE automatically
- Generate exactly ONE executable SQL statement

STRICT RULES:
- Output ONLY SQL
- NO markdown
- NO explanations
- Use ONLY schema tables/columns
- Prefer SELECT unless modification is explicit
- Destructive queries require clear intent

{join_fix_rule}

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

    intent = detect_intent(req.criteria)
    zero_required = requires_zero_rows(req.criteria)

    def call_llm(prompt: str) -> str:
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
        raw = response.json().get("response", "").strip()
        if "```" in raw:
            raw = raw.split("```")[1].strip()
        return raw.rstrip(";")

    try:
        # First attempt
        sql = call_llm(build_prompt(req))

        # JOIN repair loop (ONE retry is enough)
        if zero_required and has_inner_join(sql):
            sql = call_llm(build_prompt(req, force_join_fix=True))

        # Safety enforcement
        sql_lower = sql.lower()
        if sql_lower.startswith(("delete", "update", "insert", "drop", "alter", "truncate")):
            if intent != "write":
                raise HTTPException(
                    status_code=400,
                    detail="Write operation detected without explicit intent"
                )

        validate_sql(sql)
        return {"sql": sql}

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="SQL generation failed")