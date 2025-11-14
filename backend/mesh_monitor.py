"""
mesh_monitor.py

Runs on each Raspberry Pi node:

- Reads BATMAN-Adv originators table to see neighbors.
- Extracts simple metrics (TQ → signal strength, packet loss estimate, hop count).
- Logs metrics to CSV for training.
- If a trained model is present, predicts link failure probability and (optionally)
  can act on high-risk links.
"""

import csv
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

from config import (
    BAT_ORIGINATORS_PATH,
    LOG_DIR,
    MODEL_PATH,
    PREDICTION_THRESHOLD,
    POLL_INTERVAL_SEC,
    PREDICT_INTERVAL_SEC,
)

MODEL = None
LAST_PREDICT_TIME = 0.0


def load_model():
    """Load trained RandomForest model if available."""
    global MODEL
    if not MODEL_PATH.exists():
        print(f"[WARN] Model not found at {MODEL_PATH}. Running without predictions.")
        MODEL = None
        return
    import pickle

    with open(MODEL_PATH, "rb") as f:
        MODEL = pickle.load(f)
    print(f"[INFO] Loaded model from {MODEL_PATH}")


def parse_batman_originators() -> List[Dict[str, Any]]:
    """
    Parse /sys/kernel/debug/batman_adv/bat0/originators output.

    Returns list of dicts:
      {
        "neighbor": "<MAC>",
        "last_seen_ms": int,
        "tq": int,
        "hop_count": int,
      }

    NOTE: BATMAN output can differ slightly by version; adjust parsing if needed.
    """
    if not os.path.exists(BAT_ORIGINATORS_PATH):
        raise FileNotFoundError(f"{BAT_ORIGINATORS_PATH} does not exist")

    with open(BAT_ORIGINATORS_PATH, "r") as f:
        lines = f.readlines()

    neighbors: List[Dict[str, Any]] = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("Originator"):
            continue

        parts = line.split()
        try:
            neighbor_mac = parts[0]
            # Find TQ:xxx
            tq_token = next(p for p in parts if p.startswith("TQ:"))
            tq_val = int(tq_token.split(":")[1])
            # Last seen "(600"
            last_seen_token = [p for p in parts if p.startswith("(")][0]
            last_seen_ms = int(last_seen_token.strip("("))
            # For now assume one hop; refine if you parse full routing table
            hop_count = 1
        except Exception:
            # If parsing fails for a line, skip it
            continue

        neighbors.append(
            {
                "neighbor": neighbor_mac,
                "last_seen_ms": last_seen_ms,
                "tq": tq_val,
                "hop_count": hop_count,
            }
        )

    return neighbors


def estimate_packet_loss(tq: int) -> float:
    """
    Rough heuristic mapping TQ in [0, 255] to packet loss in [0, 0.5].
    Higher TQ => lower estimated packet loss.
    """
    tq_clamped = max(0, min(255, tq))
    loss = 0.5 * (1 - tq_clamped / 255.0)
    return loss


def estimate_signal_strength(tq: int) -> float:
    """Map TQ to a 'signal_strength' feature in [0, 1]."""
    tq_clamped = max(0, min(255, tq))
    return tq_clamped / 255.0


def get_battery_pct() -> float:
    """
    Mock battery percentage.

    If environment variable CRISIS_BATTERY_PCT is set, use that.
    Otherwise default to 80%.
    """
    env_val = os.environ.get("CRISIS_BATTERY_PCT")
    if env_val:
        try:
            return float(env_val)
        except ValueError:
            pass
    return 80.0


def log_metrics(neighbors: List[Dict[str, Any]]):
    """Log link metrics to CSV (one row per neighbor)."""
    LOG_DIR.mkdir(exist_ok=True, parents=True)
    ts = datetime.utcnow().isoformat()
    log_path = LOG_DIR / f"metrics_{datetime.utcnow().date()}.csv"
    file_exists = log_path.exists()

    with open(log_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                [
                    "timestamp",
                    "neighbor",
                    "signal_strength",
                    "packet_loss",
                    "hop_count",
                    "battery_pct",
                    "will_fail",  # label for training; default 0
                ]
            )

        for n in neighbors:
            signal_strength = estimate_signal_strength(n["tq"])
            packet_loss = estimate_packet_loss(n["tq"])
            hop_count = n["hop_count"]
            battery_pct = get_battery_pct()
            will_fail = 0  # you will relabel some rows later for training

            writer.writerow(
                [
                    ts,
                    n["neighbor"],
                    signal_strength,
                    packet_loss,
                    hop_count,
                    battery_pct,
                    will_fail,
                ]
            )


def maybe_predict_and_act(neighbors: List[Dict[str, Any]]):
    """Call model to predict failure probabilities and optionally act."""
    global LAST_PREDICT_TIME, MODEL
    if MODEL is None:
        return

    now = time.time()
    if now - LAST_PREDICT_TIME < PREDICT_INTERVAL_SEC:
        return
    LAST_PREDICT_TIME = now

    for n in neighbors:
        signal_strength = estimate_signal_strength(n["tq"])
        packet_loss = estimate_packet_loss(n["tq"])
        hop_count = n["hop_count"]
        battery_pct = get_battery_pct()

        X = np.array([[signal_strength, packet_loss, hop_count, battery_pct]])
        prob = float(MODEL.predict_proba(X)[0, 1])

        print(
            f"[PREDICT] neighbor={n['neighbor']} "
            f"tq={n['tq']} hop={hop_count} failure_prob={prob:.3f}"
        )

        if prob >= PREDICTION_THRESHOLD:
            # For now just log; once you're confident you can uncomment
            # the batctl call to deprioritize this neighbor.
            print(
                f"[ACTION] High failure probability for {n['neighbor']} "
                f"(prob={prob:.2f}). Consider dropping route."
            )
            # Example action (verify before enabling!):
            # subprocess.run(["sudo", "batctl", "td", n["neighbor"]])


def main():
    print("[INFO] Starting mesh monitor...")
    load_model()

    while True:
        try:
            neighbors = parse_batman_originators()
            print(f"[INFO] Found {len(neighbors)} neighbors")
            log_metrics(neighbors)
            maybe_predict_and_act(neighbors)
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
