import requests
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.intent import detect_patterns, Pattern
from app.strategy import STRATEGY_RULES
from app.validator import validate_sql, validate_schema_references
from app.verifier import verify_sql
from app.dialects import DIALECT_RULES
from app.rewriter import rewrite_criteria
from app.executor import execute_sql
from app.requirements import REQUIREMENTS


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
# LLM call
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
                "num_predict": 250
            }
        },
        timeout=40
    )

    response.raise_for_status()

    raw = response.json().get("response", "").strip()

    # strip markdown if model adds it
    if "```" in raw:
        import re
        m = re.search(r"```[a-zA-Z]*\n(.*?)```", raw, flags=re.DOTALL)
        if m:
            raw = m.group(1).strip()
        else:
            parts = raw.split("```")
            if len(parts) >= 2:
                raw = parts[1].strip()
        # drop leading language token like 'sql'
        if raw.lower().startswith(("sql\n", "postgresql\n", "mysql\n", "sqlite\n", "sqlserver\n")):
            raw = "\n".join(raw.splitlines()[1:]).strip()

    return raw.rstrip(";")


# ============================
# Prompt builder
# ============================
def build_prompt(req: SQLRequest) -> str:
    patterns = detect_patterns(req.criteria)

    # rewrite ambiguous questions
    rewritten_criteria = rewrite_criteria(
        req.criteria,
        patterns,
        req.language
    )

    strategy_text = "\n".join(
        STRATEGY_RULES[p] for p in patterns if p in STRATEGY_RULES
    )

    dialect_rule = DIALECT_RULES.get(req.database, "")
    simple = Pattern.SIMPLE_SELECT in patterns

    return f"""
You are an expert SQL problem solver.

ABSOLUTE RULES:
- Output ONE SQL statement only
- SQL ONLY (no explanation, no markdown)
- MUST start with SELECT
- DO NOT use WITH unless strictly necessary
- DO NOT use LIMIT unless explicitly requested
- Use ONLY tables and columns from schema

{"DO NOT use JOIN unless required." if simple else ""}

STRATEGY RULES:
{strategy_text}

DIALECT:
{dialect_rule}

SCHEMA:
{req.schema}

QUESTION:
{rewritten_criteria}
"""


# ============================
# Endpoint
# ============================
@app.post("/generate-sql")
def generate_sql(req: SQLRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    patterns = detect_patterns(req.criteria)

    # -------- first attempt --------
    sql = call_llm(build_prompt(req))

    try:
        validate_sql(sql)
        validate_schema_references(req.schema, sql)
        verify_sql(sql, patterns)
        if req.database.lower() == "sqlite":
            execute_sql(req.schema, sql)
        return {"sql": sql}

    except Exception as e:
        # -------- one controlled repair --------
        # Build constraints text from requirements/patterns
        must_use = set()
        forbidden = set()
        for p in patterns:
            r = REQUIREMENTS.get(p)
            if r:
                must_use |= {x.lower() for x in r.must_use}
                forbidden |= {x.lower() for x in r.forbidden}

        constraints = []
        if must_use:
            constraints.append("Must use: " + ", ".join(sorted(must_use)))
        if forbidden:
            constraints.append("Forbidden: " + ", ".join(sorted(forbidden)))
        dialect_rule = DIALECT_RULES.get(req.database, "")

        # include schema table names to avoid hallucinations
        constraints.append("Use ONLY tables and columns from the schema.")
        constraints.append(f"Dialect: {dialect_rule}")

        fix_prompt = f"""
The following SQL is INVALID:

{sql}

ERROR:
{str(e)}

Fix the SQL.

Rules:
- Output ONE SQL statement only
- SQL ONLY
- MUST start with SELECT
- Remove the cause of the error
- Follow all original constraints

Additional constraints:
{chr(10).join(constraints)}

Schema:
{req.schema}
"""

        sql = call_llm(fix_prompt)

        try:
            validate_sql(sql)
            validate_schema_references(req.schema, sql)
            verify_sql(sql, patterns)
            if req.database.lower() == "sqlite":
                execute_sql(req.schema, sql)
            return {"sql": sql}

        except Exception as final_error:
            print("FINAL ERROR:", final_error)
            raise HTTPException(status_code=500, detail=str(final_error))
