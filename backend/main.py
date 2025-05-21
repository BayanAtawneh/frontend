from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional
import sqlite3
from openai import OpenAI
import re
import requests


app = FastAPI()

# Allow frontend access (adjust origin if deploying)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "ecommerce-DB.db"
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-r1:free"

class QuestionRequest(BaseModel):
    question: str
    schema: Optional[str] = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        if not value.strip():
            raise ValueError("Question must not be empty")
        return value

def get_db_schema(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type IN ('table', 'view') AND sql IS NOT NULL;")
        schema_rows = cursor.fetchall()
        schema = "\n".join(row[0] for row in schema_rows)
        conn.close()
        return schema
    except sqlite3.Error as e:
        return f"Error: {e}"


def call_openrouter_api(prompt):
    """Call OpenRouter endpoint using raw HTTP (OpenAI compatible format)."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1000,
        "top_p": 1.0
    }
    try:
        response = requests.post(BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [])[0]["message"]["content"]
    except Exception as e:
        
        return None
    
def generate_sql(question: str, schema: str) -> str:
    prompt = f"""### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Database Schema
This query will run on a database whose schema is represented in this string:
{schema}
Return only the sql query without explaination to run it directly.
"""
    response = call_openrouter_api(prompt)
    #result = response["message"]["content"]
    match = re.search(r"```sql(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        # Fallback: try to extract a SELECT statement from plain text
        alt_match = re.search(r"(SELECT\s.*?);?$", response, re.DOTALL | re.IGNORECASE)
        if alt_match:
            return alt_match.group(1).strip()
    return response.strip()

def execute_query(sql_code):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_code)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description] if cursor.description else []
        cursor.close()
        conn.close()
    except sqlite3.Error as db_error:
        return {
            "sql": sql_code,
            "error": f"SQL execution error: {str(db_error)}"
        }

    return {
        "sql": sql_code,
        "columns": column_names,
        "rows": rows
    }

@app.post("/ask")
def ask_question(payload: QuestionRequest):
    schema = get_db_schema(DB_PATH)
    sql_query = generate_sql(payload.question, schema)
    result = execute_query(sql_query)
    return result
