"""Data loading, preprocessing, and Decision Tree training for at-risk prediction.

The model predicts ``at_risk`` (1 = finished the course with a D or F) from the
synthetic WolfHacks student-outcomes dataset. A fitted "bundle" (pipeline plus
evaluation metrics and reference statistics) is persisted with ``joblib`` so the
Streamlit app only retrains when the data or scikit-learn version changes.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, export_text

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "synthetic_students.csv"
MODEL_PATH = ROOT / "models" / "risk_tree.joblib"

TARGET = "at_risk"
CATEGORICAL = ["course", "class_year"]
NUMERIC = [
    "credit_hours",
    "work_hours_per_week",
    "avg_weekly_study_hours",
    "study_sessions_logged",
    "materials_uploaded",
    "practice_quizzes_taken",
    "avg_practice_quiz_score",
    "flashcards_reviewed",
    "avg_days_started_before_exam",
    "on_time_submission_rate",
    "missed_deadlines",
    "late_night_study_pct",
    "attendance_rate",
    "avg_sleep_hours",
    "midterm_score",
]
FEATURES = CATEGORICAL + NUMERIC
# Stored in the CSV as "83%" strings; converted to fractions (0.83) on load.
PERCENT_COLS = ["on_time_submission_rate", "late_night_study_pct", "attendance_rate"]
CLASS_YEARS = ["Freshman", "Sophomore", "Junior", "Senior"]

LABELS = {
    "course": "Course",
    "class_year": "Class year",
    "credit_hours": "Credit hours",
    "work_hours_per_week": "Work hours / week",
    "avg_weekly_study_hours": "Weekly study hours",
    "study_sessions_logged": "Study sessions logged",
    "materials_uploaded": "Materials uploaded",
    "practice_quizzes_taken": "Practice quizzes taken",
    "avg_practice_quiz_score": "Avg practice quiz score",
    "flashcards_reviewed": "Flashcards reviewed",
    "avg_days_started_before_exam": "Days started before exam",
    "on_time_submission_rate": "On-time submission rate",
    "missed_deadlines": "Missed deadlines",
    "late_night_study_pct": "Late-night study share",
    "attendance_rate": "Attendance rate",
    "avg_sleep_hours": "Avg sleep hours",
    "midterm_score": "Midterm score",
}

# (min, max, step) for UI inputs, matching the ranges in the data dictionary.
FEATURE_RANGES = {
    "credit_hours": (12, 18, 1),
    "work_hours_per_week": (0, 35, 1),
    "avg_weekly_study_hours": (0.5, 18.0, 0.5),
    "study_sessions_logged": (0, 150, 1),
    "materials_uploaded": (0, 40, 1),
    "practice_quizzes_taken": (0, 60, 1),
    "avg_practice_quiz_score": (30.0, 100.0, 0.5),
    "flashcards_reviewed": (0, 1500, 5),
    "avg_days_started_before_exam": (0.0, 14.0, 0.5),
    "on_time_submission_rate": (0.30, 1.00, 0.01),
    "missed_deadlines": (0, 20, 1),
    "late_night_study_pct": (0.0, 0.90, 0.01),
    "attendance_rate": (0.30, 1.00, 0.01),
    "avg_sleep_hours": (3.5, 10.0, 0.1),
    "midterm_score": (20, 100, 1),
}

# Actionable features -> (higher_is_better, advice). Used to build suggestions.
ADVICE = {
    "midterm_score": (True, "Review every missed midterm question with your instructor or a tutor — "
                            "office hours and the tutoring center are the fastest way to close gaps."),
    "attendance_rate": (True, "Attend every lecture and recitation; attendance is one of the strongest "
                              "signals of finishing with a C or better."),
    "avg_weekly_study_hours": (True, "Schedule more consistent study blocks each week (use the Study Logger "
                                     "timer to hit a weekly target)."),
    "avg_days_started_before_exam": (True, "Start exam prep earlier — aim to begin reviewing at least a week "
                                           "before each exam."),
    "on_time_submission_rate": (True, "Put every deadline on the calendar and set a personal due date "
                                      "1–2 days before the real one."),
    "missed_deadlines": (False, "You've missed several deadlines — talk to your instructor about late "
                                "options and use calendar reminders going forward."),
    "practice_quizzes_taken": (True, "Generate AI practice quizzes from your notes in the Resource Hub — "
                                     "active recall beats re-reading."),
    "avg_practice_quiz_score": (True, "Re-take practice quizzes on weak topics until you consistently score "
                                      "80%+."),
    "flashcards_reviewed": (True, "Review flashcards in short daily bursts to build spaced repetition."),
    "late_night_study_pct": (False, "Shift study time out of the midnight–4 a.m. window; late-night "
                                    "sessions are less effective."),
    "avg_sleep_hours": (True, "Protect 7–9 hours of sleep — memory consolidation happens overnight."),
    "work_hours_per_week": (False, "Your work schedule is heavy relative to on-track peers; consider "
                                   "talking to an academic advisor about balancing hours."),
    "materials_uploaded": (True, "Upload lecture notes and slides so you can generate summaries and "
                                 "practice material from them."),
}

SUPPORT_RESOURCES = [
    "📅 Book instructor or TA office hours this week",
    "🧑‍🏫 Visit the campus tutoring / academic success center",
    "🧭 Meet with your academic advisor about course load and options",
    "💬 Form or join a study group for this course",
    "🧘 Check in with counseling & wellness services if stress or sleep is a factor",
]


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def _parse_percent(series: pd.Series) -> pd.Series:
    """Convert values like ``"83%"`` to ``0.83``; numeric fractions pass through."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    stripped = series.astype(str).str.strip()
    values = pd.to_numeric(stripped.str.rstrip("%"), errors="coerce")
    return pd.Series(np.where(stripped.str.endswith("%"), values / 100.0, values), index=series.index)


