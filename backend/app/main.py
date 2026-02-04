import requests
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.intent import detect_patterns
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

# ----------------------------
# Security
# ----------------------------
SECRET_KEY = "my-super-secret-key-123"

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Access denied")

# ----------------------------
# LLM call (deterministic)
# ----------------------------
def call_llm(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "top_p": 0.1
            }
        },
        timeout=60
    )
    response.raise_for_status()

    raw = response.json().get("response", "").strip()

    # Strip accidental code fences
    if "```" in raw:
        raw = raw.split("```")[1].strip()

    return raw.rstrip(";")

# ----------------------------
# Prompt builder
# ----------------------------
def build_prompt(req: SQLRequest) -> str:
    patterns = detect_patterns(req.criteria)

    strategy_text = "\n".join(
        STRATEGY_RULES[p] for p in patterns if p in STRATEGY_RULES
    )

    dialect_rule = DIALECT_RULES.get(req.database, "")

    return f"""
You are a LeetCode-style SQL solver.

MANDATORY RULES:
- Output ONE SQL statement
- SQL ONLY
- MUST start with SELECT or WITH
- DO NOT use CREATE, INSERT, UPDATE, DELETE
- No explanation
- Use ONLY tables/columns from schema
- Follow ALL strategy rules

STRATEGY RULES:
{strategy_text}

DIALECT:
{dialect_rule}

SCHEMA:
{req.schema}

QUESTION:
{req.criteria}
"""

# ----------------------------
# Self-verification
# ----------------------------
def verify_and_fix(sql: str, req: SQLRequest) -> str:
    prompt = f"""
Check whether the SQL below correctly answers the question.

If WRONG → return FIXED SQL.
If CORRECT → return SAME SQL.

STRICT:
- SQL ONLY
- ONE statement
- MUST start with SELECT or WITH
- DO NOT use CREATE, INSERT, UPDATE, DELETE

SCHEMA:
{req.schema}

QUESTION:
{req.criteria}

SQL:
{sql}
"""
    return call_llm(prompt)

# ----------------------------
# Auto-repair
# ----------------------------
def repair_sql(sql: str, error: str, req: SQLRequest) -> str:
    prompt = f"""
The SQL below is WRONG.

ISSUE:
{error}

Fix it.

STRICT:
- SQL ONLY
- ONE statement
- MUST start with SELECT or WITH
- DO NOT use CREATE, INSERT, UPDATE, DELETE

SCHEMA:
{req.schema}

QUESTION:
{req.criteria}

SQL:
{sql}
"""
    return call_llm(prompt)

# ----------------------------
# Endpoint
# ----------------------------
@app.post("/generate-sql")
def generate_sql(req: SQLRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    try:
        # Initial generation
        sql = call_llm(build_prompt(req))

        # Self-check
        sql = verify_and_fix(sql, req)

        # Validate + execute + repair loop
        for _ in range(2):
            try:
                validate_sql(sql)

                result = execute_sql(req.schema, sql)

                # Sanity check
                if result["row_count"] == 0 and "no" not in req.criteria.lower():
                    raise Exception("Suspicious empty result")

                break  # success

            except Exception as e:
                sql = repair_sql(sql, str(e), req)

        # Final hard validation
        try:
            validate_sql(sql)
        except Exception:
            # Hard reset regeneration (CRITICAL FIX)
            sql = call_llm(
                build_prompt(req)
                + "\nCRITICAL: Output must be a SINGLE SELECT statement. No CREATE / INSERT / VIEW."
            )
            validate_sql(sql)

        return {"sql": sql}

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="SQL generation failed")
