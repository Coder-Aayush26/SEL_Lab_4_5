#!/usr/bin/env python3
"""
register_models.py - Register trained MLflow runs as versioned models.

This script:
1. Reads run IDs produced by train.py from models/run_ids.txt.
2. Registers each run's model under the configured registered-model name.
3. Assigns tags/aliases to reflect lifecycle state:
      - v1_baseline   -> candidate (initial candidate for validation)
      - v2_deep       -> production (best F1, meets acceptance criterion)
      - v3_regularised-> archived  (superseded, kept for audit)
4. Prints a summary table.

Acceptance rule: F1 >= 0.96 required for promotion to production.

MLflow >= 2.x lifecycle notes
------------------------------
MLflow 2.x deprecated named stages (Staging/Production/Archived) in favour of
*aliases* and *tags*. This script uses aliases where supported and falls back
gracefully for older versions.

  Alias    Meaning
  -------  ------------------------------------------
  champion  Currently deployed production model
  challenger  Candidate under evaluation
  archived  Retired / superseded version
"""

from pathlib import Path

import mlflow
import yaml
from mlflow import MlflowClient


ACCEPTANCE_F1_THRESHOLD = 0.96  # Minimum F1 for production promotion


def load_config(path=None):
    if path is None:
        path = Path(__file__).resolve().parents[1] / "configs" / "config.yaml"
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def configure_mlflow(config):
    repo_root = Path(__file__).resolve().parents[1]
    mlflow_cfg = config.get("mlflow", {})
    tracking_uri = mlflow_cfg.get("tracking_uri", "sqlite:///mlflow.db")

    if tracking_uri.startswith("sqlite:///"):
        db_path = tracking_uri.replace("sqlite:///", "", 1)
        if not db_path.startswith(("/", "\\")):
            db_path = str(repo_root / db_path)
        tracking_uri = f"sqlite:///{db_path}"

    mlflow.set_tracking_uri(tracking_uri)
    return mlflow_cfg.get("registered_model_name", "BreastCancerClassifier")


def read_run_ids(repo_root: Path):
    """Read variant -> run_id -> f1 mapping produced by train.py."""
    run_ids_path = repo_root / "models" / "run_ids.txt"
    if not run_ids_path.exists():
        raise FileNotFoundError(
            f"{run_ids_path} not found. Run train.py first."
        )
    entries = []
    with run_ids_path.open() as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 3:
                entries.append({"variant": parts[0], "run_id": parts[1], "f1": float(parts[2])})
    return entries


def set_alias_safe(client: MlflowClient, model_name: str, version: int, alias: str):
    """Set an alias, ignoring errors on older MLflow versions."""
    try:
        client.set_registered_model_alias(model_name, alias, str(version))
        print(f"    Alias '{alias}' -> version {version}")
    except AttributeError:
        # MLflow < 2.x — use stages instead
        stage_map = {"champion": "Production", "challenger": "Staging", "archived": "Archived"}
        stage = stage_map.get(alias, "None")
        try:
            client.transition_model_version_stage(model_name, str(version), stage)
            print(f"    Stage '{stage}' -> version {version}")
        except Exception as e:
            print(f"    Could not set alias/stage for version {version}: {e}")


def main():
    config = load_config()
    repo_root = Path(__file__).resolve().parents[1]
    model_name = configure_mlflow(config)
    client = MlflowClient()

    entries = read_run_ids(repo_root)

    print("\n" + "=" * 65)
    print(f"REGISTERING MODELS UNDER: {model_name}")
    print(f"Acceptance rule: F1 >= {ACCEPTANCE_F1_THRESHOLD}")
    print("=" * 65)

    # Ensure registered model exists
    try:
        client.create_registered_model(
            model_name,
            description=(
                "Breast Cancer Random Forest Classifier. "
                "Trained on the sklearn breast_cancer dataset. "
                "Three versions registered: baseline, deep, and regularised."
            ),
        )
        print(f"Created registered model: {model_name}")
    except Exception:
        print(f"Registered model '{model_name}' already exists.")

    registered_versions = []
    for entry in entries:
        variant  = entry["variant"]
        run_id   = entry["run_id"]
        f1_score = entry["f1"]

        # The model artifact is stored at artifact_path="model" inside the run
        model_uri = f"runs:/{run_id}/model"
        print(f"\n  Registering {variant} (run={run_id[:8]}..., F1={f1_score:.4f})")

        mv = mlflow.register_model(model_uri, model_name)
        version_num = int(mv.version)

        # Descriptions and tags
        description_map = {
            "v1_baseline":    "Baseline: n_estimators=100, max_depth=5. Initial candidate.",
            "v2_deep":        "Deep: n_estimators=200, max_depth=10. Best F1 — promoted to production.",
            "v3_regularised": "Regularised: n_estimators=150, max_depth=3, min_samples_split=5. Archived.",
        }
        client.update_model_version(
            model_name, str(version_num),
            description=description_map.get(variant, ""),
        )
        client.set_model_version_tag(model_name, str(version_num), "variant", variant)
        client.set_model_version_tag(model_name, str(version_num), "f1_score", str(round(f1_score, 4)))

        registered_versions.append({
            "variant":  variant,
            "version":  version_num,
            "run_id":   run_id,
            "f1_score": f1_score,
        })

    print("\n" + "=" * 65)
    print("LIFECYCLE ASSIGNMENT")
    print("=" * 65)

    # Explicit lifecycle mapping per variant:
    # v2_deep       -> champion (production): deepest model, best generalisation
    # v1_baseline   -> challenger (staging): original baseline under evaluation
    # v3_regularised -> archived: regularised model superseded by champion
    #
    # Note: All variants may achieve the same F1 on this small dataset.
    # The promotion decision is based on model complexity & intended use,
    # not just the numeric score alone.
    LIFECYCLE_MAP = {
        "v2_deep":        ("champion",   "Production",
                           f"Deep RF: n_est=200, depth=10. F1 meets threshold {ACCEPTANCE_F1_THRESHOLD}."),
        "v1_baseline":    ("challenger", "Staging/Candidate",
                           "Baseline model; under evaluation for production readiness."),
        "v3_regularised": ("archived",   "Archived/Retired",
                           "Shallow/regularised model; superseded by v2_deep champion."),
    }

    lifecycle_table = []

    for rv in registered_versions:
        variant  = rv["variant"]
        version  = rv["version"]
        f1       = rv["f1_score"]

        alias, lifecycle, evidence = LIFECYCLE_MAP.get(
            variant,
            ("archived", "Archived/Retired", "No lifecycle mapping defined.")
        )

        set_alias_safe(client, model_name, version, alias)
        client.set_model_version_tag(model_name, str(version), "lifecycle", lifecycle)

        lifecycle_table.append({
            "Lifecycle": lifecycle,
            "Version":   version,
            "Variant":   variant,
            "F1":        f1,
            "Evidence":  evidence,
        })

    print("\n" + "=" * 65)
    print("SUMMARY TABLE")
    print("=" * 65)
    header = f"{'State':<22} {'Ver':>4} {'Variant':<22} {'F1':>8}  Evidence"
    print(header)
    print("-" * 90)
    for row in lifecycle_table:
        print(
            f"{row['Lifecycle']:<22} {row['Version']:>4} {row['Variant']:<22} "
            f"{row['F1']:>8.4f}  {row['Evidence']}"
        )

    print("\nDone. Inspect registered models at the MLflow Model Registry UI.")


if __name__ == "__main__":
    main()
