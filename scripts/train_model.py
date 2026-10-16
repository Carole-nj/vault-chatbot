"""Train the intent classifier: TF-IDF + Linear SVM (calibrated) vs Logistic Regression.

Split 70/15/15. The best model on validation macro-F1 is evaluated once on the test set and saved.
"""
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.nlp import preprocess  # noqa: E402  (same preprocessing as inference)


def features():
    return FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=2)),
    ])


def main():
    df = pd.read_csv(ROOT / "data" / "training_data.csv").dropna()
    df["clean"] = df["text"].map(preprocess)
    df = df[df["clean"].str.len() > 0].drop_duplicates("clean")

    X_train, X_tmp, y_train, y_tmp = train_test_split(df["clean"], df["intent"], test_size=0.30, stratify=df["intent"], random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_tmp, y_tmp, test_size=0.50, stratify=y_tmp, random_state=42)
    print(f"train={len(X_train)} val={len(X_val)} test={len(X_test)} intents={df['intent'].nunique()}")

    candidates = {
        "linear_svm": Pipeline([("f", features()), ("c", CalibratedClassifierCV(LinearSVC(C=1.0), cv=3))]),
        "logistic_regression": Pipeline([("f", features()), ("c", LogisticRegression(C=10, max_iter=2000))]),
    }
    val_scores = {}
    for name, pipe in candidates.items():
        pipe.fit(X_train, y_train)
        val_scores[name] = f1_score(y_val, pipe.predict(X_val), average="macro")
        print(f"{name}: validation macro-F1 = {val_scores[name]:.4f}")

    best = max(val_scores, key=val_scores.get)
    model = candidates[best]
    pred = model.predict(X_test)
    report = classification_report(y_test, pred, output_dict=True, zero_division=0)
    metrics = {
        "selected_model": best,
        "validation_macro_f1": val_scores,
        "test_accuracy": accuracy_score(y_test, pred),
        "test_macro_precision": report["macro avg"]["precision"],
        "test_macro_recall": report["macro avg"]["recall"],
        "test_macro_f1": report["macro avg"]["f1-score"],
        "per_intent": {k: v for k, v in report.items() if k not in ("accuracy", "macro avg", "weighted avg")},
        "sizes": {"train": len(X_train), "val": len(X_val), "test": len(X_test)},
        "caveat": "Dataset is template-generated; expect lower accuracy on real customer wording. Add real enquiries to data/seed_extra.csv and retrain.",
    }
    (ROOT / "models").mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    joblib.dump(model, ROOT / "models" / "intent_model.joblib")
    (ROOT / "reports" / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    labels = sorted(df["intent"].unique())
    pd.DataFrame(confusion_matrix(y_test, pred, labels=labels), index=labels, columns=labels).to_csv(ROOT / "reports" / "confusion_matrix.csv")
    print(f"Selected {best}: test accuracy={metrics['test_accuracy']:.4f} macro-F1={metrics['test_macro_f1']:.4f}")


if __name__ == "__main__":
    main()
