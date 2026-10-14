#!/usr/bin/env python3
"""
evaluate.py - Standalone evaluation script.

Loads a saved model, runs predictions on the test set, and prints a full
evaluation report. Can also be called with a specific model path.
"""

import argparse
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import yaml
from sklearn.datasets import load_breast_cancer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split


def load_config(path=None):
    if path is None:
        path = Path(__file__).resolve().parents[1] / "configs" / "config.yaml"
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def evaluate_model(model_path: Path, config: dict, repo_root: Path):
    """Load model, evaluate, and print report."""
    print(f"\nEvaluating: {model_path}")

    model = joblib.load(model_path)

    # Load data
    dataset_csv = repo_root / config["data"].get("dataset_csv", "data/dataset.csv")
    if dataset_csv.exists():
        df = pd.read_csv(dataset_csv)
    else:
        data = load_breast_cancer()
        df = pd.DataFrame(data.data, columns=data.feature_names)
        df["target"] = data.target

    target_col = config["data"].get("target_column", "target")
    X = df.drop(columns=[target_col]).values
    y = df[target_col].values

    _, X_test, _, y_test = train_test_split(
        X, y,
        test_size=config["training"]["test_size"],
        random_state=config["training"]["random_state"],
        stratify=y,
    )

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy":  accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall":    recall_score(y_test, y_pred, zero_division=0),
        "f1_score":  f1_score(y_test, y_pred, zero_division=0),
        "roc_auc":   roc_auc_score(y_test, y_prob),
    }

    print("\n===== EVALUATION METRICS =====")
    for k, v in metrics.items():
        print(f"  {k:<12}: {v:.4f}")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Malignant", "Benign"]))

    # Save ROC curve
    report_dir = repo_root / "reports"
    report_dir.mkdir(exist_ok=True)
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    plt.figure()
    plt.plot(fpr, tpr, label=f"AUC = {metrics['roc_auc']:.3f}")
    plt.plot([0, 1], [0, 1], "k--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"ROC Curve — {model_path.stem}")
    plt.legend()
    roc_path = report_dir / f"roc_curve_{model_path.stem}.png"
    plt.savefig(roc_path, dpi=100)
    plt.close()
    print(f"ROC curve saved: {roc_path}")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate a saved Random Forest model.")
    parser.add_argument(
        "--model", type=str, default=None,
        help="Path to .pkl model file. If omitted, evaluates all models in models/."
    )
    parser.add_argument("--config", type=str, default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    repo_root = Path(__file__).resolve().parents[1]

    if args.model:
        paths = [Path(args.model)]
    else:
        paths = sorted((repo_root / "models").glob("*.pkl"))

    if not paths:
        print("No model files found. Run train.py first.")
        return

    for p in paths:
        evaluate_model(p, config, repo_root)


if __name__ == "__main__":
    main()
