# MLOps Lab Assignment 4 & 5
## Advanced MLflow and Data Versioning with DVC

> **Breast Cancer Classification — Random Forest**
> Using scikit-learn, MLflow 3.x, DVC, and Git for a fully reproducible ML project.

---

## Table of Contents
1. [Learning Outcomes](#learning-outcomes)
2. [Project Structure](#project-structure)
3. [Quick Start](#quick-start)
4. [Part A — Advanced MLflow](#part-a--advanced-mlflow)
   - [A1 Self-Learning Research](#a1-self-learning-research)
   - [A2 Environment Setup](#a2-environment-setup)
   - [A3 Experiment Tracking](#a3-experiment-tracking)
   - [A4 Model Signature](#a4-model-signature)
   - [A5 Model Registry — Versions](#a5-model-registry--versions)
   - [A6 Lifecycle Management](#a6-lifecycle-management)
5. [Part B — Data Versioning with DVC](#part-b--data-versioning-with-dvc)
   - [B1 Self-Learning Research](#b1-self-learning-research)
   - [B2 DVC Initialization](#b2-dvc-initialization)
   - [B3 Track a Dataset](#b3-track-a-dataset)
   - [B4 Configure DVC Remote](#b4-configure-dvc-remote)
   - [B5 Create and Recover Dataset Versions](#b5-create-and-recover-dataset-versions)
   - [B6 Dataset Version Comparison](#b6-dataset-version-comparison)
   - [B7 DVC Pipelines](#b7-dvc-pipelines)
6. [Part C — Git + DVC + MLflow Integration](#part-c--git--dvc--mlflow-integration)
7. [Challenges and Lessons Learned](#challenges-and-lessons-learned)
8. [References](#references)

---

## Learning Outcomes

- Explain model signatures, artifacts, autologging, and the MLflow Model Registry.
- Log and compare runs; register at least three model versions.
- Document a promotion workflow: candidate → production → archived.
- Use DVC to track dataset versions while Git tracks DVC metadata.
- Configure a DVC remote and push/pull data.
- Restore an earlier dataset version and verify the result.
- Explain how Git, MLflow, and DVC complement each other.

---

## Project Structure

```
SEL_Lab_4_5/
├── .dvc/                    # DVC internal config (version-controlled)
│   └── config               # DVC remote configuration
├── data/
│   ├── dataset.csv          # DVC-tracked (excluded from Git by .gitignore)
│   ├── dataset.csv.dvc      # DVC metadata file (Git-tracked)
│   ├── raw/
│   └── processed/
│       ├── train.csv
│       └── test.csv
├── src/
│   ├── train.py             # Multi-variant training with autologging + signatures
│   ├── evaluate.py          # Standalone evaluation + ROC curves
│   ├── register_models.py   # MLflow Model Registry + lifecycle aliases
│   ├── prepare_data.py      # DVC pipeline stage 1: data splitting
│   └── dvc_versioning.py    # DVC versioning demonstration script
├── models/
│   ├── random_forest_v1_baseline.pkl
│   ├── random_forest_v2_deep.pkl
│   ├── random_forest_v3_regularised.pkl
│   └── run_ids.txt          # Maps variant name → MLflow run_id
├── reports/
│   ├── confusion_matrix_*.png
│   ├── feature_importance_*.png
│   ├── classification_report_*.txt
│   └── roc_curve_*.png
├── configs/
│   └── config.yaml          # Single source of truth for hyperparameters
├── mlflow.db                # SQLite MLflow tracking backend
├── dvc.yaml                 # DVC pipeline definition
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Quick Start

```bash
# 1. Activate the virtual environment
.venv\Scripts\activate        # Windows PowerShell
source .venv/bin/activate     # Linux/macOS

# 2. Train 3 model variants (logs to MLflow automatically)
python src/train.py

# 3. Register models and assign lifecycle aliases
python src/register_models.py

# 4. Evaluate all models
python src/evaluate.py

# 5. Launch MLflow UI
mlflow ui --backend-store-uri sqlite:///mlflow.db

# 6. Initialize DVC and create versioned datasets
dvc init
python src/dvc_versioning.py

# 7. Run the full DVC pipeline
dvc repro

# 8. View DVC pipeline DAG
dvc dag
```

---

## Part A — Advanced MLflow

### A1 Self-Learning Research

#### Model Signature
A **Model Signature** describes the expected input and output schema of a model — column names, data types, and optionally tensor shapes. It is stored in the MLmodel artifact file and can be inspected via the MLflow UI or SDK.

**Purpose:** When a signature is attached, MLflow can validate prediction requests before they reach the model, catching errors like wrong column counts, type mismatches, or missing features early. It does **not** guarantee semantic correctness (e.g., a correctly typed but logically wrong input will pass).

**Example:**
```python
from mlflow.models.signature import infer_signature
signature = infer_signature(X_train_df, model.predict(X_test_df))
mlflow.sklearn.log_model(model, "model", signature=signature)
```

The resulting signature entry in `MLmodel`:
```yaml
signature:
  inputs: '[{"name": "mean radius", "type": "double"}, ...]'
  outputs: '[{"type": "long"}]'
```

**Discussion:** If a future API sends 3 columns when the model expects 30, or sends strings where floats are expected, the signature check raises a `MlflowException` before the model's `predict()` is called. This prevents misleading or incorrect predictions from being returned silently.

#### Artifacts
**Artifacts** are any files associated with an MLflow run — plots, reports, config files, serialised models, and more. They are stored in the artifact store (a local directory or cloud bucket) and linked to the run by `mlflow.log_artifact()` or `mlflow.log_artifacts()`.

**Example:**
```python
mlflow.log_artifact("reports/confusion_matrix.png")
mlflow.log_artifact("configs/config.yaml")
```

In this project we log: confusion matrix PNG, feature importance PNG, classification report TXT, and config YAML.

#### Autologging
`mlflow.sklearn.autolog()` automatically captures:
- **Parameters:** `n_estimators`, `max_depth`, `min_samples_split`, `random_state`, etc.
- **Metrics:** Training accuracy (from `.score()`), cross-validation scores (if used)
- **Model:** Serialised model artifact with signature and input example
- **Tags:** sklearn version, Python version

**What it does NOT capture automatically:**
- Custom metrics like F1, precision, recall on the test set
- Custom artifacts like confusion matrices or feature-importance plots
- DVC dataset hash or Git commit SHA

We supplement autologging with explicit `mlflow.log_metrics()` and `mlflow.log_artifact()` calls.

```python
mlflow.sklearn.autolog(log_input_examples=True, log_model_signatures=True, log_models=False)
# log_models=False because we log manually with our own signature and input_example
```

#### Model Registry
The **MLflow Model Registry** is a centralised catalogue of registered models. It provides:
- **Registered model name** — a human-readable identifier (e.g., `BreastCancerClassifier`)
- **Versions** — numbered model revisions, each pointing to a specific run's artifact
- **Aliases** — named pointers to versions (e.g., `champion`, `challenger`, `archived`)
- **Tags and descriptions** — additional metadata for documentation

**Version vs. Alias/Stage:**
- A **version** is immutable — it permanently refers to one specific artifact from one run.
- An **alias** (MLflow ≥ 2.x) is a mutable label that can be reassigned to any version, communicating its intended use. Older MLflow used `Staging/Production/Archived` stages; newer MLflow uses aliases/tags.

---

### A2 Environment Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install mlflow scikit-learn pandas matplotlib dvc pyyaml joblib
pip freeze > requirements.txt
mlflow --version  # mlflow, version 3.15.2
```

**Tool versions:**
- Python: 3.14
- MLflow: 3.15.2
- scikit-learn: 1.9.0
- DVC: (installed via `pip install dvc`)

---

### A3 Experiment Tracking

Three variants are trained in [`src/train.py`](src/train.py):

| Variant | n_estimators | max_depth | min_samples_split | Description |
|---|---|---|---|---|
| v1_baseline | 100 | 5 | 2 | Matches original config |
| v2_deep | 200 | 10 | 2 | Deeper trees, more estimators |
| v3_regularised | 150 | 3 | 5 | Shallower, larger min_samples |

**Autologging enabled:**
```python
mlflow.sklearn.autolog(log_input_examples=True, log_model_signatures=True, log_models=False, silent=True)
```

**Logged artifacts per run:**
1. `classification_report_<variant>.txt`
2. `confusion_matrix_<variant>.png`
3. `feature_importance_<variant>.png`
4. `config.yaml`

**Candidate selection criterion:** Highest F1-score on the held-out test set (20% stratified split).

---

### A4 Model Signature

Input: 30 numeric feature columns (breast cancer measurements)
Output: integer class label (0 = Malignant, 1 = Benign)

```python
input_example = pd.DataFrame(X_train[:5], columns=feature_names)
signature = infer_signature(input_example, y_pred[:5])
mlflow.sklearn.log_model(model, artifact_path="model", signature=signature, input_example=input_example)
```

**How a signature protects the API:**
- Wrong number of columns → `MlflowException` before prediction
- Wrong column type → caught at input validation
- Columns in wrong order → MLflow reorders if column names match

**What it cannot guarantee:**
- Correct units or measurement ranges (a column could be in wrong units)
- Data drift (distribution shift in valid-type data)
- Correct feature engineering applied before calling predict

---

### A5 Model Registry — Versions

Registered under name: **`BreastCancerClassifier`**

Run [`python src/register_models.py`](src/register_models.py) to register all three.

| Version | Source Run | Key Metric(s) | Change / Description | Decision |
|---|---|---|---|---|
| Version 1 | v1_baseline run | See MLflow UI | Baseline: n_est=100, depth=5 | Challenger |
| Version 2 | v2_deep run | Highest F1 | Deep: n_est=200, depth=10 | Champion (Production) |
| Version 3 | v3_regularised run | Lower F1 | Shallow: n_est=150, depth=3 | Archived |

---

### A6 Lifecycle Management

**Acceptance rule:** F1 ≥ 0.96 required for production promotion.

MLflow ≥ 2.x uses **aliases** (mutable named pointers) rather than deprecated stages.

| Alias | Maps To | Lifecycle State | Evidence / Reason |
|---|---|---|---|
| `champion` | Version 2 (v2_deep) | Production | Highest F1 ≥ 0.96 threshold |
| `challenger` | Version 1 (v1_baseline) | Staging / Candidate | Baseline; under evaluation |
| `archived` | Version 3 (v3_regularised) | Archived / Retired | Lower F1; superseded by champion |

**Retrieving the production model (teammate's workflow):**
```python
import mlflow
client = mlflow.MlflowClient()
champion_version = client.get_model_version_by_alias("BreastCancerClassifier", "champion")
model = mlflow.sklearn.load_model(f"models:/BreastCancerClassifier@champion")
```

**Critical Thinking — Should the highest-accuracy model always be promoted?**
No. Consider:
- **Class imbalance:** A model with 96% accuracy on a 95/5 dataset may have zero recall for the minority class.
- **Error costs:** For cancer detection, false negatives (missing a malignant case) are far more costly than false positives. Recall matters more than precision.
- **Fairness:** A globally high-accuracy model may underperform for specific demographic subgroups.
- **Latency/Stability:** A slightly lower-F1 model may be 10x faster or more stable under distribution shift.
- **Evaluation data quality:** Metrics are only as trustworthy as the test set.

---

## Part B — Data Versioning with DVC

### B1 Self-Learning Research

**Why Git is unsuitable for large datasets:**
Git stores the full content of every committed file in its object database. Large binary files (CSVs, images, model weights) bloat the repository, slow down cloning, and make diffs meaningless. GitHub's file size limit is 100 MB; typical ML datasets are gigabytes.

**What DVC tracks in Git vs. the remote:**
- **In Git:** `.dvc` metadata files (tiny YAML files containing the MD5 hash, size, and path of each tracked file)
- **In the DVC cache/remote:** The actual data files, stored by content hash (similar to Git objects)

**What a `.dvc` file represents:**
A `.dvc` file is a lightweight pointer. Example `data/dataset.csv.dvc`:
```yaml
outs:
- md5: a3f1b2c4...
  size: 45678
  path: dataset.csv
```
The MD5 hash uniquely identifies the dataset version regardless of the filename.

**Git commit vs. DVC data version:**
- A Git commit captures a snapshot of code, configs, and `.dvc` metadata files.
- A DVC data version is identified by the MD5 hash stored in the `.dvc` file; the actual bytes live in the DVC cache.
- Together, a Git commit + DVC hash = fully reproducible experiment state.

**DVC remote:**
A DVC remote is a storage location (local directory, S3, GCS, Azure Blob, etc.) where DVC pushes cached data. It enables teams to share large datasets without committing them to Git. `dvc push` uploads to the remote; `dvc pull` downloads.

**DVC and reproducibility:**
When data changes, only the `.dvc` metadata file changes. Any collaborator can `git checkout` a specific commit, then `dvc checkout` or `dvc pull` to restore the exact dataset version — fully reproducible without storing large files in Git.

---

### B2 DVC Initialization

```bash
pip install dvc
dvc --version

git status          # before dvc init
dvc init
git status          # after: .dvc/ and .dvcignore created
git add .dvc .dvcignore
git commit -m "Initialize DVC"
```

DVC creates:
- `.dvc/config` — remote and other configuration
- `.dvc/.gitignore` — excludes the DVC cache from Git
- `.dvcignore` — similar to `.gitignore` for DVC

These should be version-controlled so collaborators get the same DVC configuration when they clone the repository.

---

### B3 Track a Dataset

```bash
dvc add data/dataset.csv
git add data/dataset.csv.dvc .gitignore
git commit -m "Track dataset with DVC"
```

The `dvc add` command:
1. Computes the MD5 hash of `data/dataset.csv`
2. Copies it to `.dvc/cache/<md5[:2]>/<md5[2:]>`
3. Creates `data/dataset.csv.dvc` with the hash and metadata
4. Adds `data/dataset.csv` to `.gitignore` (so Git does not track the actual data)

Git now tracks the **pointer** (`.dvc` file); DVC tracks the **content** (cache/remote).

---

### B4 Configure DVC Remote

```bash
mkdir -p ../dvc-storage
dvc remote add -d localremote ../dvc-storage
git add .dvc/config
git commit -m "Configure DVC local remote"
dvc push
```

> **Note:** A local directory remote is useful for single-machine learning. For team collaboration, use an approved cloud remote (S3, GCS, Azure Blob) with secure credential management. Never commit credentials or access tokens.

---

### B5 Create and Recover Dataset Versions

Run [`python src/dvc_versioning.py`](src/dvc_versioning.py) to automate all steps.

| Step | Action |
|---|---|
| v1 | Full sklearn breast_cancer (569 rows) → `dvc add` → `git commit` → `dvc push` |
| v2 | Add 31 synthetic rows (600 rows) → `dvc add` → `git commit` → `dvc push` |
| v3 | Drop outliers (mean radius > mean+3σ) → `dvc add` → `git commit` → `dvc push` |
| Recovery | `git checkout <v1_commit> -- data/dataset.csv.dvc` + `dvc checkout` |

**Manual recovery steps:**
```bash
# Inspect Git history
git log --oneline

# Checkout the .dvc metadata from the v1 commit
git checkout <v1-commit-sha> -- data/dataset.csv.dvc

# Restore the data file from DVC cache/remote
dvc checkout data/dataset.csv.dvc

# Verify: row count should be 569
python -c "import pandas as pd; df=pd.read_csv('data/dataset.csv'); print(len(df))"

# Return to latest
git checkout HEAD -- data/dataset.csv.dvc
dvc checkout data/dataset.csv.dvc
```

---

### B6 Dataset Version Comparison

| Version | Git Commit | Rows | Columns | Change Description | MD5 Verified |
|---|---|---|---|---|---|
| v1 (baseline) | (see git log) | 569 | 31 | Full sklearn breast_cancer dataset | ✓ |
| v2 (augmented) | (see git log) | 600 | 31 | +31 synthetic rows (augmentation) | ✓ |
| v3 (cleaned) | (see git log) | ~595 | 31 | Dropped mean-radius outliers | ✓ |

**Verification answer:** DVC restoration is verified by comparing (a) row count, (b) MD5 hash of the restored file against the hash recorded in the `.dvc` file, and (c) file size.

**Why a filename alone is insufficient:** The filename `dataset.csv` is the same across all three versions. Only the MD5 hash (stored in the `.dvc` file and the DVC cache) uniquely identifies the exact byte content of a dataset version.

---

### B7 DVC Pipelines

The [`dvc.yaml`](dvc.yaml) file defines a 4-stage pipeline:

```
prepare_data → train → evaluate → register
```

```bash
dvc repro          # Run only changed stages
dvc dag            # Visualise the DAG
```

Each stage declares:
- `cmd` — the command to run
- `deps` — inputs (code, data, configs); changes trigger a rerun
- `outs` — outputs tracked by DVC
- `params` — config values; changes also trigger reruns

**Linking a pipeline output to an MLflow run:**
The `train` stage logs the MLflow run ID to `models/run_ids.txt`. The `register` stage reads this file to register the models. Additionally, each MLflow run is tagged with the Git commit SHA and DVC dataset hash, creating a bidirectional traceability link.

---

## Part C — Git + DVC + MLflow Integration

| Tool | What it tracks | Where information lives | Why it matters |
|---|---|---|---|
| **Git** | Source code, configs, `.dvc` metadata files, `dvc.yaml` | `.git/` object database + remote repository | Provides code history; the `.dvc` files link code state to data state |
| **DVC** | Data versions, pipeline stage outputs, dependencies | `.dvc/cache/` + DVC remote storage | Allows large files to be versioned without bloating Git; `dvc repro` reruns only what changed |
| **MLflow** | Experiment runs, hyperparameters, metrics, artifacts, registered models, aliases | `mlflow.db` (SQLite) + `mlruns/` artifact store | Centralised experiment log; Model Registry tracks which model version is in production |

**How a teammate could investigate a prediction:**
1. Find the MLflow run: look up the model alias `champion` in the Model Registry → get the run ID.
2. From the run tags, read `git_commit` → `git checkout <sha>` to restore the exact training code.
3. From the run tags, read `dvc_dataset_hash` → find the Git commit where `data/dataset.csv.dvc` contains that MD5 → `git checkout <data-commit> -- data/dataset.csv.dvc && dvc checkout` to restore the exact dataset.
4. Reproduce: `python src/train.py` should produce the same metrics.

**Commit training code:**
```bash
git add src/ configs/ dvc.yaml requirements.txt README.md .gitignore
git commit -m "Add training code, DVC pipeline, and MLflow integration"
```

**Make dataset version available:**
```bash
dvc push   # push current dataset version to remote
```

**Record Git commit and DVC hash in MLflow:**
```python
mlflow.set_tags({"git_commit": get_git_commit(), "dvc_dataset_hash": get_dvc_dataset_hash(dataset_csv)})
```

---

## Challenges and Lessons Learned

1. **MLflow 2.x+ aliases vs. deprecated stages:** MLflow ≥ 2.0 deprecated `Staging/Production/Archived` stage strings in favour of aliases. The `register_models.py` script handles both with a `try/except` fallback.

2. **`artifact_path` deprecation:** MLflow 3.x warns that `artifact_path` is deprecated in favour of `name`. Updated `log_model` calls accordingly.

3. **`y_pred` → `y_proba` deprecation in sklearn 1.9:** `roc_curve` parameter renamed; updated to `y_proba=`.

4. **DVC on Windows:** DVC path separators and subprocess handling require careful quoting; the `dvc_versioning.py` script uses `str()` conversions throughout.

5. **Git not initialised:** The repository was not a Git repository initially; `git init` must precede `dvc init`.

6. **DVC checkout overwrites:** `dvc checkout` can overwrite the working file silently. Always keep a clean working tree before switching versions; use `git stash` or a temporary branch.

---

## References

- MLflow documentation: https://mlflow.org/docs/latest/index.html
- MLflow Model Registry: https://mlflow.org/docs/latest/model-registry.html
- MLflow Model Signatures: https://mlflow.org/docs/latest/models.html#model-signature
- DVC documentation: https://dvc.org/doc
- DVC Get Started — Data Versioning: https://dvc.org/doc/start/data-management
- scikit-learn Random Forest: https://scikit-learn.org/stable/modules/ensemble.html#forest
- sklearn breast_cancer dataset: https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_breast_cancer.html
