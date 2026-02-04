import requests

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
    return response.json()["response"].strip().rstrip(";")

def verify_and_fix(sql: str, schema: str, criteria: str) -> str:
    prompt = f"""
Check whether the SQL satisfies the question.

If WRONG → return FIXED SQL.
If CORRECT → return SAME SQL.

STRICT:
- SQL ONLY
- No explanation

Schema:
{schema}

Question:
{criteria}

SQL:
{sql}
"""
    return call_llm(prompt)
