#!/usr/bin/env python3
"""
dvc_versioning.py - Demonstrate DVC dataset versioning workflow.

This script:
1. Creates the initial dataset (v1 — full breast cancer CSV).
2. Runs `dvc add` to track it and commits DVC metadata to Git.
3. Creates a modified dataset (v2 — adds synthetic noise rows).
4. Runs `dvc add` again and commits.
5. Creates a further dataset (v3 — drops outliers).
6. Demonstrates how to recover v1 using `git checkout` + `dvc checkout`.
7. Prints a version-comparison table.

Requirements: git and dvc must be on PATH (or in .venv/Scripts).
"""

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_CSV = REPO_ROOT / "data" / "dataset.csv"
DATA_DIR = REPO_ROOT / "data"
DVC_STORAGE = REPO_ROOT.parent / "dvc-storage"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd: list, check=True, capture=False):
    """Run a subprocess command and optionally capture output."""
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    kwargs = {"cwd": str(REPO_ROOT)}
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    result = subprocess.run(cmd, **kwargs)
    if check and result.returncode != 0:
        print(f"  [ERROR] Command failed with exit code {result.returncode}")
    if capture:
        return result.stdout.strip()
    return result


def md5_of_file(path: Path) -> str:
    hasher = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def git_commit(message: str):
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", message], check=False)


def get_dvc_md5() -> str:
    """Read md5 from data/dataset.csv.dvc."""
    dvc_file = DATASET_CSV.with_suffix(".csv.dvc")
    if not dvc_file.exists():
        return "N/A"
    import yaml
    with dvc_file.open() as f:
        meta = yaml.safe_load(f)
    try:
        return meta["outs"][0]["md5"]
    except Exception:
        return "N/A"


# ---------------------------------------------------------------------------
# Dataset creators
# ---------------------------------------------------------------------------

