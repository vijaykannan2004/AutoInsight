import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from scipy import stats
import json
from typing import Dict, List, Tuple, Optional, Any

class DataCleaner:
    """Advanced data cleaning and preprocessing pipeline"""

    def __init__(self):
        self.cleaning_log = []
        self.original_shape = None
        self.cleaning_applied = {
            "missing_values_handled": 0,
            "duplicates_removed": 0,
            "outliers_removed": 0,
            "data_types_converted": 0
        }

    def detect_outliers_iqr(self, series: pd.Series, multiplier: float = 1.5) -> pd.Series:
        """Detect outliers using IQR method"""
        if series.dtype not in ['int64', 'float64']:
            return pd.Series([False] * len(series))

        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR

        return (series < lower_bound) | (series > upper_bound)

    def detect_outliers_zscore(self, series: pd.Series, threshold: float = 3.0) -> pd.Series:
        """Detect outliers using Z-score method"""
        if series.dtype not in ['int64', 'float64']:
            return pd.Series([False] * len(series))

        z_scores = np.abs(stats.zscore(series.dropna()))
        return pd.Series(z_scores > threshold, index=series.index).reindex(series.index, fill_value=False)

    def detect_outliers_isolation_forest(self, df: pd.DataFrame, contamination: float = 0.1) -> pd.Series:
        """Detect outliers using Isolation Forest"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return pd.Series([False] * len(df))

        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        outliers = iso_forest.fit_predict(df[numeric_cols].fillna(df[numeric_cols].median()))
        return pd.Series(outliers == -1, index=df.index)

    def handle_missing_values(self, df: pd.DataFrame, strategy: str = "auto") -> pd.DataFrame:
        """Handle missing values with various strategies"""
        df_clean = df.copy()
        missing_handled = 0

        for col in df.columns:
            if df[col].isnull().any():
                missing_count = df[col].isnull().sum()

                if df[col].dtype in ['int64', 'float64']:
                    if strategy == "auto":
                        df_clean[col].fillna(df[col].median(), inplace=True)
                    elif strategy == "mean":
                        df_clean[col].fillna(df[col].mean(), inplace=True)
                    elif strategy == "median":
                        df_clean[col].fillna(df[col].median(), inplace=True)
                    elif strategy == "mode":
                        df_clean[col].fillna(df[col].mode().iloc[0], inplace=True)
                    elif strategy == "interpolate":
                        df_clean[col] = df_clean[col].interpolate()
                else:
                    if strategy == "auto" or strategy == "mode":
                        mode_val = df[col].mode()
                        if len(mode_val) > 0:
                            df_clean[col].fillna(mode_val.iloc[0], inplace=True)
                        else:
                            df_clean[col].fillna("Unknown", inplace=True)
                    elif strategy == "constant":
                        df_clean[col].fillna("Unknown", inplace=True)

                missing_handled += missing_count
                self.cleaning_log.append(f"Filled {missing_count} missing values in {col}")

        self.cleaning_applied["missing_values_handled"] = missing_handled
        return df_clean

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows"""
        original_count = len(df)
        df_clean = df.drop_duplicates()
        duplicates_removed = original_count - len(df_clean)

        if duplicates_removed > 0:
            self.cleaning_log.append(f"Removed {duplicates_removed} duplicate rows")
            self.cleaning_applied["duplicates_removed"] = duplicates_removed

        return df_clean

    def remove_outliers(self, df: pd.DataFrame, method: str = "iqr",
                       sensitivity: str = "medium") -> pd.DataFrame:
        """Remove outliers using specified method"""
        df_clean = df.copy()
        outliers_mask = pd.Series([False] * len(df))

        # Set parameters based on sensitivity
        if sensitivity == "low":
            multiplier = 2.5
            threshold = 3.5
            contamination = 0.05
        elif sensitivity == "high":
            multiplier = 1.0
            threshold = 2.0
            contamination = 0.15
        else:  # medium
            multiplier = 1.5
            threshold = 3.0
            contamination = 0.1

        for col in df.select_dtypes(include=[np.number]).columns:
            if method == "iqr":
                col_outliers = self.detect_outliers_iqr(df[col], multiplier)
            elif method == "zscore":
                col_outliers = self.detect_outliers_zscore(df[col], threshold)
            elif method == "isolation_forest":
                col_outliers = self.detect_outliers_isolation_forest(df, contamination)
            else:
                continue

            outliers_mask = outliers_mask | col_outliers

        outliers_removed = outliers_mask.sum()
        df_clean = df_clean[~outliers_mask]

        if outliers_removed > 0:
            self.cleaning_log.append(f"Removed {outliers_removed} outliers using {method} method")
            self.cleaning_applied["outliers_removed"] = outliers_removed

        return df_clean

    def convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Automatically detect and convert data types"""
        df_clean = df.copy()
        converted_count = 0

        for col in df.columns:
            # Try to convert object columns to more appropriate types
            if df[col].dtype == 'object':
                # Try datetime conversion
                try:
                    df_clean[col] = pd.to_datetime(df[col])
                    self.cleaning_log.append(f"Converted {col} to datetime")
                    converted_count += 1
                    continue
                except:
                    pass

                # Try numeric conversion
                try:
                    df_clean[col] = pd.to_numeric(df[col])
                    self.cleaning_log.append(f"Converted {col} to numeric")
                    converted_count += 1
                    continue
                except:
                    pass

                # Convert to categorical if low cardinality
                if df[col].nunique() / len(df) < 0.5 and df[col].nunique() < 100:
                    df_clean[col] = df[col].astype('category')
                    self.cleaning_log.append(f"Converted {col} to categorical")
                    converted_count += 1

        self.cleaning_applied["data_types_converted"] = converted_count
        return df_clean

    def standardize_data(self, df: pd.DataFrame, method: str = "z-score",
                        columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Standardize/normalize numeric data"""
        df_clean = df.copy()
        numeric_cols = columns or df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_cols:
            return df_clean

        if method == "z-score":
            scaler = StandardScaler()
        elif method == "min-max":
            scaler = MinMaxScaler()
        else:
            return df_clean

        df_clean[numeric_cols] = scaler.fit_transform(df_clean[numeric_cols])
        self.cleaning_log.append(f"Standardized {len(numeric_cols)} numeric columns using {method}")

        return df_clean

    def calculate_data_quality_score(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate data quality metrics"""
        total_cells = len(df) * len(df.columns)

        # Completeness
        non_null_cells = total_cells - df.isnull().sum().sum()
        completeness = non_null_cells / total_cells

        # Uniqueness
        duplicate_rows = df.duplicated().sum()
        uniqueness = 1 - (duplicate_rows / len(df))

        # Validity (basic checks)
        validity_scores = []
        for col in df.select_dtypes(include=[np.number]).columns:
            # Check for negative values where they might not make sense
            if 'age' in col.lower() or 'count' in col.lower():
                valid_positive = (df[col] >= 0).sum()
                validity_scores.append(valid_positive / len(df))

        for col in df.select_dtypes(include=['object']).columns:
            # Check for empty strings
            non_empty = (df[col] != '').sum()
            validity_scores.append(non_empty / len(df))

        validity = np.mean(validity_scores) if validity_scores else 1.0

        # Consistency (data type consistency)
        consistency = 1.0  # Simplified - could check for mixed types

        return {
            "completeness": completeness,
            "uniqueness": uniqueness,
            "validity": validity,
            "consistency": consistency,
            "overall": (completeness + uniqueness + validity + consistency) / 4
        }

    def clean_dataset(self, df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Complete data cleaning pipeline"""
        self.original_shape = df.shape
        self.cleaning_log = []
        self.cleaning_applied = {
            "missing_values_handled": 0,
            "duplicates_removed": 0,
            "outliers_removed": 0,
            "data_types_converted": 0
        }

        # Default configuration
        default_config = {
            "handle_missing": True,
            "remove_duplicates": True,
            "remove_outliers": True,
            "convert_types": True,
            "standardize": False,
            "missing_strategy": "auto",
            "outlier_method": "iqr",
            "outlier_sensitivity": "medium"
        }

        if config:
            default_config.update(config)

        df_clean = df.copy()

        # Apply cleaning steps
        if default_config["convert_types"]:
            df_clean = self.convert_data_types(df_clean)

        if default_config["handle_missing"]:
            df_clean = self.handle_missing_values(df_clean, default_config["missing_strategy"])

        if default_config["remove_duplicates"]:
            df_clean = self.remove_duplicates(df_clean)

        if default_config["remove_outliers"]:
            df_clean = self.remove_outliers(
                df_clean,
                default_config["outlier_method"],
                default_config["outlier_sensitivity"]
            )

        if default_config["standardize"]:
            df_clean = self.standardize_data(df_clean)

        # Generate comprehensive report
        report = self.generate_cleaning_report(df, df_clean)

        return df_clean, report

    def generate_cleaning_report(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive cleaning report"""
        quality_scores_before = self.calculate_data_quality_score(original_df)
        quality_scores_after = self.calculate_data_quality_score(cleaned_df)

        return {
            "original_shape": self.original_shape or original_df.shape,
            "cleaned_shape": cleaned_df.shape,
            "cleaning_applied": self.cleaning_applied,
            "cleaning_log": self.cleaning_log,
            "quality_scores": {
                "before": quality_scores_before,
                "after": quality_scores_after,
                "improvement": quality_scores_after["overall"] - quality_scores_before["overall"]
            },
            "data_reduction": {
                "rows_removed": self.original_shape[0] - cleaned_df.shape[0] if self.original_shape else 0,
                "percentage_removed": ((self.original_shape[0] - cleaned_df.shape[0]) / self.original_shape[0] * 100) if self.original_shape and self.original_shape[0] > 0 else 0
            },
            "columns": {
                col: {
                    "dtype": str(cleaned_df[col].dtype),
                    "missing_before": int(original_df[col].isnull().sum()),
                    "missing_after": int(cleaned_df[col].isnull().sum()),
                    "unique_values": int(cleaned_df[col].nunique()),
                    "sample_values": cleaned_df[col].dropna().head(5).tolist(),
                    "converted": col in [log for log in self.cleaning_log if f"Converted {col}" in log]
                }
                for col in cleaned_df.columns
            },
            "numeric_summary": {},
            "correlations": [],
            "recommendations": self.generate_recommendations(cleaned_df)
        }

    def generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate cleaning and analysis recommendations"""
        recommendations = []

        # Check for remaining missing values
        if df.isnull().any().any():
            missing_cols = df.columns[df.isnull().any()].tolist()
            recommendations.append(f"Consider further handling of missing values in: {', '.join(missing_cols)}")

        # Check for low cardinality categorical variables
        cat_cols = df.select_dtypes(include=['category', 'object']).columns
        for col in cat_cols:
            if df[col].nunique() == 1:
                recommendations.append(f"Column '{col}' has only one unique value and may not be useful for analysis")
            elif df[col].nunique() == 2:
                recommendations.append(f"Column '{col}' is binary and could be encoded as 0/1 for modeling")

        # Check for highly skewed numeric variables
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].skew() > 2:
                recommendations.append(f"Column '{col}' is highly skewed (skew={df[col].skew():.2f}) - consider transformation")

        # Check for high correlations
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    if abs(corr_matrix.iloc[i, j]) > 0.9:
                        high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))

            for col1, col2, corr in high_corr_pairs:
                recommendations.append(f"High correlation detected between '{col1}' and '{col2}' ({corr:.2f}) - consider dimensionality reduction")

        return recommendations

