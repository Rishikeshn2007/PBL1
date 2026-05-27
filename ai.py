import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


DATASET_PATH = "dataset.csv"
TARGET_COLUMN = "Chronic Kidney Disease: yes"

FEATURE_COLUMNS = [
    "Specific Gravity",
    "Albumin",
]

TEST_SIZE = 0.30
RANDOM_STATE = 4


def load_dataset(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df = df.replace(["?", "\t?", " ?"], np.nan)

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' was not found in {path}.")

    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.fillna(df.median(numeric_only=True))
    return df


def split_dataset(df):
    missing_features = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing_features:
        raise ValueError(f"Missing feature columns: {missing_features}")

    x = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN].astype(int)

    return train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )


def build_models():
    return {
        "Logistic Regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        C=0.01,
                        max_iter=1000,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=1,
            min_samples_leaf=60,
            random_state=RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=5,
            max_depth=1,
            min_samples_leaf=80,
            max_features=1,
            random_state=42,
        ),
    }


def evaluate_models(models, x_train, x_test, y_train, y_test):
    results = []

    for name, model in models.items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)

        accuracy = accuracy_score(y_test, predictions)
        precision = precision_score(y_test, predictions, zero_division=0)
        recall = recall_score(y_test, predictions, zero_division=0)

        results.append(
            {
                "Algorithm": name,
                "Accuracy": accuracy,
                "Precision": precision,
                "Recall": recall,
            }
        )

    return pd.DataFrame(results)


def print_results(results):
    display_results = results.copy()
    for column in ["Accuracy", "Precision", "Recall"]:
        display_results[column] = (display_results[column] * 100).round(2)

    print("\nCKD Prediction Model Comparison")
    print(display_results.to_string(index=False))

    best_model = results.sort_values("Accuracy", ascending=False).iloc[0]
    print("\nBest model based on accuracy:")
    print(
        f"{best_model['Algorithm']} "
        f"with {best_model['Accuracy'] * 100:.2f}% accuracy"
    )

    print("\nPrediction labels:")
    print("1 = CKD")
    print("0 = No CKD")

def main():
    df = load_dataset(DATASET_PATH)
    x_train, x_test, y_train, y_test = split_dataset(df)
    models = build_models()
    results = evaluate_models(models, x_train, x_test, y_train, y_test)
    print_results(results)


if __name__ == "__main__":
    main()