def make_v1():
    """Full breast cancer dataset (569 rows)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = load_breast_cancer()
    df = pd.DataFrame(data.data, columns=data.feature_names)
    df["target"] = data.target
    df.to_csv(DATASET_CSV, index=False)
    return df


def make_v2(df_v1: pd.DataFrame):
    """Add 31 synthetic rows (10% augmentation)."""
    rng = np.random.default_rng(42)
    numeric_cols = df_v1.columns[:-1]
    synthetic = pd.DataFrame(
        rng.normal(loc=df_v1[numeric_cols].mean().values,
                   scale=df_v1[numeric_cols].std().values,
                   size=(31, len(numeric_cols))),
        columns=numeric_cols,
    )
    synthetic["target"] = rng.integers(0, 2, 31)
    df_v2 = pd.concat([df_v1, synthetic], ignore_index=True)
    df_v2.to_csv(DATASET_CSV, index=False)
    return df_v2


def make_v3(df_v2: pd.DataFrame):
    """
    Drop rows where 'mean radius' is an extreme outlier (> mean + 3*std).
    Simulates a data-cleaning step.
    """
    col = "mean radius"
    mean, std = df_v2[col].mean(), df_v2[col].std()
    mask = df_v2[col] <= mean + 3 * std
    df_v3 = df_v2[mask].reset_index(drop=True)
    df_v3.to_csv(DATASET_CSV, index=False)
    return df_v3


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 65)
    print("DVC DATA VERSIONING WORKFLOW")
    print("=" * 65)

    # Check prerequisites
    for tool in ["git", "dvc"]:
        if not shutil.which(tool):
            # Try in .venv/Scripts
            venv_tool = REPO_ROOT / ".venv" / "Scripts" / f"{tool}.exe"
            if venv_tool.exists():
                print(f"  {tool} found in .venv: {venv_tool}")
            else:
                print(f"  WARNING: '{tool}' not found on PATH. Some steps may fail.")

    # -----------------------------------------------------------------------
    # Step 1: DVC remote setup
    # -----------------------------------------------------------------------
    print("\n[B4] Configuring DVC local remote storage ...")
    DVC_STORAGE.mkdir(parents=True, exist_ok=True)

    dvc_config = REPO_ROOT / ".dvc" / "config"
    if dvc_config.exists():
        content = dvc_config.read_text()
        if "localremote" not in content:
            run(["dvc", "remote", "add", "-d", "localremote", str(DVC_STORAGE)], check=False)
            run(["git", "add", ".dvc/config"], check=False)
            run(["git", "commit", "-m", "Configure DVC local remote"], check=False)
    else:
        run(["dvc", "remote", "add", "-d", "localremote", str(DVC_STORAGE)], check=False)
        run(["git", "add", ".dvc/config"], check=False)
        run(["git", "commit", "-m", "Configure DVC local remote"], check=False)

    versions = []

    # -----------------------------------------------------------------------
    # Step 2: Dataset v1 — baseline
    # -----------------------------------------------------------------------
    print("\n[B5-v1] Creating baseline dataset (full breast cancer CSV) ...")
    df_v1 = make_v1()
    rows_v1 = len(df_v1)
    cols_v1 = len(df_v1.columns)
    size_v1 = DATASET_CSV.stat().st_size

    run(["dvc", "add", "data/dataset.csv"], check=False)
    git_commit("Track dataset v1 with DVC — 569 rows (full breast cancer)")
    run(["dvc", "push"], check=False)

    commit_v1 = run(
        ["git", "rev-parse", "--short", "HEAD"], capture=True
    )
    md5_v1 = get_dvc_md5()
    versions.append({"version": "v1 (baseline)", "commit": commit_v1,
                     "rows": rows_v1, "cols": cols_v1,
                     "description": "Full sklearn breast_cancer (569 rows)",
                     "md5": md5_v1, "size_bytes": size_v1})

    # -----------------------------------------------------------------------
    # Step 3: Dataset v2 — augmented
    # -----------------------------------------------------------------------
    print("\n[B5-v2] Augmenting dataset (adding 31 synthetic rows) ...")
    df_v2 = make_v2(df_v1)
    rows_v2 = len(df_v2)
    size_v2 = DATASET_CSV.stat().st_size

    run(["dvc", "add", "data/dataset.csv"], check=False)
    git_commit("Update dataset v2 — add 31 synthetic rows (augmentation)")
    run(["dvc", "push"], check=False)

    commit_v2 = run(
        ["git", "rev-parse", "--short", "HEAD"], capture=True
    )
    md5_v2 = get_dvc_md5()
    versions.append({"version": "v2 (augmented)", "commit": commit_v2,
                     "rows": rows_v2, "cols": cols_v1,
                     "description": "v1 + 31 synthetic rows",
                     "md5": md5_v2, "size_bytes": size_v2})

    # -----------------------------------------------------------------------
    # Step 4: Dataset v3 — cleaned
    # -----------------------------------------------------------------------
    print("\n[B5-v3] Cleaning dataset (dropping extreme outliers in mean radius) ...")
    df_v3 = make_v3(df_v2)
    rows_v3 = len(df_v3)
    size_v3 = DATASET_CSV.stat().st_size

    run(["dvc", "add", "data/dataset.csv"], check=False)
    git_commit("Update dataset v3 — drop outliers (mean radius > mean+3*std)")
    run(["dvc", "push"], check=False)

    commit_v3 = run(
        ["git", "rev-parse", "--short", "HEAD"], capture=True
    )
    md5_v3 = get_dvc_md5()
    versions.append({"version": "v3 (cleaned)", "commit": commit_v3,
                     "rows": rows_v3, "cols": cols_v1,
                     "description": "v2 minus mean-radius outliers",
                     "md5": md5_v3, "size_bytes": size_v3})

    # -----------------------------------------------------------------------
    # Step 5: Demonstrate recovery of v1
    # -----------------------------------------------------------------------
    print("\n[B5-recovery] Restoring dataset v1 ...")
    print(f"  Current rows: {rows_v3} (v3)")
    print(f"  Git checkout commit {commit_v1} for data/dataset.csv.dvc ...")
    run(["git", "checkout", commit_v1, "--", "data/dataset.csv.dvc"], check=False)
    run(["dvc", "checkout", "data/dataset.csv.dvc"], check=False)

    if DATASET_CSV.exists():
        df_restored = pd.read_csv(DATASET_CSV)
        restored_rows = len(df_restored)
        restored_md5  = md5_of_file(DATASET_CSV)
        match = (restored_rows == rows_v1) and (restored_md5 == md5_v1)
        print(f"\n  Restored rows : {restored_rows}  (expected {rows_v1})")
        print(f"  Restored MD5  : {restored_md5}")
        print(f"  Original MD5  : {md5_v1}")
        print(f"  Verification  : {'PASS ✓' if match else 'FAIL ✗'}")
    else:
        print("  WARNING: dataset.csv not found after checkout.")

    # Return to latest version (v3)
    print("\n  Restoring latest version (v3) ...")
    run(["git", "checkout", "HEAD", "--", "data/dataset.csv.dvc"], check=False)
    run(["dvc", "checkout", "data/dataset.csv.dvc"], check=False)
    latest_rows = len(pd.read_csv(DATASET_CSV))
    print(f"  Current rows after restore: {latest_rows} (expected {rows_v3})")

    # -----------------------------------------------------------------------
    # Summary table
    # -----------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("DATASET VERSION COMPARISON TABLE")
    print("=" * 65)
    print(f"{'Version':<20} {'Commit':>8} {'Rows':>6} {'Cols':>5}  Description")
    print("-" * 80)
    for v in versions:
        print(f"{v['version']:<20} {v['commit']:>8} {v['rows']:>6} {v['cols']:>5}  {v['description']}")

    print("\nMD5 Hashes:")
    for v in versions:
        print(f"  {v['version']:<20}  {v['md5']}")

    print("\nVerification method: row count + MD5 hash comparison")
    print("A filename alone is insufficient — the same filename can contain")
    print("different data across commits. The DVC .dvc file's md5 hash is the")
    print("authoritative identifier for a specific data version.\n")


if __name__ == "__main__":
    main()
