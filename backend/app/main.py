import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SECRET_KEY = os.getenv("SECRET_KEY")

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
# Security
# ----------------------------
def verify_api_key(x_api_key: str = Header(None)):
    if not SECRET_KEY or x_api_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Access denied")

# ----------------------------
# Prompt builder
# ----------------------------
def build_prompt(req: SQLRequest) -> str:
    lang = "English" if req.language == "en" else "Japanese"

    mode_rule = (
        "Only generate SELECT statements."
        if req.sqlMode == "read"
        else "You may generate INSERT, UPDATE, DELETE, CREATE, ALTER, or DROP statements."
    )

    return f"""
You are an expert SQL engineer.

Language: {lang}
Database: {req.database}

Rules:
- Output ONLY valid SQL
- No explanations, no markdown
- Use ONLY tables and columns from the schema
- The schema may contain MANY CREATE TABLE statements
- Use JOINs when required
- Single SQL statement unless user explicitly asks otherwise
- {mode_rule}

Schema (raw DDL):
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
        return {"sql": sql}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
