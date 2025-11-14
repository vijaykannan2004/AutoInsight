import os
import pandas as pd
import numpy as np
import json
import asyncio
from io import StringIO, BytesIO
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Import enhanced modules
from data_cleaner import DataCleaner
from insights import InsightsGenerator
from visualization import ChartGenerator
from export import DataExporter

# -----------------------------
# 1️⃣ App Setup
# -----------------------------
app = FastAPI(
    title="AutoInsight API",
    description="AI-Powered Data Analytics Platform",
    version="2.0.0"
)

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
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
print("Google API Key loaded:", "✅" if GOOGLE_API_KEY else "⚠️")

# -----------------------------
# 3️⃣ Initialize Services
# -----------------------------
data_cleaner = DataCleaner()
insights_generator = InsightsGenerator()
chart_generator = ChartGenerator()
data_exporter = DataExporter()

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
# 5️⃣ Pydantic Models
# -----------------------------
class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class ExportRequest(BaseModel):
    format: str
    data_id: Optional[str] = None
    chart_configs: Optional[List[Dict[str, Any]]] = None

class ChartRequest(BaseModel):
    chart_type: str
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    title: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

# -----------------------------
# 6️⃣ Data Storage (In-memory for demo)
# -----------------------------
# In production, this would be a database
data_storage = {}
analysis_cache = {}

# -----------------------------
# 7️⃣ Utility Functions
# -----------------------------
def generate_cleaning_report(df: pd.DataFrame):
    """Legacy function for backward compatibility"""
    return data_cleaner.auto_clean_report(df)

def generate_ai_insights_legacy(report):
    """Legacy AI insights generation"""
    if not insights_generator.model_flash:
        return "AI analysis skipped (no valid API key)."

    prompt = f"""
    Analyze this dataset summary and correlations.
    Give clear, concise business insights (3–5 bullet points).
    Data summary:
    {report}
    """

    try:
        response = insights_generator.model_flash.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI analysis failed: {str(e)}"

# -----------------------------
# 8️⃣ Routes
# -----------------------------
@app.get("/")
async def home():
    if os.path.exists(index_html):
        return FileResponse(index_html)
    else:
        return {"message": "Frontend not found. Please ensure index.html exists."}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "data_cleaner": "✅",
            "insights_generator": "✅" if insights_generator.model_flash else "⚠️",
            "chart_generator": "✅",
            "data_exporter": "✅"
        },
        "api_key_configured": bool(GOOGLE_API_KEY)
    }

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Enhanced CSV upload with basic analysis (legacy endpoint)"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid CSV file.")

    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))

        # Store data in memory for later analysis
        data_id = f"data_{len(data_storage)}"
        data_storage[data_id] = df

        report = generate_cleaning_report(df)
        insights = generate_ai_insights_legacy(report)

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
            "data_id": data_id,
            "filename": file.filename,
            "cleaning_report": report,
            "ai_insights": insights,
            "data": data_summary,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing file: {str(e)}")

