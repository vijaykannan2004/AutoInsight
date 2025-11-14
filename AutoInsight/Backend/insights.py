import os
import pandas as pd
import numpy as np
import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
from scipy import stats
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class InsightsGenerator:
    """Advanced AI-powered insights generation with statistical analysis"""

    def __init__(self):
        self.model_pro = None
        self.model_flash = None
        self._initialize_models()

    def _initialize_models(self):
        """Initialize Gemini models"""
        try:
            if GOOGLE_API_KEY:
                genai.configure(api_key=GOOGLE_API_KEY)
                self.model_pro = genai.GenerativeModel("gemini-1.5-pro")
                self.model_flash = genai.GenerativeModel("gemini-1.5-flash")
                print("✅ Gemini models initialized successfully")
            else:
                print("⚠️ No GOOGLE_API_KEY found")
        except Exception as e:
            print(f"⚠️ Failed to initialize Gemini models: {e}")

    def _choose_model(self, data_size: int, complexity: str = "medium"):
        """Choose appropriate model based on data size and complexity"""
        if data_size < 10000 or complexity == "simple":
            return self.model_flash
        else:
            return self.model_pro

    def generate_comprehensive_insights(self, df: pd.DataFrame, cleaning_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive insights combining statistical and AI analysis"""
        insights = {
            "data_overview": self._generate_data_overview(df),
            "statistical_insights": self._generate_statistical_insights(df),
            "pattern_recognition": self._identify_patterns(df),
            "correlation_analysis": self._analyze_correlations(df),
            "anomaly_detection": self._detect_anomalies(df),
            "business_insights": [],
            "recommendations": [],
            "statistical_significance": [],
            "ai_generated_insights": self._generate_ai_insights(df, cleaning_report)
        }

        # Generate business insights using AI
        business_insights = self._generate_business_insights(df, insights)
        insights["business_insights"] = business_insights.get("insights", [])

        # Generate recommendations
        insights["recommendations"] = self._generate_data_recommendations(df, insights)

        return insights

    def _generate_data_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive data overview"""
        overview = {
            "basic_stats": {
                "rows": len(df),
                "columns": len(df.columns),
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
            },
            "data_types": {},
            "quality_metrics": {},
            "completeness": {}
        }

        # Data type breakdown
        for dtype in df.dtypes.unique():
            dtype_name = str(dtype)
            count = len(df.select_dtypes(include=[dtype]).columns)
            overview["data_types"][dtype_name] = count

        # Data quality metrics
        missing_values = df.isnull().sum()
        duplicate_rows = df.duplicated().sum()

        overview["quality_metrics"] = {
            "total_missing": int(missing_values.sum()),
            "missing_percentage": round((missing_values.sum() / (len(df) * len(df.columns))) * 100, 2),
            "duplicate_rows": int(duplicate_rows),
            "duplicate_percentage": round((duplicate_rows / len(df)) * 100, 2),
            "complete_rows": int(len(df) - df.isnull().any(axis=1).sum()),
            "complete_percentage": round(((len(df) - df.isnull().any(axis=1).sum()) / len(df)) * 100, 2)
        }

        # Column-wise completeness
        overview["completeness"] = {
            col: {
                "complete": int(len(df) - missing_values.get(col, 0)),
                "missing": int(missing_values.get(col, 0)),
                "completeness_pct": round(((len(df) - missing_values.get(col, 0)) / len(df)) * 100, 2)
            }
            for col in df.columns
        }

        return overview

    def _generate_statistical_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate detailed statistical insights"""
        insights = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns

        # Numeric statistics
        if len(numeric_cols) > 0:
            insights["numeric_analysis"] = {}
            for col in numeric_cols:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    insights["numeric_analysis"][col] = {
                        "mean": float(col_data.mean()),
                        "median": float(col_data.median()),
                        "std": float(col_data.std()),
                        "min": float(col_data.min()),
                        "max": float(col_data.max()),
                        "q1": float(col_data.quantile(0.25)),
                        "q3": float(col_data.quantile(0.75)),
                        "skewness": float(col_data.skew()),
                        "kurtosis": float(col_data.kurtosis()),
                        "variance": float(col_data.var()),
                        "coefficient_of_variation": float(col_data.std() / col_data.mean()) if col_data.mean() != 0 else 0
                    }

        # Categorical statistics
        if len(categorical_cols) > 0:
            insights["categorical_analysis"] = {}
            for col in categorical_cols:
                value_counts = df[col].value_counts()
                insights["categorical_analysis"][col] = {
                    "unique_count": len(value_counts),
                    "most_frequent": value_counts.index[0] if len(value_counts) > 0 else None,
                    "most_frequent_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                    "least_frequent": value_counts.index[-1] if len(value_counts) > 0 else None,
                    "least_frequent_count": int(value_counts.iloc[-1]) if len(value_counts) > 0 else 0,
                    "entropy": float(stats.entropy(value_counts)),
                    "cardinality_ratio": len(value_counts) / len(df)
                }

        return insights

    def _identify_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify patterns in data"""
        patterns = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns

        # Distribution patterns
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) > 10:
                # Check for normal distribution
                _, p_value = stats.normaltest(data)
                patterns.append({
                    "type": "distribution",
                    "column": col,
                    "pattern": "normal" if p_value > 0.05 else "non-normal",
                    "p_value": float(p_value),
                    "description": f"{col} appears to follow a {'normal' if p_value > 0.05 else 'non-normal'} distribution"
                })

                # Check for outliers
                q1, q3 = data.quantile([0.25, 0.75])
                iqr = q3 - q1
                outliers = ((data < (q1 - 1.5 * iqr)) | (data > (q3 + 1.5 * iqr))).sum()
                if outliers > 0:
                    patterns.append({
                        "type": "outliers",
                        "column": col,
                        "outlier_count": int(outliers),
                        "outlier_percentage": float((outliers / len(data)) * 100),
                        "description": f"{col} has {outliers} outliers ({outliers/len(data)*100:.1f}%)"
                    })

        # Seasonality/Time patterns (if datetime columns exist)
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        if len(datetime_cols) > 0 and len(numeric_cols) > 0:
            for date_col in datetime_cols:
                for num_col in numeric_cols[:2]:  # Limit to avoid too many patterns
                    try:
                        # Simple trend analysis
                        sorted_df = df.sort_values(date_col)
                        x = np.arange(len(sorted_df))
                        y = sorted_df[num_col].dropna().values
                        if len(y) > 10:
                            slope, intercept, r_value, p_value, std_err = stats.linregress(x[:len(y)], y)
                            if p_value < 0.05 and abs(r_value) > 0.3:
                                trend = "increasing" if slope > 0 else "decreasing"
                                patterns.append({
                                    "type": "trend",
                                    "columns": [date_col, num_col],
                                    "trend": trend,
                                    "correlation": float(r_value),
                                    "p_value": float(p_value),
                                    "description": f"{num_col} shows a {trend} trend over {date_col}"
                                })
                    except Exception:
                        continue

        return patterns

    def _analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive correlation analysis"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return {"message": "Insufficient numeric columns for correlation analysis"}

        corr_matrix = df[numeric_cols].corr()

        # Find strong correlations
        strong_correlations = []
        moderate_correlations = []
        weak_correlations = []

        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]

                if abs(corr_val) > 0.7:
                    strong_correlations.append({
                        "columns": [col1, col2],
                        "correlation": float(corr_val),
                        "strength": "strong" if abs(corr_val) > 0.8 else "moderate-strong",
                        "direction": "positive" if corr_val > 0 else "negative"
                    })
                elif abs(corr_val) > 0.3:
                    moderate_correlations.append({
                        "columns": [col1, col2],
                        "correlation": float(corr_val),
                        "strength": "moderate",
                        "direction": "positive" if corr_val > 0 else "negative"
                    })
                elif abs(corr_val) > 0.1:
                    weak_correlations.append({
                        "columns": [col1, col2],
                        "correlation": float(corr_val),
                        "strength": "weak",
                        "direction": "positive" if corr_val > 0 else "negative"
                    })

        return {
            "correlation_matrix": corr_matrix.to_dict(),
            "strong_correlations": strong_correlations,
            "moderate_correlations": moderate_correlations,
            "weak_correlations": weak_correlations,
            "summary": {
                "total_pairs": len(numeric_cols) * (len(numeric_cols) - 1) // 2,
                "strong_pairs": len(strong_correlations),
                "moderate_pairs": len(moderate_correlations),
                "weak_pairs": len(weak_correlations)
            }
        }

    def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in dataset"""
        anomalies = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) > 10:
                # Z-score anomaly detection
                z_scores = np.abs(stats.zscore(data))
                z_anomalies = data[z_scores > 3]
                if len(z_anomalies) > 0:
                    anomalies.append({
                        "column": col,
                        "method": "z_score",
                        "anomaly_count": len(z_anomalies),
                        "anomaly_percentage": float((len(z_anomalies) / len(data)) * 100),
                        "anomaly_values": z_anomalies.tolist()[:10],  # Limit to 10 values
                        "description": f"{len(z_anomalies)} anomalous values detected in {col} using Z-score method"
                    })

                # IQR anomaly detection
                q1, q3 = data.quantile([0.25, 0.75])
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                iqr_anomalies = data[(data < lower_bound) | (data > upper_bound)]
                if len(iqr_anomalies) > 0:
                    anomalies.append({
                        "column": col,
                        "method": "iqr",
                        "anomaly_count": len(iqr_anomalies),
                        "anomaly_percentage": float((len(iqr_anomalies) / len(data)) * 100),
                        "anomaly_values": iqr_anomalies.tolist()[:10],
                        "description": f"{len(iqr_anomalies)} anomalous values detected in {col} using IQR method"
                    })

        return anomalies

    def _generate_ai_insights(self, df: pd.DataFrame, cleaning_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights using Gemini"""
        if not self.model_flash:
            return {"error": "AI model not available"}

        try:
            # Prepare data summary for AI
            summary = {
                "shape": df.shape,
                "columns": list(df.columns),
                "data_types": df.dtypes.to_dict(),
                "numeric_summary": df.describe().to_dict() if not df.empty else {},
                "cleaning_summary": cleaning_report
            }

            prompt = f"""
            Analyze this dataset and provide comprehensive insights.
            Focus on practical business implications and actionable findings.

            Dataset Summary:
            {json.dumps(summary, indent=2, default=str)}

            Provide insights in the following JSON format:
            {{
                "key_findings": ["Finding 1", "Finding 2", ...],
                "business_implications": ["Implication 1", "Implication 2", ...],
                "data_quality_issues": ["Issue 1", "Issue 2", ...],
                "recommended_actions": ["Action 1", "Action 2", ...],
                "opportunity_areas": ["Opportunity 1", "Opportunity 2", ...]
            }}

            Keep insights concise but actionable. Focus on what business users can do with this information.
            """

            model = self._choose_model(len(df))
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean response text and parse JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                ai_insights = json.loads(json_match.group())
            else:
                # Fallback if JSON parsing fails
                ai_insights = {
                    "key_findings": [response_text],
                    "business_implications": [],
                    "data_quality_issues": [],
                    "recommended_actions": [],
                    "opportunity_areas": []
                }

            return ai_insights

        except Exception as e:
            return {"error": f"AI analysis failed: {str(e)}"}

    def _generate_business_insights(self, df: pd.DataFrame, statistical_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business-focused insights"""
        if not self.model_pro:
            return {"insights": ["AI model not available for business insights"]}

        try:
            # Create business context
            context = {
                "dataset_size": len(df),
                "columns": list(df.columns),
                "key_statistics": statistical_insights.get("statistical_insights", {}),
                "patterns": statistical_insights.get("pattern_recognition", []),
                "correlations": statistical_insights.get("correlation_analysis", {})
            }

            prompt = f"""
            Based on this statistical analysis of a business dataset, generate actionable business insights.

            Analysis Context:
            {json.dumps(context, indent=2, default=str)}

            Generate 5-7 business insights that focus on:
            1. Operational efficiency opportunities
            2. Risk management considerations
            3. Performance optimization
            4. Strategic decision support
            5. Cost-saving opportunities

            Format as JSON:
            {{
                "insights": [
                    {{
                        "category": "Operational Efficiency",
                        "insight": "Specific actionable insight",
                        "impact": "High/Medium/Low",
                        "action_items": ["Action 1", "Action 2"]
                    }}
                ]
            }}
            """

            response = self.model_pro.generate_content(prompt)
            response_text = response.text.strip()

            # Parse response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                business_insights = json.loads(json_match.group())
            else:
                business_insights = {"insights": [{"category": "General", "insight": response_text, "impact": "Medium", "action_items": []}]}

            return business_insights

        except Exception as e:
            return {"insights": [f"Business insights generation failed: {str(e)}"]}

    def _generate_data_recommendations(self, df: pd.DataFrame, insights: Dict[str, Any]) -> List[str]:
        """Generate data-driven recommendations"""
        recommendations = []

        # Data quality recommendations
        quality_metrics = insights.get("data_overview", {}).get("quality_metrics", {})
        if quality_metrics.get("missing_percentage", 0) > 5:
            recommendations.append(f"Address missing data ({quality_metrics.get('missing_percentage', 0):.1f}% missing) through imputation or data quality improvements")

        if quality_metrics.get("duplicate_percentage", 0) > 1:
            recommendations.append(f"Remove duplicate rows ({quality_metrics.get('duplicate_percentage', 0):.1f}% duplicates) to improve data quality")

        # Analysis recommendations
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            corr_analysis = insights.get("correlation_analysis", {})
            strong_pairs = corr_analysis.get("strong_correlations", [])
            if strong_pairs:
                recommendations.append("Investigate strong correlations for potential feature engineering or multicollinearity issues")

        # Anomaly recommendations
        anomalies = insights.get("anomaly_detection", [])
        if anomalies:
            recommendations.append("Review detected anomalies for data entry errors or genuine outliers that may require special treatment")

        # Pattern-based recommendations
        patterns = insights.get("pattern_recognition", [])
        non_normal = [p for p in patterns if p.get("pattern") == "non-normal"]
        if non_normal:
            recommendations.append("Consider data transformations for non-normal distributions to improve analysis accuracy")

        # Business recommendations from AI insights
        ai_insights = insights.get("ai_generated_insights", {})
        if "recommended_actions" in ai_insights:
            recommendations.extend(ai_insights["recommended_actions"])

        return list(set(recommendations))  # Remove duplicates

    async def handle_nl_query(self, query: str, df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle natural language queries with enhanced context"""
        if not self.model_flash:
            return {"error": "AI model not available for query processing"}

        try:
            # Enhanced context preparation
            columns = list(df.columns)
            preview = df.head(10).to_dict(orient="records")  # More rows for better context
            dtypes = df.dtypes.to_dict()
            numeric_summary = df.describe().to_dict() if not df.empty else {}

            # Additional context
            if context:
                context_str = f"\nAdditional Context: {json.dumps(context, default=str)}"
            else:
                context_str = ""

            prompt = f"""
            You are an expert data analyst. Answer the user's question based on this dataset.

            Dataset Information:
            - Columns: {columns}
            - Data types: {dtypes}
            - Sample data: {preview}
            - Statistical summary: {numeric_summary}
            {context_str}

            User question: {query}

            Provide a comprehensive response in JSON format:
            {{
                "answer": "Clear, concise answer to the question",
                "evidence": {{
                    "data_points": [...],
                    "statistics": {...},
                    "source": "Based on dataset analysis"
                }},
                "visualization_suggestion": {{
                    "type": "recommended chart type",
                    "x_column": "x-axis column",
                    "y_column": "y-axis column",
                    "title": "Descriptive chart title"
                }},
                "follow_up_questions": ["Question 1", "Question 2"],
                "confidence": "High/Medium/Low"
            }}

            If you cannot answer based on the available data, state this clearly.
            Use only the provided dataset information.
            """

            model = self._choose_model(len(df))
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # Parse JSON response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "mode": "gemini",
                    "response": parsed,
                    "query": query,
                    "timestamp": pd.Timestamp.now().isoformat()
                }
            else:
                return {
                    "mode": "gemini",
                    "response": {
                        "answer": response_text,
                        "evidence": {"source": "AI generated response"},
                        "confidence": "Medium"
                    }
                }

        except Exception as e:
            return {
                "mode": "gemini",
                "error": f"Query processing failed: {str(e)}",
                "query": query
            }