# Legacy function for backward compatibility
def auto_clean_report(df: pd.DataFrame):
    """Legacy function - use DataCleaner class for new implementations"""
    cleaner = DataCleaner()
    _, report = cleaner.clean_dataset(df, {"handle_missing": False, "remove_duplicates": False, "remove_outliers": False})

    # Convert to old format for compatibility
    legacy_report = {
        "rows": report["original_shape"][0],
        "cols": report["original_shape"][1],
        "missing_counts": {col: info["missing_before"] for col, info in report["columns"].items()},
        "columns": {
            col: {
                "dtype": info["dtype"],
                "unique": info["unique_values"],
                "sample_values": info["sample_values"]
            }
            for col, info in report["columns"].items()
        },
        "suggested_steps": []
    }

    # Add numeric summary
    numeric_cols = df.select_dtypes(include=[np.number])
    if not numeric_cols.empty:
        legacy_report["numeric_summary"] = numeric_cols.describe().to_dict()

        # Correlation pairs
        corr = numeric_cols.corr()
        pairs = []
        for c1 in corr.columns:
            for c2 in corr.columns:
                if c1 != c2 and abs(corr.loc[c1, c2]) > 0.8:
                    pairs.append([c1, c2, corr.loc[c1, c2]])
        legacy_report["highly_correlated_pairs"] = pairs
    else:
        legacy_report["numeric_summary"] = {}
        legacy_report["highly_correlated_pairs"] = []

    if df.isnull().any().any():
        legacy_report["suggested_steps"].append("Handle missing values.")
    if any(df.duplicated()):
        legacy_report["suggested_steps"].append("Remove duplicate rows.")

    return legacy_report

if __name__ == "__main__":
    # Sample DataFrame for testing
    df = pd.DataFrame({
        "id": range(1, 11),
        "age": [25, 30, np.nan, 45, 50, 35, 60, 28, 33, 100],  # Outlier and missing
        "salary": [50000, 60000, 55000, 80000, 90000, 65000, 120000, 52000, 58000, 70000],
        "department": ["IT", "HR", "IT", "Finance", "IT", "HR", "Finance", "IT", "HR", "IT"],
        "date_joined": ["2020-01-01", "2019-05-15", "2021-03-10", "2018-11-20", "2020-07-25",
                       "2019-09-30", "2017-04-05", "2021-01-15", "2020-08-20", "2019-12-10"]
    })

    # Add some duplicates
    df = pd.concat([df, df.iloc[[0, 1]]], ignore_index=True)

    cleaner = DataCleaner()
    cleaned_df, report = cleaner.clean_dataset(df)

    print("Original Shape:", df.shape)
    print("Cleaned Shape:", cleaned_df.shape)
    print("Cleaning Log:", report["cleaning_log"])
    print("Quality Improvement:", report["quality_scores"]["improvement"])

