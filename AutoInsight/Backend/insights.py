import os
import pandas as pd
import numpy as np
import asyncio
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Generate basic insights after upload
def generate_insights(report, df):
    insights = []

    if 'highly_correlated_pairs' in report and report['highly_correlated_pairs']:
        top_corr = report['highly_correlated_pairs'][0]
        insights.append(f"{top_corr[0]} and {top_corr[1]} show strong correlation ({top_corr[2]:.2f}).")

    missing_cols = [c for c, v in report['missing_counts'].items() if v > 0]
    if missing_cols:
        insights.append(f"{len(missing_cols)} columns contain missing values — handle them before modeling.")

    for col, info in report["columns"].items():
        if info["dtype"].startswith("object") and info["unique"] < 5:
            insights.append(f"'{col}' has few unique values — useful for group comparison.")

    if len(report['suggested_steps']) > 0:
        insights.append("Several preprocessing actions are recommended (see suggested steps).")

    return {
        "auto_insights": insights,
        "recommended_visuals": [
            {"type": "scatter", "x": "Experience", "y": "Salary"},
            {"type": "bar", "x": "Department", "y": "Salary"},
            {"type": "histogram", "column": "Salary"}
        ]
    }

# Natural Language Query Handler using Gemini
async def handle_nl_query(query: str, df: pd.DataFrame):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        columns = list(df.columns)
        preview = df.head(5).to_dict(orient="records")

        prompt = (
            "You are an AI data analyst. "
            "Answer the question based only on this dataset. "
            "Respond strictly in JSON with 'answer' (short explanation), "
            "'evidence' (table or list of values), and optional 'plot' suggestion. "
            f"Dataset columns: {columns}\n"
            f"Sample rows: {preview}\n"
            f"User question: {query}"
        )

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Try to parse JSON, fallback to raw text
        try:
            parsed = json.loads(text)
            return {"mode": "gemini", "response": parsed}
        except Exception:
            return {"mode": "gemini", "response": {"answer": text}}

    except Exception as e:
        return {"mode": "gemini", "error": str(e)}
