#!/usr/bin/env python3
"""
train.py - Advanced MLflow training script for Breast Cancer Classification.

Covers:
- Autologging (mlflow.sklearn.autolog)
- Model signatures and input examples
- Artifact logging (confusion matrix, classification report, feature importance)
- Multiple hyperparameter variants for experiment comparison
- Git commit and DVC dataset hash tagging in MLflow runs
"""

import argparse
import hashlib
import os
import subprocess
from datetime import datetime
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import yaml
from mlflow.models.signature import ModelSignature, infer_signature
from mlflow.types.schema import ColSpec, Schema
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config(path=None):
    """Load YAML configuration file."""
    if path is None:
        path = Path(__file__).resolve().parents[1] / "configs" / "config.yaml"
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def configure_mlflow(config):
    """Set MLflow tracking URI and experiment name from config."""
    repo_root = Path(__file__).resolve().parents[1]
    mlflow_cfg = config.get("mlflow", {})
    tracking_uri = mlflow_cfg.get("tracking_uri", "sqlite:///mlflow.db")

    if tracking_uri.startswith("sqlite:///"):
        db_path = tracking_uri.replace("sqlite:///", "", 1)
        if not db_path.startswith(("/", "\\")):
            db_path = str(repo_root / db_path)
        tracking_uri = f"sqlite:///{db_path}"
    else:
        tracking_uri = str((repo_root / tracking_uri).resolve())

    mlflow.set_tracking_uri(tracking_uri)
    experiment_name = mlflow_cfg.get("experiment_name", "breast_cancer_random_forest")
    mlflow.set_experiment(experiment_name)
    return repo_root