def load_data(path=DATA_PATH, require_target: bool = True) -> pd.DataFrame:
    """Load a student CSV (path or file-like) and coerce every column to its proper type.

    ``require_target=False`` accepts files without the ``at_risk`` column, e.g. a new class to score.
    """
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in FEATURES + ([TARGET] if require_target else []) if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
    for col in PERCENT_COLS:
        df[col] = _parse_percent(df[col])
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in CATEGORICAL:
        df[col] = df[col].astype(str).str.strip()
    if TARGET in df.columns:
        df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce").astype("Int64")
    return df


def held_out_split(df: pd.DataFrame, random_state: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The exact stratified 80/20 split used for training, so held-out rows can be exported and re-tested."""
    return train_test_split(df, test_size=0.2, stratify=df[TARGET], random_state=random_state)


# --------------------------------------------------------------------------- #
# Training
# --------------------------------------------------------------------------- #
def build_pipeline(**tree_params: Any) -> Pipeline:
    """Imputation + one-hot encoding feeding a DecisionTreeClassifier."""
    preprocess = ColumnTransformer(
        [
            # add_indicator lets the tree use "value was missing" (e.g. no quizzes taken) as a signal.
            ("num", SimpleImputer(strategy="median", add_indicator=True), NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
        ]
    )
    tree = DecisionTreeClassifier(random_state=42, **tree_params)
    return Pipeline([("prep", preprocess), ("tree", tree)])


def _base_feature(encoded_name: str) -> str:
    """Map an encoded column name (e.g. ``cat__course_BIO 181``) back to its source feature."""
    name = encoded_name.split("__", 1)[-1]
    if name.startswith("missingindicator_"):
        return name[len("missingindicator_"):]
    for cat in CATEGORICAL:
        if name.startswith(cat + "_"):
            return cat
    return name


def train_model(df: pd.DataFrame | None = None, random_state: int = 42) -> dict[str, Any]:
    """Tune and train the decision tree, returning a bundle with metrics and metadata."""
    df = load_data() if df is None else df
    df = df.assign(**{TARGET: df[TARGET].astype(int)})
    y = df[TARGET]
    train_df, test_df = held_out_split(df, random_state)
    X_train, y_train = train_df[FEATURES], train_df[TARGET]
    X_test, y_test = test_df[FEATURES], test_df[TARGET]

    search = GridSearchCV(
        build_pipeline(),
        param_grid={
            "tree__max_depth": [3, 4, 5, 6, 8],
            "tree__min_samples_leaf": [5, 10, 20],
            "tree__criterion": ["gini", "entropy"],
            "tree__class_weight": [None, "balanced"],
        },
        # F1 on the at-risk class: we care about catching struggling students, not just accuracy.
        scoring="f1",
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state),
        n_jobs=-1,
    )
    search.fit(X_train, y_train)
    pipe: Pipeline = search.best_estimator_

    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "baseline_accuracy": max(y_test.mean(), 1 - y_test.mean()),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "cv_f1": search.best_score_,
    }

    encoded_names = pipe.named_steps["prep"].get_feature_names_out()
    importances: dict[str, float] = {f: 0.0 for f in FEATURES}
    for name, value in zip(encoded_names, pipe.named_steps["tree"].feature_importances_):
        importances[_base_feature(name)] += float(value)

    on_track = df[df[TARGET] == 0]
    reference = {
        col: {"median": float(on_track[col].median()), "std": float(df[col].std() or 1.0)}
        for col in NUMERIC
    }

    return {
        "pipeline": pipe,
        "metrics": metrics,
        "best_params": {k.replace("tree__", ""): v for k, v in search.best_params_.items()},
        "feature_importances": dict(sorted(importances.items(), key=lambda kv: -kv[1])),
        "reference": reference,
        "medians": {col: float(df[col].median()) for col in NUMERIC},
        "n_train": len(X_train),
        "n_test": len(X_test),
        "positive_rate": float(y.mean()),
        "sklearn_version": sklearn.__version__,
        "data_mtime": DATA_PATH.stat().st_mtime if DATA_PATH.exists() else None,
    }


def save_bundle(bundle: dict[str, Any], path: Path = MODEL_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)


def load_or_train(force: bool = False, path: Path = MODEL_PATH) -> dict[str, Any]:
    """Load the persisted bundle, retraining if missing, stale, or built by another sklearn version."""
    if not force and path.exists():
        try:
            bundle = joblib.load(path)
            data_mtime = DATA_PATH.stat().st_mtime if DATA_PATH.exists() else None
            if bundle.get("sklearn_version") == sklearn.__version__ and bundle.get("data_mtime") == data_mtime:
                return bundle
        except Exception:  # corrupt or incompatible pickle -> retrain below
            pass
    bundle = train_model()
    save_bundle(bundle, path)
    return bundle


# --------------------------------------------------------------------------- #
# Prediction & explanation
# --------------------------------------------------------------------------- #
def format_value(feature: str, value: float | None) -> str:
    """Human-readable formatting for a feature value."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "not reported"
    if feature in PERCENT_COLS:
        return f"{value * 100:.0f}%"
    if feature == "avg_practice_quiz_score":
        return f"{value:.1f}"
    if float(value).is_integer():
        return f"{int(value)}"
    return f"{value:.1f}"


def _rule_text(encoded_name: str, threshold: float, went_left: bool, value: float) -> str:
    name = encoded_name.split("__", 1)[-1]
    if name.startswith("missingindicator_"):
        feat = name[len("missingindicator_"):]
        return f"{LABELS[feat]} {'was reported' if went_left else 'was not reported'}"
    for cat in CATEGORICAL:
        if name.startswith(cat + "_"):
            level = name[len(cat) + 1:]
            return f"{LABELS[cat]} {'is not' if went_left else 'is'} {level}"
    op = "≤" if went_left else ">"
    return f"{LABELS[name]} {op} {format_value(name, threshold)}  (you: {format_value(name, value)})"


def profile_to_frame(profile: dict[str, Any]) -> pd.DataFrame:
    """Turn a dict of feature values into a one-row DataFrame in training column order."""
    row = {f: profile.get(f, np.nan) for f in FEATURES}
    for f in NUMERIC:
        row[f] = np.nan if row[f] is None else float(row[f])
    return pd.DataFrame([row], columns=FEATURES)


def explain_path(pipe: Pipeline, X_row: pd.DataFrame) -> list[str]:
    """Return the decision rules the tree followed for a single profile."""
    prep, tree = pipe.named_steps["prep"], pipe.named_steps["tree"]
    Xt = prep.transform(X_row)
    names = prep.get_feature_names_out()
    leaf = tree.apply(Xt)[0]
    rules = []
    for node in tree.decision_path(Xt).indices:
        if node == leaf:
            continue
        f, thr = tree.tree_.feature[node], tree.tree_.threshold[node]
        value = float(Xt[0, f])
        rules.append(_rule_text(names[f], thr, value <= thr, value))
    return rules


def suggestions(bundle: dict[str, Any], profile: dict[str, Any], k: int = 4) -> list[dict[str, Any]]:
    """Rank actionable gaps vs. on-track peers, weighted by how much the tree relies on each feature."""
    ref, importances = bundle["reference"], bundle["feature_importances"]
    scored = []
    for feat, (higher_better, advice) in ADVICE.items():
        value = profile.get(feat)
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        target, std = ref[feat]["median"], ref[feat]["std"] or 1.0
        gap = (target - value) / std if higher_better else (value - target) / std
        if gap > 0.25:
            scored.append((gap * (0.5 + importances.get(feat, 0.0)), feat, advice, value, target))
    scored.sort(key=lambda s: -s[0])
    return [
        {
            "feature": feat,
            "label": LABELS[feat],
            "advice": advice,
            "you": format_value(feat, value),
            "target": format_value(feat, target),
        }
        for _, feat, advice, value, target in scored[:k]
    ]


def risk_tier(probability: float) -> str:
    if probability >= 0.5:
        return "at_risk"
    if probability >= 0.3:
        return "watch"
    return "on_track"


def predict_risk(bundle: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Predict at-risk probability for one profile and explain it."""
    pipe: Pipeline = bundle["pipeline"]
    X_row = profile_to_frame(profile)
    probability = float(pipe.predict_proba(X_row)[0, 1])
    return {
        "probability": probability,
        "prediction": int(pipe.predict(X_row)[0]),
        "tier": risk_tier(probability),
        "path": explain_path(pipe, X_row),
        "suggestions": suggestions(bundle, profile),
    }


def score_students(bundle: dict[str, Any], df: pd.DataFrame) -> pd.DataFrame:
    """Batch-predict a whole CSV of students, adding probability, tier and the top suggestion."""
    pipe: Pipeline = bundle["pipeline"]
    scored = df.copy()
    scored["risk_probability"] = pipe.predict_proba(df[FEATURES])[:, 1]
    scored["predicted_at_risk"] = pipe.predict(df[FEATURES]).astype(int)
    scored["risk_tier"] = scored["risk_probability"].map(risk_tier)
    top = []
    for record in df[FEATURES].to_dict("records"):
        tips = suggestions(bundle, record, k=1)
        top.append(f"{tips[0]['label']}: {tips[0]['advice']}" if tips else "")
    scored["top_suggestion"] = top
    return scored.sort_values("risk_probability", ascending=False)


def evaluate_labeled(scored: pd.DataFrame) -> dict[str, Any] | None:
    """Metrics for an uploaded CSV that includes the true at_risk outcome."""
    if TARGET not in scored.columns or scored[TARGET].isna().all():
        return None
    labeled = scored.dropna(subset=[TARGET])
    y_true, y_pred = labeled[TARGET].astype(int), labeled["predicted_at_risk"]
    return {
        "n": len(labeled),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, labeled["risk_probability"]) if y_true.nunique() == 2 else None,
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
    }


def tree_rules_text(bundle: dict[str, Any], max_depth: int = 10) -> str:
    """Full text dump of the trained tree's rules."""
    pipe: Pipeline = bundle["pipeline"]
    names = [n.split("__", 1)[-1] for n in pipe.named_steps["prep"].get_feature_names_out()]
    return export_text(pipe.named_steps["tree"], feature_names=names, max_depth=max_depth)


def encoded_feature_names(bundle: dict[str, Any]) -> list[str]:
    return [n.split("__", 1)[-1] for n in bundle["pipeline"].named_steps["prep"].get_feature_names_out()]


if __name__ == "__main__":
    b = load_or_train(force=True)
    print("Best params:", b["best_params"])
    for key, val in b["metrics"].items():
        print(f"{key:>18}: {val}")
    print("Top features:", list(b["feature_importances"].items())[:6])
