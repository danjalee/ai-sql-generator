from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.intent import detect_patterns
from app.strategy import STRATEGY_RULES
from app.validator import validate_sql
from app.verifier import call_llm, verify_and_fix
from app.dialects import DIALECT_RULES

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
# Prompt builder
# ----------------------------
def build_prompt(req: SQLRequest) -> str:
    patterns = detect_patterns(req.criteria)

    strategy_text = "\n".join(
        STRATEGY_RULES[p] for p in patterns if p in STRATEGY_RULES
    )

    dialect_rule = DIALECT_RULES.get(req.database, "")

    return f"""
You are a LeetCode SQL solver.

MANDATORY:
- ONE SQL statement
- SQL ONLY
- No explanation
- Follow ALL rules

STRATEGY RULES:
{strategy_text}

Dialect:
{dialect_rule}

Schema:
{req.schema}

Question:
{req.criteria}
"""

# ----------------------------
# Endpoint
# ----------------------------
@app.post("/generate-sql")
def generate_sql(req: SQLRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    try:
        # 1️⃣ Generate
        sql = call_llm(build_prompt(req))

        # 2️⃣ Self-verify & repair
        sql = verify_and_fix(sql, req.schema, req.criteria)

        # 3️⃣ Final validation
        validate_sql(sql)

        return {"sql": sql}

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="SQL generation failed")
