import requests
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.intent import detect_patterns, Pattern
from app.strategy import STRATEGY_RULES
from app.validator import validate_sql
from app.dialects import DIALECT_RULES
from app.executor import execute_sql

# ============================
# Request model
# ============================
class SQLRequest(BaseModel):
    language: str
    database: str
    schema: str
    criteria: str


# ============================
# App
# ============================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# Security
# ============================
SECRET_KEY = "my-super-secret-key-123"

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Access denied")


# ============================
# LLM call (FAST + deterministic)
# ============================
def call_llm(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "top_p": 0.05,
                "num_predict": 300   # critical: stops rambling
            }
        },
        timeout=40
    )
    response.raise_for_status()

    raw = response.json().get("response", "").strip()

    if "```" in raw:
        raw = raw.split("```")[1].strip()

    return raw.rstrip(";")

# ============================
# Prompt builder (ANTI-WITH)
# ============================
def build_prompt(req: SQLRequest) -> str:
    patterns = detect_patterns(req.criteria)

    strategy_text = "\n".join(
        STRATEGY_RULES[p] for p in patterns if p in STRATEGY_RULES
    )

    dialect_rule = DIALECT_RULES.get(req.database, "")

    no_cte = Pattern.SIMPLE_SELECT in patterns

    return f"""
You are an expert SQL solver.

ABSOLUTE RULES:
- Output ONE SQL statement
- SQL ONLY (no explanation)
- MUST start with SELECT
- DO NOT use WITH unless absolutely required
- DO NOT use LIMIT unless explicitly requested
- DO NOT use CREATE, INSERT, UPDATE, DELETE
- Use ONLY tables and columns from schema
- Prefer simplest possible query

{"DO NOT use JOIN unless required." if no_cte else ""}

STRATEGY RULES:
{strategy_text}

DIALECT:
{dialect_rule}

SCHEMA:
{req.schema}

QUESTION:
{req.criteria}
"""

# ============================
# Endpoint
# ============================
@app.post("/generate-sql")
def generate_sql(req: SQLRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    try:
        # Generate SQL (single shot)
        sql = call_llm(build_prompt(req))

        # Hard validation
        validate_sql(sql)

        # Execute once (no loops)
        try:
            result = execute_sql(req.schema, sql)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Execution failed: {e}"
            )

        # Sanity check
        if result["row_count"] == 0:
            raise HTTPException(
                status_code=400,
                detail="Query returned zero rows (likely wrong logic)"
            )

        return {"sql": sql}

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="SQL generation failed")
