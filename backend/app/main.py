import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from app.dialects import DIALECT_RULES
from app.validator import validate_sql

# ============================
# Load environment variables
# ============================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

# ============================
# Request model
# ============================
class SQLRequest(BaseModel):
    language: str
    database: str
    sqlMode: str   # read | write
    schema: str
    criteria: str

# ============================
# FastAPI app
# ============================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-sql-generator-frontend.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# Security
# ============================
def verify_api_key(x_api_key: str = Header(None)):
    if not SECRET_KEY or x_api_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Access denied")

# ============================
# Write intent detection
# ============================
WRITE_KEYWORDS = [
    "delete", "insert", "update", "drop",
    "truncate", "create", "alter"
]

def has_write_intent(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in WRITE_KEYWORDS)

# ============================
# Prompt builder
# ============================
def build_prompt(req: SQLRequest, mode: str) -> str:
    lang = "English" if req.language == "en" else "Japanese"
    dialect_rule = DIALECT_RULES.get(req.database, "")

    if mode == "read":
        mode_rule = "Generate ONLY a valid SELECT statement. If the request is not a SELECT request, return NOTHING."
    else:
        mode_rule = "You may generate INSERT, UPDATE, DELETE, CREATE, ALTER, or DROP statements."

    return f"""
You are an expert SQL engineer.

Language: {lang}
Database: {req.database}
Dialect rules: {dialect_rule}

STRICT RULES (MUST FOLLOW ALL):
- Output ONLY valid SQL
- No explanations, comments, or markdown
- Use ONLY tables and columns defined in the schema
- DO NOT invent tables, columns, aliases, variables, parameters, or fake conditions
- DO NOT generate fake SELECTs like `WHERE 1=0`
- DO NOT use CTEs (WITH) unless explicitly requested
- DO NOT reference variables in LIMIT or OFFSET
- If Nth / Rank queries are required, use subqueries or window functions
- Single SQL statement only
- {mode_rule}

Schema (DDL):
{req.schema}

User request:
{req.criteria}
""".strip()

# ============================
# API endpoint
# ============================
@app.post("/generate-sql")
def generate_sql(req: SQLRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    # Normalize sqlMode
    mode = req.sqlMode.lower()
    if mode in ["select", "read"]:
        mode = "read"
    else:
        mode = "write"

    # 🚫 HARD BLOCK: write intent in READ mode
    if mode == "read" and has_write_intent(req.criteria):
        raise HTTPException(
            status_code=400,
            detail="Write operation detected. Change SQL Mode to WRITE."
        )

    try:
        prompt = build_prompt(req, mode)

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0
        )

        sql = response.choices[0].message.content.strip()

        if not sql:
            raise HTTPException(
                status_code=400,
                detail="No SQL could be generated for this request"
            )

        # Final validation
        validate_sql(sql, mode)

        return {"sql": sql}

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail="SQL generation failed")