# Legacy functions for backward compatibility
insights_generator = InsightsGenerator()

def generate_insights(report, df):
    """Legacy function - use InsightsGenerator class for new implementations"""
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

async def handle_nl_query(query: str, df: pd.DataFrame):
    """Legacy function - use InsightsGenerator class for new implementations"""
    return await insights_generator.handle_nl_query(query, df)

if __name__ == "__main__":
    # Test insights generator
    from data_cleaner import DataCleaner

    # Create sample data
    np.random.seed(42)
    df = pd.DataFrame({
        "age": np.random.randint(18, 65, 100),
        "salary": np.random.normal(75000, 25000, 100),
        "department": np.random.choice(["IT", "HR", "Finance", "Marketing"], 100),
        "experience": np.random.exponential(5, 100),
        "performance": np.random.uniform(3.0, 5.0, 100)
    })

    # Add correlations
    df["salary"] = df["salary"] + df["age"] * 1000 + df["experience"] * 5000

    generator = InsightsGenerator()

    # Test insights generation
    print("Testing insights generation...")
    insights = generator.generate_comprehensive_insights(df, {})
    print(f"Generated {len(insights)} insight categories")

    # Test NL query
    async def test_query():
        result = await generator.handle_nl_query("What is the average salary by department?", df)
        print("Query result:", result.get("response", {}).get("answer", "No answer"))

    # Run async test
    asyncio.run(test_query())
    print("Insights generator tests completed!")
