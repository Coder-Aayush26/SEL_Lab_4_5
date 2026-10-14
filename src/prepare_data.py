#!/usr/bin/env python3
"""
prepare_data.py - Load breast cancer data from CSV and split into train/test sets.

This is the first stage of the DVC pipeline. It reads the DVC-tracked
data/dataset.csv and produces deterministic train/test CSV splits.
"""

from pathlib import Path

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split


def load_config(path=None):
    if path is None:
        path = Path(__file__).resolve().parents[1] / "configs" / "config.yaml"
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    repo_root = Path(__file__).resolve().parents[1]

    dataset_csv = repo_root / config["data"].get("dataset_csv", "data/dataset.csv")
    processed_dir = repo_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    if not dataset_csv.exists():
        # Fallback: create from sklearn
        from sklearn.datasets import load_breast_cancer
        data = load_breast_cancer()
        df = pd.DataFrame(data.data, columns=data.feature_names)
        df["target"] = data.target
        dataset_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(dataset_csv, index=False)
        print(f"Created dataset at {dataset_csv}")
    else:
        df = pd.read_csv(dataset_csv)
        print(f"Loaded dataset: {dataset_csv} ({len(df)} rows)")

    target_col = config["data"].get("target_column", "target")
    X = df.drop(columns=[target_col])
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=config["training"]["test_size"],
        random_state=config["training"]["random_state"],
        stratify=y if config["training"].get("stratify", True) else None,
    )

    train_df = X_train.copy()
    train_df[target_col] = y_train.values
    test_df = X_test.copy()
    test_df[target_col] = y_test.values

    train_df.to_csv(processed_dir / "train.csv", index=False)
    test_df.to_csv(processed_dir / "test.csv", index=False)

    print(f"Train split: {len(train_df)} rows -> data/processed/train.csv")
    print(f"Test split : {len(test_df)} rows -> data/processed/test.csv")


if __name__ == "__main__":
    main()
