import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.utils
from typing import Dict, List, Any, Optional, Tuple
import json

class ChartGenerator:
    """Generate interactive Plotly.js charts for data visualization"""

    def __init__(self):
        self.chart_count = 0
        self.charts = []

    def get_chart_id(self) -> str:
        """Generate unique chart ID"""
        self.chart_count += 1
        return f"chart_{self.chart_count}"

    def recommend_chart_types(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Recommend appropriate chart types based on data characteristics"""
        recommendations = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        # Numeric vs Numeric: Scatter plots
        if len(numeric_cols) >= 2:
            for i, col1 in enumerate(numeric_cols[:3]):  # Limit to top 3 combinations
                for col2 in numeric_cols[i+1:4]:  # Limit combinations
                    recommendations.append({
                        "type": "scatter",
                        "title": f"{col1} vs {col2}",
                        "x_column": col1,
                        "y_column": col2,
                        "description": f"Relationship between {col1} and {col2}",
                        "priority": "high"
                    })

        # Numeric vs Categorical: Box plots, Bar charts
        if numeric_cols and categorical_cols:
            for num_col in numeric_cols[:2]:  # Limit to top 2 numeric columns
                for cat_col in categorical_cols[:2]:  # Limit to top 2 categorical columns
                    if df[cat_col].nunique() <= 20:  # Reasonable cardinality
                        recommendations.append({
                            "type": "box",
                            "title": f"{num_col} by {cat_col}",
                            "x_column": cat_col,
                            "y_column": num_col,
                            "description": f"Distribution of {num_col} across {cat_col} categories",
                            "priority": "high"
                        })

                        recommendations.append({
                            "type": "bar",
                            "title": f"Average {num_col} by {cat_col}",
                            "x_column": cat_col,
                            "y_column": num_col,
                            "description": f"Average {num_col} for each {cat_col}",
                            "priority": "medium"
                        })

        # Single Numeric: Histograms, Distribution plots
        for col in numeric_cols[:3]:  # Limit to top 3 numeric columns
            recommendations.append({
                "type": "histogram",
                "title": f"Distribution of {col}",
                "x_column": col,
                "description": f"Frequency distribution of {col} values",
                "priority": "high"
            })

        # Categorical vs Categorical: Heatmaps (for low cardinality)
        if len(categorical_cols) >= 2:
            for i, col1 in enumerate(categorical_cols[:2]):
                for col2 in categorical_cols[i+1:3]:
                    if df[col1].nunique() <= 10 and df[col2].nunique() <= 10:
                        recommendations.append({
                            "type": "heatmap",
                            "title": f"{col1} vs {col2} Heatmap",
                            "x_column": col2,
                            "y_column": col1,
                            "description": f"Cross-tabulation between {col1} and {col2}",
                            "priority": "medium"
                        })

        # Time series: Line charts
        if datetime_cols and numeric_cols:
            for date_col in datetime_cols:
                for num_col in numeric_cols[:2]:
                    recommendations.append({
                        "type": "line",
                        "title": f"{num_col} over Time",
                        "x_column": date_col,
                        "y_column": num_col,
                        "description": f"Trend of {num_col} over time",
                        "priority": "high"
                    })

        # Correlation heatmap
        if len(numeric_cols) >= 2:
            recommendations.append({
                "type": "correlation",
                "title": "Correlation Matrix",
                "description": "Correlation between all numeric variables",
                "priority": "high"
            })

        # Sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)

        return recommendations[:8]  # Return top 8 recommendations

    def create_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str,
                           color_col: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        """Create a scatter plot"""
        chart_id = self.get_chart_id()

        if not title:
            title = f"{y_col} vs {x_col}"

        fig = px.scatter(
            df, x=x_col, y=y_col, color=color_col,
            title=title,
            template="plotly_white",
            hover_data=[x_col, y_col] + ([color_col] if color_col else [])
        )

        fig.update_layout(
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            showlegend=color_col is not None,
            height=500,
            margin=dict(l=40, r=40, t=60, b=40)
        )

        return {
            "id": chart_id,
            "type": "scatter",
            "title": title,
            "config": fig.to_json(),
            "description": f"Scatter plot showing relationship between {x_col} and {y_col}"
        }

    def create_histogram(self, df: pd.DataFrame, col: str, bins: int = 30,
                        title: Optional[str] = None) -> Dict[str, Any]:
        """Create a histogram"""
        chart_id = self.get_chart_id()

        if not title:
            title = f"Distribution of {col}"

        fig = px.histogram(
            df, x=col, nbins=bins,
            title=title,
            template="plotly_white",
            marginal="box"
        )

        fig.update_layout(
            xaxis_title=col.replace('_', ' ').title(),
            yaxis_title="Frequency",
            height=500,
            margin=dict(l=40, r=40, t=60, b=40)
        )

        return {
            "id": chart_id,
            "type": "histogram",
            "title": title,
            "config": fig.to_json(),
            "description": f"Histogram showing distribution of {col} values"
        }

    def create_box_plot(self, df: pd.DataFrame, x_col: str, y_col: str,
                       title: Optional[str] = None) -> Dict[str, Any]:
        """Create a box plot"""
        chart_id = self.get_chart_id()

        if not title:
            title = f"{y_col} by {x_col}"

        fig = px.box(
            df, x=x_col, y=y_col,
            title=title,
            template="plotly_white"
        )

        # Rotate x-axis labels if there are many categories
        if df[x_col].nunique() > 5:
            fig.update_xaxes(tickangle=45)

        fig.update_layout(
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            height=500,
            margin=dict(l=40, r=40, t=60, b=80)
        )

        return {
            "id": chart_id,
            "type": "box",
            "title": title,
            "config": fig.to_json(),
            "description": f"Box plot showing {y_col} distribution across {x_col} categories"
        }

    def create_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                       aggregation: str = "mean", title: Optional[str] = None) -> Dict[str, Any]:
        """Create a bar chart with aggregation"""
        chart_id = self.get_chart_id()

        if not title:
            agg_name = aggregation.title()
            title = f"{agg_name} {y_col} by {x_col}"

        # Perform aggregation
        if aggregation == "mean":
            agg_df = df.groupby(x_col)[y_col].mean().reset_index()
            agg_col = f"{aggregation}_{y_col}"
            agg_df[agg_col] = agg_df[y_col]
        elif aggregation == "sum":
            agg_df = df.groupby(x_col)[y_col].sum().reset_index()
            agg_col = f"{aggregation}_{y_col}"
            agg_df[agg_col] = agg_df[y_col]
        elif aggregation == "count":
            agg_df = df.groupby(x_col)[y_col].count().reset_index()
            agg_col = f"{aggregation}_{y_col}"
            agg_df[agg_col] = agg_df[y_col]
        else:
            agg_df = df.groupby(x_col)[y_col].mean().reset_index()
            agg_col = f"mean_{y_col}"
            agg_df[agg_col] = agg_df[y_col]

        fig = px.bar(
            agg_df, x=x_col, y=agg_col,
            title=title,
            template="plotly_white"
        )

        # Rotate x-axis labels if there are many categories
        if df[x_col].nunique() > 5:
            fig.update_xaxes(tickangle=45)

        fig.update_layout(
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=f"{aggregation.title()} {y_col}".replace('_', ' ').title(),
            height=500,
            margin=dict(l=40, r=40, t=60, b=80)
        )

        return {
            "id": chart_id,
            "type": "bar",
            "title": title,
            "config": fig.to_json(),
            "description": f"Bar chart showing {aggregation} {y_col} by {x_col}"
        }

    def create_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                        color_col: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        """Create a line chart (time series)"""
        chart_id = self.get_chart_id()

        if not title:
            title = f"{y_col} over Time"

        # Sort by x_col for proper line drawing
        df_sorted = df.sort_values(x_col)

        fig = px.line(
            df_sorted, x=x_col, y=y_col, color=color_col,
            title=title,
            template="plotly_white"
        )

        fig.update_layout(
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            showlegend=color_col is not None,
            height=500,
            margin=dict(l=40, r=40, t=60, b=40)
        )

        return {
            "id": chart_id,
            "type": "line",
            "title": title,
            "config": fig.to_json(),
            "description": f"Line chart showing {y_col} trends over {x_col}"
        }

    def create_heatmap(self, df: pd.DataFrame, x_col: str, y_col: str,
                      title: Optional[str] = None) -> Dict[str, Any]:
        """Create a heatmap for categorical cross-tabulation"""
        chart_id = self.get_chart_id()

        if not title:
            title = f"{y_col} vs {x_col} Heatmap"

        # Create cross-tabulation
        crosstab = pd.crosstab(df[y_col], df[x_col])

        fig = px.imshow(
            crosstab,
            title=title,
            template="plotly_white",
            labels=dict(x=x_col, y=y_col, color="Count"),
            aspect="auto"
        )

        fig.update_layout(
            height=500,
            margin=dict(l=80, r=40, t=60, b=80)
        )

        return {
            "id": chart_id,
            "type": "heatmap",
            "title": title,
            "config": fig.to_json(),
            "description": f"Heatmap showing frequency distribution between {x_col} and {y_col}"
        }

    def create_correlation_heatmap(self, df: pd.DataFrame, title: Optional[str] = None) -> Dict[str, Any]:
        """Create a correlation matrix heatmap"""
        chart_id = self.get_chart_id()

        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return None

        if not title:
            title = "Correlation Matrix"

        corr_matrix = numeric_df.corr()

        fig = px.imshow(
            corr_matrix,
            title=title,
            template="plotly_white",
            labels=dict(x="Variable", y="Variable", color="Correlation"),
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmid=0
        )

        fig.update_layout(
            height=500,
            margin=dict(l=80, r=40, t=60, b=80)
        )

        return {
            "id": chart_id,
            "type": "correlation",
            "title": title,
            "config": fig.to_json(),
            "description": "Correlation heatmap showing relationships between numeric variables"
        }

    def create_chart(self, df: pd.DataFrame, chart_type: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Create a chart based on type and parameters"""
        try:
            if chart_type == "scatter":
                return self.create_scatter_plot(df, kwargs.get("x_column"), kwargs.get("y_column"),
                                              kwargs.get("color_column"), kwargs.get("title"))
            elif chart_type == "histogram":
                return self.create_histogram(df, kwargs.get("x_column"),
                                           kwargs.get("bins", 30), kwargs.get("title"))
            elif chart_type == "box":
                return self.create_box_plot(df, kwargs.get("x_column"), kwargs.get("y_column"),
                                          kwargs.get("title"))
            elif chart_type == "bar":
                return self.create_bar_chart(df, kwargs.get("x_column"), kwargs.get("y_column"),
                                          kwargs.get("aggregation", "mean"), kwargs.get("title"))
            elif chart_type == "line":
                return self.create_line_chart(df, kwargs.get("x_column"), kwargs.get("y_column"),
                                           kwargs.get("color_column"), kwargs.get("title"))
            elif chart_type == "heatmap":
                return self.create_heatmap(df, kwargs.get("x_column"), kwargs.get("y_column"),
                                        kwargs.get("title"))
            elif chart_type == "correlation":
                return self.create_correlation_heatmap(df, kwargs.get("title"))
            else:
                return None
        except Exception as e:
            print(f"Error creating {chart_type} chart: {str(e)}")
            return None

    def generate_auto_charts(self, df: pd.DataFrame, max_charts: int = 6) -> Dict[str, Any]:
        """Automatically generate recommended charts"""
        recommendations = self.recommend_chart_types(df)
        charts = []

        # Sample data if dataset is too large
        df_sample = df.sample(n=min(10000, len(df)), random_state=42) if len(df) > 10000 else df

        for rec in recommendations[:max_charts]:
            chart = self.create_chart(df_sample, rec["type"], **rec)
            if chart:
                charts.append(chart)

        return {
            "charts": charts,
            "recommendations": recommendations[max_charts:],  # Remaining recommendations
            "total_generated": len(charts),
            "data_sample_size": len(df_sample)
        }

    def filter_data_for_chart(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to dataset for chart updates"""
        df_filtered = df.copy()

        for column, filter_config in filters.items():
            if column not in df.columns:
                continue

            filter_type = filter_config.get("type", "value")

            if filter_type == "value":
                # Specific value filter
                values = filter_config.get("values", [])
                if values:
                    df_filtered = df_filtered[df_filtered[column].isin(values)]

            elif filter_type == "range":
                # Range filter for numeric columns
                min_val = filter_config.get("min")
                max_val = filter_config.get("max")
                if min_val is not None:
                    df_filtered = df_filtered[df_filtered[column] >= min_val]
                if max_val is not None:
                    df_filtered = df_filtered[df_filtered[column] <= max_val]

            elif filter_type == "search":
                # Text search filter
                search_term = filter_config.get("term", "").lower()
                if search_term:
                    df_filtered = df_filtered[df_filtered[column].astype(str).str.lower().str.contains(search_term)]

        return df_filtered

    def export_chart(self, chart_config: Dict[str, Any], format: str = "png",
                    width: int = 1200, height: int = 600) -> Dict[str, Any]:
        """Export chart configuration for frontend rendering"""
        return {
            "chart_id": chart_config["id"],
            "format": format,
            "dimensions": {"width": width, "height": height},
            "config": chart_config["config"],
            "title": chart_config["title"],
            "type": chart_config["type"]
        }

def generate_sample_data() -> pd.DataFrame:
    """Generate sample data for testing"""
    np.random.seed(42)
    n_samples = 1000

    data = {
        "age": np.random.randint(18, 65, n_samples),
        "salary": np.random.normal(75000, 25000, n_samples),
        "experience": np.random.exponential(5, n_samples),
        "department": np.random.choice(["IT", "HR", "Finance", "Marketing", "Sales"], n_samples),
        "performance_score": np.random.uniform(3.0, 5.0, n_samples),
        "date_joined": pd.date_range("2018-01-01", "2023-12-31", periods=n_samples)
    }

    # Add some correlations
    data["salary"] = data["salary"] + data["age"] * 1000 + data["experience"] * 5000
    data["salary"] = np.clip(data["salary"], 30000, 150000)

    # Ensure performance has relationship with experience
    data["performance_score"] = data["performance_score"] + data["experience"] * 0.05
    data["performance_score"] = np.clip(data["performance_score"], 3.0, 5.0)

    return pd.DataFrame(data)

if __name__ == "__main__":
    # Test the chart generator
    df = generate_sample_data()
    generator = ChartGenerator()

    # Generate auto charts
    result = generator.generate_auto_charts(df, max_charts=4)

    print("Generated Charts:")
    for chart in result["charts"]:
        print(f"- {chart['title']} ({chart['type']})")

    print(f"\nTotal charts generated: {result['total_generated']}")
    print(f"Data sample size: {result['data_sample_size']}")

    # Test individual chart creation
    scatter_chart = generator.create_scatter_plot(df, "age", "salary", "department")
    if scatter_chart:
        print(f"\nSample chart created: {scatter_chart['title']} (ID: {scatter_chart['id']})")