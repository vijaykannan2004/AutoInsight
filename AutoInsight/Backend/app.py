import os
import pandas as pd
import numpy as np
from io import StringIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import google.generativeai as genai

# -----------------------------
# 1️⃣ App Setup
# -----------------------------
app = FastAPI(title="AutoInsight API")

# Enable CORS (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# 2️⃣ Load Environment Variables
# -----------------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # ✅ Correct variable name
print("Loaded Key =", GOOGLE_API_KEY)


# -----------------------------
# 3️⃣ Configure Gemini API
# -----------------------------
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-pro")
        print("✅ Google Gemini connected successfully.")
    except Exception as e:
        print("⚠️ Gemini init failed:", e)
        model = None
else:
    print("⚠️ No GOOGLE_API_KEY found. Skipping AI insights.")
    model = None

# -----------------------------
# 4️⃣ Static Files Setup
# -----------------------------
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Frontend"))
static_dir = os.path.join(frontend_dir, "static")
index_html = os.path.join(frontend_dir, "index.html")

if not os.path.exists(static_dir):
    print("⚠️ Warning: Frontend static directory not found!")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# -----------------------------
# 5️⃣ Utility Functions
# -----------------------------
def generate_cleaning_report(df: pd.DataFrame):
    report = {}
    report["rows"], report["cols"] = df.shape
    report["missing_counts"] = df.isnull().sum().to_dict()

    col_info = {}
    for col in df.columns:
        col_info[col] = {
            "dtype": str(df[col].dtype),
            "unique": int(df[col].nunique()),
            "sample_values": df[col].dropna().unique()[:5].tolist(),
        }
    report["columns"] = col_info

    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        report["numeric_summary"] = numeric_df.describe().to_dict()
        corr = numeric_df.corr()
        corr_pairs = []
        for c1 in corr.columns:
            for c2 in corr.columns:
                if c1 != c2:
                    corr_pairs.append((c1, c2, round(corr[c1][c2], 3)))
        corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        report["highly_correlated_pairs"] = corr_pairs[:6]
    else:
        report["numeric_summary"] = {}
        report["highly_correlated_pairs"] = []

    return report


def generate_ai_insights(report):
    if not model:
        return "AI analysis skipped (no valid API key)."

    prompt = f"""
    Analyze this dataset summary and correlations.
    Give clear, concise business insights (3–5 bullet points).
    Data summary:
    {report}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI analysis failed: {str(e)}"


# -----------------------------
# 6️⃣ Routes
# -----------------------------
@app.get("/")
async def home():
    if os.path.exists(index_html):
        return FileResponse(index_html)
    else:
        return {"message": "Frontend not found. Please ensure index.html exists."}


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid CSV file.")

    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))

        report = generate_cleaning_report(df)
        insights = generate_ai_insights(report)

        data_summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {
                col: {
                    "type": str(df[col].dtype),
                    "missing": int(df[col].isnull().sum()),
                    "unique_count": int(df[col].nunique()),
                    "sample_values": df[col].dropna().head(10).tolist(),
                }
                for col in df.columns
            },
        }

        return {
            "status": "success",
            "filename": file.filename,
            "cleaning_report": report,
            "ai_insights": insights,
            "data": data_summary,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing file: {str(e)}")


# -----------------------------
# 7️⃣ Run command (for local testing)
# -----------------------------
# uvicorn app:app --reload --port 8000
