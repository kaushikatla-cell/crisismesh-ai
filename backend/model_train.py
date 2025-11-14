"""
Train a RandomForest model to predict link failures using logged metrics.

Usage:
  1. Run mesh_monitor.py for a while to collect logs/metrics_*.csv.
  2. Manually label some rows in those CSVs with will_fail = 0/1.
  3. Run: python3 model_train.py
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from config import LOG_DIR, MODEL_PATH


def load_dataset() -> tuple[np.ndarray, np.ndarray]:
    files = list(LOG_DIR.glob("metrics_*.csv"))
    if not files:
        raise FileNotFoundError(f"No metrics_*.csv files found in {LOG_DIR}")

    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)

    # Expected columns
    feature_cols = ["signal_strength", "packet_loss", "hop_count", "battery_pct"]
    for col in feature_cols + ["will_fail"]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' missing from logs. Found: {df.columns}")

    X = df[feature_cols].values
    y = df["will_fail"].values  # 0 or 1
    return X, y


def train_model():
    X, y = load_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print("=== Classification Report ===")
    print(classification_report(y_test, y_pred))

    MODEL_PATH.parent.mkdir(exist_ok=True, parents=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)
    print(f"[OK] Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