@app.post("/upload/enhanced")
async def upload_enhanced(file: UploadFile = File(...)):
    """Enhanced analysis endpoint with comprehensive insights"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid CSV file.")

    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))

        # Store data in memory for later analysis
        data_id = f"data_{len(data_storage)}"
        data_storage[data_id] = df

        # Advanced data cleaning and analysis
        cleaned_df, cleaning_report = data_cleaner.clean_dataset(df)

        # Generate comprehensive insights
        insights = insights_generator.generate_comprehensive_insights(cleaned_df, cleaning_report)

        # Generate auto-charts
        charts_result = chart_generator.generate_auto_charts(cleaned_df, max_charts=6)

        # Create enhanced response
        response = {
            "status": "success",
            "data_id": data_id,
            "filename": file.filename,
            "original_shape": cleaning_report["original_shape"],
            "cleaned_shape": cleaning_report["cleaned_shape"],
            "cleaning_report": cleaning_report,
            "insights": insights,
            "charts": charts_result,
            "data_preview": {
                "columns": list(cleaned_df.columns),
                "dtypes": {col: str(cleaned_df[col].dtype) for col in cleaned_df.columns},
                "sample_data": cleaned_df.head(10).to_dict(orient="records")
            }
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in enhanced analysis: {str(e)}")

@app.post("/query")
async def natural_language_query(request: QueryRequest, data_id: str):
    """Natural language query processing"""
    if data_id not in data_storage:
        raise HTTPException(status_code=404, detail="Data not found")

    try:
        df = data_storage[data_id]
        result = await insights_generator.handle_nl_query(
            request.query,
            df,
            request.context
        )

        return {
            "status": "success",
            "data_id": data_id,
            "query": request.query,
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/visualize")
async def create_visualization(request: ChartRequest, data_id: str):
    """Create custom visualization"""
    if data_id not in data_storage:
        raise HTTPException(status_code=404, detail="Data not found")

    try:
        df = data_storage[data_id]

        # Apply filters if provided
        if request.filters:
            df = chart_generator.filter_data_for_chart(df, request.filters)

        # Create chart
        chart_params = {
            "x_column": request.x_column,
            "y_column": request.y_column,
            "color_column": request.color_column,
            "title": request.title
        }

        chart = chart_generator.create_chart(df, request.chart_type, **chart_params)

        if not chart:
            raise HTTPException(status_code=400, detail=f"Failed to create {request.chart_type} chart")

        return {
            "status": "success",
            "data_id": data_id,
            "chart": chart
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating visualization: {str(e)}")

@app.get("/charts/recommendations/{data_id}")
async def get_chart_recommendations(data_id: str):
    """Get chart recommendations for dataset"""
    if data_id not in data_storage:
        raise HTTPException(status_code=404, detail="Data not found")

    try:
        df = data_storage[data_id]
        recommendations = chart_generator.recommend_chart_types(df)

        return {
            "status": "success",
            "data_id": data_id,
            "recommendations": recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@app.post("/export/data")
async def export_data(request: ExportRequest, data_id: str):
    """Export dataset to various formats"""
    if data_id not in data_storage:
        raise HTTPException(status_code=404, detail="Data not found")

    try:
        df = data_storage[data_id]
        result = data_exporter.export_data(df, request.format)

        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "status": "success",
            "data_id": data_id,
            "export": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")

@app.post("/export/chart")
async def export_chart(request: ExportRequest, data_id: str):
    """Export chart to various formats"""
    if not request.chart_configs:
        raise HTTPException(status_code=400, detail="No chart configurations provided")

    try:
        exports = []
        for chart_config in request.chart_configs:
            result = data_exporter.export_chart(
                chart_config,
                request.format
            )

            if result.get("error"):
                exports.append({
                    "chart_id": chart_config.get("id", "unknown"),
                    "error": result["error"]
                })
            else:
                exports.append(result)

        return {
            "status": "success",
            "data_id": data_id,
            "exports": exports
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting charts: {str(e)}")

@app.post("/export/report")
async def export_analysis_report(request: ExportRequest, data_id: str):
    """Generate and export comprehensive analysis report"""
    if data_id not in data_storage:
        raise HTTPException(status_code=404, detail="Data not found")

    try:
        df = data_storage[data_id]

        # Get cached analysis or generate new one
        if data_id in analysis_cache:
            analysis_results = analysis_cache[data_id]
        else:
            cleaned_df, cleaning_report = data_cleaner.clean_dataset(df)
            analysis_results = {
                "filename": f"dataset_{data_id}",
                "cleaning_report": cleaning_report,
                "insights": insights_generator.generate_comprehensive_insights(cleaned_df, cleaning_report)
            }
            analysis_cache[data_id] = analysis_results

        charts = []  # Could include charts in the future
        result = data_exporter.generate_analysis_report(
            df,
            analysis_results,
            charts,
            request.format
        )

        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "status": "success",
            "data_id": data_id,
            "export": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/data/{data_id}/preview")
async def get_data_preview(data_id: str, limit: int = 100):
    """Get data preview with pagination"""
    if data_id not in data_storage:
        raise HTTPException(status_code=404, detail="Data not found")

    try:
        df = data_storage[data_id]
        preview_data = df.head(limit).to_dict(orient="records")

        return {
            "status": "success",
            "data_id": data_id,
            "total_rows": len(df),
            "preview_rows": len(preview_data),
            "columns": list(df.columns),
            "data": preview_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting data preview: {str(e)}")

@app.delete("/data/{data_id}")
async def clear_data(data_id: str):
    """Clear data from memory"""
    if data_id in data_storage:
        del data_storage[data_id]

    if data_id in analysis_cache:
        del analysis_cache[data_id]

    return {"status": "success", "message": f"Data {data_id} cleared"}

@app.get("/datasets")
async def list_datasets():
    """List all active datasets"""
    datasets = []
    for data_id, df in data_storage.items():
        datasets.append({
            "data_id": data_id,
            "rows": len(df),
            "columns": len(df.columns),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        })

    return {
        "status": "success",
        "count": len(datasets),
        "datasets": datasets
    }

# -----------------------------
# 9️⃣ Run command (for local testing)
# -----------------------------
# uvicorn app:app --reload --port 8000