def get_git_commit():
    """Return the current Git commit SHA, or 'unknown' if not in a Git repo."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
        return commit
    except Exception:
        return "unknown"


def get_dvc_dataset_hash(dataset_path: Path) -> str:
    """
    Return the DVC md5 hash recorded in the .dvc metadata file, or compute
    a raw MD5 hash of the file if no .dvc file exists.
    """
    dvc_file = Path(str(dataset_path) + ".dvc")
    if dvc_file.exists():
        with dvc_file.open("r") as f:
            content = yaml.safe_load(f)
        try:
            return content["outs"][0]["md5"]
        except (KeyError, IndexError, TypeError):
            pass

    # Fallback: compute md5 of the actual file
    if dataset_path.exists():
        hasher = hashlib.md5()
        with dataset_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    return "unknown"


def load_or_create_dataset(config, repo_root: Path):
    """
    Load the Breast Cancer dataset. Save it as CSV for DVC tracking if not
    already present, then return X, y, and the DataFrame.
    """
    dataset_csv = repo_root / config["data"].get("dataset_csv", "data/dataset.csv")
    dataset_csv.parent.mkdir(parents=True, exist_ok=True)

    data = load_breast_cancer()
    df = pd.DataFrame(data.data, columns=data.feature_names)
    df["target"] = data.target

    if not dataset_csv.exists():
        df.to_csv(dataset_csv, index=False)
        print(f"  Dataset saved to: {dataset_csv}")
    else:
        # Load from CSV to ensure DVC-tracked version is used
        df = pd.read_csv(dataset_csv)
        print(f"  Dataset loaded from: {dataset_csv}  ({len(df)} rows)")

    target_col = config["data"].get("target_column", "target")
    X = df.drop(columns=[target_col]).values
    y = df[target_col].values
    return X, y, df, dataset_csv


def save_confusion_matrix(y_test, y_pred, report_dir: Path, variant_name: str) -> Path:
    """Save a confusion matrix plot and return its path."""
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Malignant", "Benign"])
    disp.plot(ax=ax, colorbar=True, cmap="Blues")
    ax.set_title(f"Confusion Matrix — {variant_name}")
    cm_path = report_dir / f"confusion_matrix_{variant_name}.png"
    plt.tight_layout()
    plt.savefig(cm_path, dpi=100)
    plt.close()
    return cm_path


def save_feature_importance(model, feature_names, report_dir: Path, variant_name: str) -> Path:
    """Save a feature-importance bar chart and return its path."""
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:15]  # top 15 features

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(len(indices)), importances[indices])
    ax.set_xticks(range(len(indices)))
    ax.set_xticklabels([feature_names[i] for i in indices], rotation=45, ha="right")
    ax.set_title(f"Feature Importance — {variant_name}")
    ax.set_ylabel("Importance")
    plt.tight_layout()
    fi_path = report_dir / f"feature_importance_{variant_name}.png"
    plt.savefig(fi_path, dpi=100)
    plt.close()
    return fi_path


def build_model_signature(X_train, y_pred, feature_names):
    """
    Build an MLflow ModelSignature from actual data.

    The signature describes:
    - inputs : 30 numeric columns (one per breast-cancer feature)
    - outputs: a single integer column (class label 0 or 1)

    Using infer_signature is the recommended approach as it derives the schema
    directly from real numpy arrays, avoiding manual type mapping.
    """
    # Create a small Pandas DataFrame with proper column names for clarity
    input_example = pd.DataFrame(X_train[:5], columns=feature_names)
    signature = infer_signature(input_example, y_pred[:5])
    return signature, input_example


# ---------------------------------------------------------------------------
# Training routine
# ---------------------------------------------------------------------------

def train_variant(variant: dict, config: dict, repo_root: Path,
                   X_train, X_test, y_train, y_test,
                   feature_names, git_commit: str, dvc_hash: str):
    """
    Train one RandomForestClassifier variant, log everything to MLflow,
    and return the run_id + metrics.
    """
    model_dir = repo_root / "models"
    report_dir = repo_root / "reports"
    model_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)

    variant_name = variant["name"]
    run_name = f"rf_{variant_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Enable autologging — captures params, metrics, and the model automatically
    # for scikit-learn (parameters, feature names, cross-val scores if applicable)
    mlflow.sklearn.autolog(
        log_input_examples=True,
        log_model_signatures=True,
        log_models=False,   # We log manually to include signature + example
        silent=True,
    )

    with mlflow.start_run(run_name=run_name) as run:
        run_id = run.info.run_id
        print(f"\n  MLflow run started: {run_id}")

        # --- Tags: link this run to code and data versions ---
        mlflow.set_tags({
            "git_commit": git_commit,
            "dvc_dataset_hash": dvc_hash,
            "variant": variant_name,
            "dataset": config["data"]["dataset"],
            "framework": "scikit-learn",
        })

        # --- Model ---
        model = RandomForestClassifier(
            n_estimators=variant["n_estimators"],
            max_depth=variant["max_depth"],
            min_samples_split=variant["min_samples_split"],
            random_state=config["model"]["random_state"],
        )
        model.fit(X_train, y_train)

        # --- Metrics ---
        y_pred = model.predict(X_test)
        metrics = {
            "accuracy":  accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall":    recall_score(y_test, y_pred, zero_division=0),
            "f1_score":  f1_score(y_test, y_pred, zero_division=0),
        }
        mlflow.log_metrics(metrics)

        # Autolog also logs params; supplement with ours explicitly
        mlflow.log_params({
            "n_estimators":    variant["n_estimators"],
            "max_depth":       variant["max_depth"],
            "min_samples_split": variant["min_samples_split"],
            "test_size":       config["training"]["test_size"],
            "random_state":    config["model"]["random_state"],
        })

        # --- Artifacts ---
        # 1. Classification report (text)
        report_txt = classification_report(y_test, y_pred, target_names=["Malignant", "Benign"])
        report_path = report_dir / f"classification_report_{variant_name}.txt"
        report_path.write_text(report_txt, encoding="utf-8")
        mlflow.log_artifact(str(report_path))

        # 2. Confusion matrix (image)
        cm_path = save_confusion_matrix(y_test, y_pred, report_dir, variant_name)
        mlflow.log_artifact(str(cm_path))

        # 3. Feature importance plot (image)
        fi_path = save_feature_importance(model, list(feature_names), report_dir, variant_name)
        mlflow.log_artifact(str(fi_path))

        # 4. Config file
        mlflow.log_artifact(str(repo_root / "configs" / "config.yaml"))

        # --- Model with Signature and Input Example ---
        signature, input_example = build_model_signature(X_train, y_pred, feature_names)
        mlflow.sklearn.log_model(
            model,
            name="model",
            signature=signature,
            input_example=input_example,
            registered_model_name=None,  # Register separately in register_models.py
        )

        # --- Save locally as well ---
        local_model_path = model_dir / f"random_forest_{variant_name}.pkl"
        joblib.dump(model, local_model_path)

        print(f"  Variant: {variant_name}")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1-Score:  {metrics['f1_score']:.4f}")

    return run_id, metrics


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

VARIANTS = [
    # Variant 1 — baseline (matches original config)
    {"name": "v1_baseline",    "n_estimators": 100, "max_depth": 5,    "min_samples_split": 2},
    # Variant 2 — deeper trees, more estimators
    {"name": "v2_deep",        "n_estimators": 200, "max_depth": 10,   "min_samples_split": 2},
    # Variant 3 — shallow trees, larger min_samples_split (regularised)
    {"name": "v3_regularised", "n_estimators": 150, "max_depth": 3,    "min_samples_split": 5},
]


def main():
    parser = argparse.ArgumentParser(description="Train Random Forest variants on Breast Cancer data.")
    parser.add_argument("--config", type=str, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print(f"TRAINING STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    config = load_config(args.config)
    repo_root = configure_mlflow(config)

    git_commit = get_git_commit()
    print(f"\nGit commit : {git_commit}")

    print("\nLoading dataset ...")
    X, y, df, dataset_csv = load_or_create_dataset(config, repo_root)

    dvc_hash = get_dvc_dataset_hash(dataset_csv)
    print(f"DVC/MD5 hash : {dvc_hash}")
    print(f"Dataset shape: {X.shape}")

    data = load_breast_cancer()
    feature_names = data.feature_names

    print("\nSplitting dataset ...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=config["training"]["test_size"],
        random_state=config["training"]["random_state"],
        stratify=y if config["training"].get("stratify", True) else None,
    )
    print(f"Train: {len(X_train)}  |  Test: {len(X_test)}")

    results = []
    for variant in VARIANTS:
        print(f"\n--- Training variant: {variant['name']} ---")
        run_id, metrics = train_variant(
            variant, config, repo_root,
            X_train, X_test, y_train, y_test,
            feature_names, git_commit, dvc_hash,
        )
        results.append({"variant": variant["name"], "run_id": run_id, **metrics})

    # Summary table
    print("\n" + "=" * 65)
    print("EXPERIMENT SUMMARY")
    print("=" * 65)
    print(f"{'Variant':<20} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>8}")
    print("-" * 65)
    for r in results:
        print(f"{r['variant']:<20} {r['accuracy']:>9.4f} {r['precision']:>10.4f} "
              f"{r['recall']:>8.4f} {r['f1_score']:>8.4f}")

    # Persist run IDs so register_models.py can consume them
    run_ids_path = repo_root / "models" / "run_ids.txt"
    with run_ids_path.open("w") as f:
        for r in results:
            f.write(f"{r['variant']}\t{r['run_id']}\t{r['f1_score']:.6f}\n")
    print(f"\nRun IDs saved to: {run_ids_path}")
    print(f"MLflow tracking URI: {mlflow.get_tracking_uri()}")
    print("\nDone. Launch 'mlflow ui --backend-store-uri sqlite:///mlflow.db' to explore runs.")


if __name__ == "__main__":
    main()