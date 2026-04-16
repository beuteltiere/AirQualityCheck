"""
Temperature Drop Predictor
--------------------------
Neural network that predicts the likelihood of temperature dropping
below a threshold within the next 30 minutes.

Usage:
  python temp_nn.py --train               # Train the model
  python temp_nn.py --predict 24.5        # Predict for a single new reading
  python temp_nn.py --predict 24.5 --history "24.8,24.7,24.6,..."  # With history
"""

import argparse
import json
import os
import warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, roc_curve, ConfusionMatrixDisplay
)

warnings.filterwarnings("ignore")

# ─── Configuration ────────────────────────────────────────────────────────────
THRESHOLD     = 25.0      # °C — predict drop BELOW this value
PREDICT_AHEAD = 30        # minutes ahead to predict
WINDOW_SIZE   = 60        # minutes of history used as input features
DATA_PATH     = "/mnt/user-data/uploads/TestTempInCelsius.csv"
MODEL_PATH    = "/mnt/user-data/outputs/temp_model.joblib"
SCALER_PATH   = "/mnt/user-data/outputs/temp_scaler.joblib"
META_PATH     = "/mnt/user-data/outputs/temp_meta.json"


# ─── Feature Engineering ──────────────────────────────────────────────────────
def make_features(temps: np.ndarray) -> np.ndarray:
    """
    Build a feature vector from a window of temperature readings.
    temps: 1-D array of length WINDOW_SIZE (oldest → newest)
    """
    t = np.array(temps, dtype=float)
    features = []

    # Raw readings (last 30 of the window to keep size reasonable)
    features.extend(t[-30:].tolist())

    # Rolling stats over different windows
    for w in [5, 10, 20, 30, 60]:
        chunk = t[-w:] if len(t) >= w else t
        features.append(float(np.mean(chunk)))
        features.append(float(np.std(chunk)))
        features.append(float(np.min(chunk)))
        features.append(float(np.max(chunk)))

    # Trend (linear slope) over last 30 and 60 mins
    for w in [30, 60]:
        chunk = t[-w:] if len(t) >= w else t
        if len(chunk) > 1:
            slope = np.polyfit(range(len(chunk)), chunk, 1)[0]
        else:
            slope = 0.0
        features.append(float(slope))

    # Distance to threshold
    features.append(float(t[-1] - THRESHOLD))           # current gap
    features.append(float(np.mean(t[-10:]) - THRESHOLD)) # recent mean gap

    # Rate of change
    features.append(float(t[-1] - t[-2]) if len(t) >= 2 else 0.0)   # last 1 min
    features.append(float(t[-1] - t[-5]) if len(t) >= 5 else 0.0)   # last 5 min
    features.append(float(t[-1] - t[-15]) if len(t) >= 15 else 0.0) # last 15 min

    # How many of last 10 readings are within 1°C of threshold
    features.append(float(np.sum(t[-10:] < THRESHOLD + 1.0)))

    return np.array(features, dtype=float)


# ─── Dataset Builder ──────────────────────────────────────────────────────────
def build_dataset(df: pd.DataFrame):
    """
    Slide a window over each room's time series and create (X, y) pairs.
    y = 1 if temp drops below THRESHOLD in the next PREDICT_AHEAD minutes.
    """
    X_list, y_list = [], []

    for room, group in df.groupby("room"):
        group = group.sort_values("time").reset_index(drop=True)
        temps = group["temperature"].values
        n = len(temps)

        print(f"  {room}: {n} readings", end="")

        count = 0
        for i in range(WINDOW_SIZE, n - PREDICT_AHEAD):
            window = temps[i - WINDOW_SIZE : i]
            future = temps[i : i + PREDICT_AHEAD]
            label  = int(np.any(future < THRESHOLD))

            X_list.append(make_features(window))
            y_list.append(label)
            count += 1

        pos = sum(y_list[-count:])
        print(f"  →  {count} samples  |  {pos} positive ({100*pos/count:.1f}%)")

    return np.array(X_list, dtype=float), np.array(y_list, dtype=int)


