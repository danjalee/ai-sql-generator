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

    raw = response.json().get("response", "").strip()
    if "```" in raw:
        raw = raw.split("```")[1].strip()
    return raw.rstrip(";")