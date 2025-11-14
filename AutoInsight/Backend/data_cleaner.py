import pandas as pd
import numpy as np

def auto_clean_report(df: pd.DataFrame):
    report = {}
    report["rows"], report["cols"] = df.shape
    report["missing_counts"] = df.isnull().sum().to_dict()

    # Column summary
    report["columns"] = {}
    for col in df.columns:
        report["columns"][col] = {
            "dtype": str(df[col].dtype),
            "unique": df[col].nunique(),
            "sample_values": df[col].dropna().unique()[:5].tolist()
        }

    # Numeric summary
    numeric_cols = df.select_dtypes(include=[np.number])
    if not numeric_cols.empty:
        report["numeric_summary"] = numeric_cols.describe().to_dict()

        # Correlation pairs
        corr = numeric_cols.corr()
        pairs = []
        for c1 in corr.columns:
            for c2 in corr.columns:
                if c1 != c2 and abs(corr.loc[c1, c2]) > 0.8:
                    pairs.append([c1, c2, corr.loc[c1, c2]])
        report["highly_correlated_pairs"] = pairs
    else:
        report["numeric_summary"] = {}
        report["highly_correlated_pairs"] = []

    report["suggested_steps"] = []
    if df.isnull().any().any():
        report["suggested_steps"].append("Handle missing values.")
    if any(df.duplicated()):
        report["suggested_steps"].append("Remove duplicate rows.")
    return report

if __name__ == "__main__":
    import json
    # sample DataFrame for quick run
    df = pd.DataFrame({
        "id": range(1, 6),
        "value": [1, 2, np.nan, 4, 5],
        "cat": ["a", "b", "a", "b", "a"]
    })
    report = auto_clean_report(df)
    print(json.dumps(report, default=str, indent=2))