# ─── Training ─────────────────────────────────────────────────────────────────
def train():
    print("=" * 60)
    print(f"  Temperature Drop Predictor — Training")
    print(f"  Threshold : {THRESHOLD}°C")
    print(f"  Predicts  : next {PREDICT_AHEAD} minutes")
    print(f"  History   : last {WINDOW_SIZE} minutes")
    print("=" * 60)

    print("\n[1/5] Loading data …")
    df = pd.read_csv(DATA_PATH, parse_dates=["time"])
    print(f"      {len(df):,} rows, rooms: {sorted(df['room'].unique())}")

    print("\n[2/5] Building features …")
    X, y = build_dataset(df)
    print(f"\n      Total samples: {len(X):,}  |  Features: {X.shape[1]}")
    print(f"      Class balance: {y.sum():,} positive ({100*y.mean():.1f}%)")

    print("\n[3/5] Splitting & scaling …")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    print("\n[4/5] Training neural network …")
    model = MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),
        activation="relu",
        solver="adam",
        max_iter=200,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=15,
        random_state=42,
        verbose=True,
        learning_rate_init=0.001,
    )
    model.fit(X_train_s, y_train)
    print(f"      Stopped at iteration {model.n_iter_}")

    print("\n[5/5] Evaluating …")
    y_pred  = model.predict(X_test_s)
    y_proba = model.predict_proba(X_test_s)[:, 1]
    auc     = roc_auc_score(y_test, y_proba)

    print("\n── Classification Report ──────────────────────────────")
    print(classification_report(y_test, y_pred,
                                 target_names=["Will NOT drop", "WILL drop"]))
    print(f"  ROC-AUC: {auc:.4f}")

    # Save model artefacts
    os.makedirs("/mnt/user-data/outputs", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    meta = {
        "threshold": THRESHOLD,
        "predict_ahead": PREDICT_AHEAD,
        "window_size": WINDOW_SIZE,
        "n_features": X.shape[1],
        "roc_auc": round(auc, 4),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    # ── Plots ──────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle(
        f"Temperature Drop Predictor  (threshold={THRESHOLD}°C, horizon={PREDICT_AHEAD} min)",
        fontsize=13, fontweight="bold"
    )

    # Loss curve
    axes[0].plot(model.loss_curve_, label="Train loss", color="#2196F3")
    if hasattr(model, "validation_scores_"):
        axes[0].plot(
            [1 - s for s in model.validation_scores_],
            label="Val loss (1-acc)", color="#FF5722", linestyle="--"
        )
    axes[0].set_title("Training Loss Curve")
    axes[0].set_xlabel("Iteration")
    axes[0].set_ylabel("Loss")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # ROC curve
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    axes[1].plot(fpr, tpr, color="#4CAF50", lw=2, label=f"AUC = {auc:.3f}")
    axes[1].plot([0, 1], [0, 1], "k--", alpha=0.4)
    axes[1].set_title("ROC Curve")
    axes[1].set_xlabel("False Positive Rate")
    axes[1].set_ylabel("True Positive Rate")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm,
                                   display_labels=["Won't drop", "Will drop"])
    disp.plot(ax=axes[2], colorbar=False, cmap="Blues")
    axes[2].set_title("Confusion Matrix")

    plt.tight_layout()
    plot_path = "/mnt/user-data/outputs/training_results.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"\n  Plots saved → {plot_path}")
    print(f"  Model saved → {MODEL_PATH}")
    print(f"\n✅  Done!  ROC-AUC = {auc:.4f}")
    return model, scaler


# ─── Prediction ───────────────────────────────────────────────────────────────
def predict(new_temp: float, history: list[float] | None = None):
    """
    Predict probability of temperature dropping below threshold
    in the next PREDICT_AHEAD minutes.

    new_temp : the most recent temperature reading
    history  : list of previous readings (oldest → newest), optional
    """
    model  = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    with open(META_PATH) as f:
        meta = json.load(f)

    # Build a full WINDOW_SIZE history
    if history is None:
        history = []
    history = list(history) + [new_temp]

    # Pad or trim to WINDOW_SIZE
    window_size = meta["window_size"]
    if len(history) < window_size:
        pad = [history[0]] * (window_size - len(history))
        window = pad + history
    else:
        window = history[-window_size:]

    features = make_features(np.array(window)).reshape(1, -1)
    features_s = scaler.transform(features)
    proba = model.predict_proba(features_s)[0, 1]

    print(f"\n{'='*45}")
    print(f"  Current temperature : {new_temp}°C")
    print(f"  Threshold           : {meta['threshold']}°C")
    print(f"  Prediction horizon  : {meta['predict_ahead']} minutes")
    print(f"{'─'*45}")
    print(f"  ▶  Drop probability : {proba*100:.1f}%")

    if proba < 0.20:
        verdict = "🟢  UNLIKELY to drop below threshold"
    elif proba < 0.50:
        verdict = "🟡  POSSIBLE drop — monitor closely"
    elif proba < 0.75:
        verdict = "🟠  LIKELY to drop below threshold"
    else:
        verdict = "🔴  VERY LIKELY to drop below threshold"

    print(f"  {verdict}")
    print(f"{'='*45}\n")
    return proba


# ─── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Temperature Drop Predictor")
    parser.add_argument("--train",   action="store_true", help="Train the model")
    parser.add_argument("--predict", type=float, metavar="TEMP",
                        help="Predict for a new temperature reading")
    parser.add_argument("--history", type=str, default=None,
                        help="Comma-separated recent readings (oldest first)")
    args = parser.parse_args()

    if args.train:
        train()
    elif args.predict is not None:
        history = None
        if args.history:
            history = [float(x.strip()) for x in args.history.split(",")]
        predict(args.predict, history)
    else:
        parser.print_help()
