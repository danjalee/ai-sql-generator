import os
import traceback
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from app.dialects import DIALECT_RULES
from app.validator import validate_sql

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SECRET_KEY = os.getenv("SECRET_KEY")

# ----------------------------
# Request model
# ----------------------------
class SQLRequest(BaseModel):
    language: str          # "en" | "ja"
    database: str          # mysql | postgresql | sqlserver | sqlite
    sqlMode: str           # read | write
    schema_ddl: str        # renamed from "schema"
    criteria: str

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ai-sql-generator-frontend.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# API key check
# ----------------------------
def verify_api_key(x_api_key: str = Header(None)):
    if not SECRET_KEY or x_api_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Access denied")

# ----------------------------
# Write intent detector
# ----------------------------
WRITE_KEYWORDS = [
    "delete", "insert", "update",
    "drop", "truncate", "create", "alter"
]

def has_write_intent(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in WRITE_KEYWORDS)

# ----------------------------
# Prompt builder
# ----------------------------
def build_prompt(req: SQLRequest) -> str:
    lang = "English" if req.language == "en" else "Japanese"
    dialect_rule = DIALECT_RULES.get(req.database, "")

    mode_rule = (
        "Only generate SELECT statements."
        if req.sqlMode == "read"
        else "You may generate INSERT, UPDATE, DELETE, CREATE, ALTER, or DROP statements."
    )

    return f"""
You are an expert SQL engineer.

Language: {lang}
Database: {req.database}

STRICT RULES (must follow all):
- Output ONLY valid SQL
- No explanations, no markdown
- Use ONLY tables and columns explicitly defined in the schema
- DO NOT invent tables, columns, aliases, or parameters
- Single SQL statement only
- {dialect_rule}
- {mode_rule}

Schema (raw DDL):
{req.schema_ddl}

User request:
{req.criteria}
"""

# ----------------------------
# API endpoint
# ----------------------------
@app.post("/generate-sql")
def generate_sql(req: SQLRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    # HARD BLOCK write intent in READ mode
    if req.sqlMode == "read" and has_write_intent(req.criteria):
        raise HTTPException(
            status_code=400,
            detail="Write operations are not allowed in READ mode"
        )

    try:
        prompt = build_prompt(req)

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0
        )

        sql = response.choices[0].message.content.strip()

        validate_sql(sql, req.sqlMode)

        return {"sql": sql}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))